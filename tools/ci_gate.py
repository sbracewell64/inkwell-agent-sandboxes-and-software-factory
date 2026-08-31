"""Run the repository's offline checks with non-vacuous, three-valued evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from typing import Any

from adws.adw_modules.subprocess_supervisor import (
    process_group_popen_kwargs,
    stop_process_group,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ci" / "checks.json"
DEFAULT_EVIDENCE = ROOT / "ci-evidence.json"
STATUSES = ("observed-good", "observed-bad", "could-not-observe")
# A validator that could not execute its predicate — a required child tool was
# absent or unspawnable, timed out, or the host lacks a primitive it needs —
# reports observation failure through this reserved exit code. Failure to
# observe is not a predicate failure, so such a check is could-not-observe and
# never observed-bad; it is not a pass either, and the gate still exits red.
COULD_NOT_OBSERVE_EXIT = 125
# Validators name each reason on its own line using this prefix, the shape
# docs/validation/check_line_endings.py already prints.
CNO_REASON_PREFIX = "could-not-observe: "
# BOUNDEDNESS-OWNER: sssf.ci_gate.check_timeout_seconds
TIMEOUT_MIN_SECONDS = 1
TIMEOUT_MAX_SECONDS = 300
CHECK_MAX_OUTPUT_BYTES = 8 * 1024 * 1024
_CANCEL_REQUESTED = False


def load_checks(path: Path) -> list[dict[str, Any]]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"manifest could not be observed: {exc}") from exc

    if document.get("schema_version") != 1:
        raise ValueError("manifest schema_version must be 1")

    checks = document.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ValueError("zero checks discovered")

    seen: set[str] = set()
    for check in checks:
        if not isinstance(check, dict):
            raise ValueError("each check must be an object")
        check_id = check.get("id")
        command = check.get("command")
        timeout = check.get("timeout_seconds")
        if not isinstance(check_id, str) or not check_id:
            raise ValueError("each check needs a nonempty id")
        if check_id in seen:
            raise ValueError(f"duplicate check id: {check_id}")
        seen.add(check_id)
        if (
            not isinstance(command, list)
            or not command
            or not all(isinstance(part, str) and part for part in command)
        ):
            raise ValueError(f"{check_id}: command must be a nonempty string list")
        if not isinstance(timeout, int) or not TIMEOUT_MIN_SECONDS <= timeout <= TIMEOUT_MAX_SECONDS:
            raise ValueError(
                f"{check_id}: timeout_seconds must be "
                f"{TIMEOUT_MIN_SECONDS}..{TIMEOUT_MAX_SECONDS}"
            )

    return checks


# BOUNDEDNESS-OWNER: sssf.ci_gate.check_output_capture
# BOUNDEDNESS-POLICY: sssf.policy.bounded-check-output.v1
class BoundedOutput:
    """A finite retained-byte ceiling for one check's combined output.

    `communicate()` holds whatever the child produced. A check that loops
    printing is then bounded only by the gate's own memory, which is not a
    bound. Retention stops at `limit`; `seen` keeps counting, so the evidence
    can always say a log was clipped rather than simply being shorter.
    """

    def __init__(self, limit: int) -> None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("check output limit must be a positive integer")
        self.limit = limit
        self.seen = 0
        self.truncated = False
        self._data = bytearray()

    def feed(self, chunk: bytes) -> None:
        if not chunk:
            return
        self.seen += len(chunk)
        remaining = self.limit - len(self._data)
        if remaining > 0:
            self._data.extend(chunk[:remaining])
        if len(chunk) > remaining:
            self.truncated = True

    def read_from(self, pipe) -> None:
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                self.feed(chunk)
        finally:
            pipe.close()

    def text(self) -> str:
        rendered = self._data.decode("utf-8", "replace")
        if self.truncated:
            rendered += (
                f"\n[bounded] output truncated at {self.limit} bytes "
                f"({self.seen} bytes seen)"
            )
        return rendered


# Retained for the call sites that predate the public name.
_BoundedOutput = BoundedOutput


def _expanded_command(command: list[str]) -> list[str]:
    return [sys.executable if part == "{python}" else part for part in command]


def child_cno_reason(output: str) -> str:
    """Name why a validator could not observe, from its own reason lines."""
    reasons = [
        line.split(CNO_REASON_PREFIX, 1)[1].strip()
        for line in output.splitlines()
        if CNO_REASON_PREFIX in line
    ]
    if not reasons:
        return f"validator could not observe (exit {COULD_NOT_OBSERVE_EXIT})"
    return "; ".join(reasons)


def _stop_process(process: subprocess.Popen[str]) -> bool:
    return stop_process_group(process)


def run_check(check: dict[str, Any]) -> dict[str, Any]:
    command = _expanded_command(check["command"])
    result: dict[str, Any] = {
        "id": check["id"],
        "command": command,
        "status": "could-not-observe",
    }

    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            **process_group_popen_kwargs(),
        )
    except OSError as exc:
        result["reason"] = f"tool unavailable: {exc}"
        return result

    deadline = time.monotonic() + check["timeout_seconds"]
    # A check's own output is unbounded input to this process, so it is held
    # against a ceiling on the way in. Reaching it is stated in the evidence,
    # never a quietly shorter log.
    capture = BoundedOutput(CHECK_MAX_OUTPUT_BYTES)
    reader = threading.Thread(target=capture.read_from, args=(process.stdout,), daemon=True)
    reader.start()

    while True:
        if _CANCEL_REQUESTED:
            cleanup_succeeded = _stop_process(process)
            result["reason"] = (
                "execution cancelled" if cleanup_succeeded
                else "execution cancelled; process-tree cleanup failed"
            )
            break

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            cleanup_succeeded = _stop_process(process)
            result["reason"] = (
                "check timed out" if cleanup_succeeded
                else "check timed out; process-tree cleanup failed"
            )
            break

        try:
            process.wait(timeout=min(0.2, remaining))
            result["returncode"] = process.returncode
            if process.returncode != COULD_NOT_OBSERVE_EXIT:
                result["status"] = (
                    "observed-good" if process.returncode == 0 else "observed-bad"
                )
            break
        except subprocess.TimeoutExpired:
            continue

    reader.join(timeout=max(0.0, deadline - time.monotonic()))
    if reader.is_alive():
        cleanup_succeeded = _stop_process(process)
        reader.join(timeout=2)
        if reader.is_alive() or not cleanup_succeeded:
            result["status"] = "could-not-observe"
            result["reason"] = (
                "check output pipe did not close after process-tree cleanup"
                if reader.is_alive()
                else "check process-tree cleanup failed"
            )
    output = capture.text()
    if result.get("returncode") == COULD_NOT_OBSERVE_EXIT:
        # The child names its own could-not-observe reasons on its stdout, so
        # they can only be read once the reader has drained it. A capture that
        # hit its ceiling may have dropped a reason line; child_cno_reason then
        # falls back to naming the reserved exit code, and output_truncated in
        # this same row says why the named reason is missing.
        result["reason"] = child_cno_reason(output)
    if output:
        result["output"] = output.rstrip()
    result["output_limit_bytes"] = capture.limit
    result["output_bytes_seen"] = capture.seen
    result["output_truncated"] = capture.truncated
    return result


def conclusion(results: list[dict[str, Any]], discovered: int) -> str:
    if discovered == 0 or len(results) != discovered:
        return "could-not-observe"
    statuses = {result["status"] for result in results}
    if "could-not-observe" in statuses:
        return "could-not-observe"
    if "observed-bad" in statuses:
        return "observed-bad"
    return "observed-good"


def write_evidence(path: Path, evidence: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    path.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def execute(manifest: Path, evidence_path: Path) -> int:
    results: list[dict[str, Any]] = []
    manifest_error = ""

    try:
        checks = load_checks(manifest)
    except ValueError as exc:
        checks = []
        manifest_error = str(exc)

    for check in checks:
        print(f"::group::{check['id']}", flush=True)
        result = run_check(check)
        if result.get("output"):
            print(result["output"])
        print(f"status: {result['status']}")
        print("::endgroup::", flush=True)
        results.append(result)
        if _CANCEL_REQUESTED:
            break

    counts = {status: 0 for status in STATUSES}
    for result in results:
        counts[result["status"]] += 1

    overall = conclusion(results, len(checks))
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "conclusion": overall,
        "discovered_checks": len(checks),
        "executed_checks": len(results),
        "status_counts": counts,
        "results": results,
    }
    if manifest_error:
        evidence["manifest_observation"] = manifest_error

    write_evidence(evidence_path, evidence)
    return 0 if overall == "observed-good" and len(results) > 0 else 1


def _request_cancel(_signum: int, _frame: object) -> None:
    global _CANCEL_REQUESTED
    _CANCEL_REQUESTED = True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("run",))
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _request_cancel)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _request_cancel)

    return execute(args.manifest.resolve(), args.evidence.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
