"""Validate deterministic CI and watch each non-vacuity failure control go red."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import ci_gate  # noqa: E402

WORKFLOW = Path(".github/workflows/ci.yml")
MANIFEST = Path("ci/checks.json")
EXPECTED_ACTIONS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "oven-sh/setup-bun": "735343b667d3e6f658f44d0eca948eb6282f2b76",
    "extractions/setup-just": "dd310ad5a97d8e7b41793f8ef055398d51ad4de6",
}
# The pinned fragment below is a contiguous substring, so it cannot see a trigger
# APPENDED after the `push` block. The allowed trigger set is therefore also
# pinned structurally: the workflow's `on:` block must be exactly this text, and
# its event keys exactly these, so an added `workflow_dispatch:`, `schedule:`,
# `pull_request_target:` or extra base branch is refused rather than ignored.
EXPECTED_ON_BLOCK = (
    "on:\n"
    "  pull_request:\n"
    "    branches: [main, planning/future-sssf]\n"
    "  push:\n"
    "    branches: [main]\n"
)
EXPECTED_EVENTS = ("pull_request", "push")

EXPECTED_CHECKS = {
    "ci-contract-and-watched-red-controls": (
        "{python}", "docs/validation/check_ci_contract.py"
    ),
    "agent-bootstrap-validator": (
        "{python}", "docs/validation/check_agent_bootstrap.py"
    ),
    "line-ending-validator": (
        "{python}", "docs/validation/check_line_endings.py", "--require-worktree-lf"
    ),
    "sqlite-free-observability-validator": (
        "{python}", "docs/validation/check_obs_query.py"
    ),
    "sandbox-source-contract-validator": (
        "{python}", "docs/validation/check_sandbox_source_contract.py"
    ),
    "executor-supervisor-and-pi-adapter-validator": (
        "{python}", "docs/validation/check_executor_supervisor.py"
    ),
    "production-extension-path-validator": (
        "{python}", "docs/validation/check_production_extension_path.py"
    ),
    "planning-dependency-graph-validator": (
        "{python}", "docs/validation/check_planning_dependency_graph.py"
    ),
    "inkwell-unit-tests": ("just", "inkwell", "test"),
}


def workflow_on_block(text: str) -> str | None:
    """The workflow's whole `on:` block, or None if it is absent or duplicated.

    Top-level keys are separated by a blank line in this workflow, so the block
    runs from `on:` to the first blank line or the first non-indented line —
    whichever comes first. Anything appended inside it is therefore visible.
    """
    lines = text.splitlines(keepends=True)
    start = None
    for index, raw in enumerate(lines):
        if raw.rstrip("\n") == "on:":
            if start is not None:
                return None
            start = index
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        body = lines[index].rstrip("\n")
        if not body or not body.startswith((" ", "\t")):
            end = index
            break
    return "".join(lines[start:end])


def contract_errors(root: Path) -> list[str]:
    errors: list[str] = []
    workflow_path = root / WORKFLOW
    workflow_files = sorted((root / ".github" / "workflows").glob("*.y*ml"))

    if workflow_files != [workflow_path]:
        errors.append("workflow path drift: expected only .github/workflows/ci.yml")
    if not workflow_path.is_file():
        return errors or ["workflow path drift: ci.yml is missing"]

    text = workflow_path.read_text(encoding="utf-8")
    required_fragments = (
        # A durable authoritative landing target must not be excluded from the
        # required verification trigger. `planning/future-sssf` is the canonical
        # planning base, so it is named exactly; a glob is not used, and `push`
        # stays restricted to `main`.
        "on:\n  pull_request:\n    branches: [main, planning/future-sssf]\n  push:\n    branches: [main]",
        "permissions:\n  contents: read",
        "concurrency:\n  group: deterministic-ci-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: true",
        "timeout-minutes: 10",
        "fail-fast: false",
        "os: [ubuntu-24.04, windows-2022]",
        "ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}",
        "persist-credentials: false",
        "python-version: '3.12.8'",
        "check-latest: false",
        "token: ''",
        "bun-version: '1.3.14'",
        "no-cache: true",
        "just-version: '1.58.0'",
        "github-token: ''",
        "python tools/ci_gate.py run --evidence ci-evidence-${{ runner.os }}.json",
    )
    for fragment in required_fragments:
        if fragment not in text:
            errors.append(f"workflow contract missing: {fragment.splitlines()[0]}")

    for forbidden in ("pull_request_target:", "paths:", "paths-ignore:", "secrets."):
        if forbidden in text:
            errors.append(f"workflow contains forbidden trigger/credential surface: {forbidden}")

    on_block = workflow_on_block(text)
    if on_block is None:
        errors.append("workflow trigger block is missing or declared more than once")
    else:
        events = re.findall(r"^  ([A-Za-z_][A-Za-z0-9_-]*):", on_block, flags=re.MULTILINE)
        if tuple(events) != EXPECTED_EVENTS:
            errors.append(
                f"workflow trigger events are {events!r}; exactly {list(EXPECTED_EVENTS)} "
                "are allowed"
            )
        if on_block != EXPECTED_ON_BLOCK:
            errors.append("workflow trigger block differs from the exact allowed trigger set")

    observed_actions = dict(
        re.findall(r"uses:\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40})", text)
    )
    if observed_actions != EXPECTED_ACTIONS:
        errors.append(f"action pins differ: {observed_actions!r}")
    if len(re.findall(r"^\s*uses:", text, flags=re.MULTILINE)) != len(EXPECTED_ACTIONS):
        errors.append("an action is unpinned or an unexpected action was added")

    manifest_path = root / MANIFEST
    try:
        checks = ci_gate.load_checks(manifest_path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    observed_checks = {
        check["id"]: tuple(check["command"])
        for check in checks
    }
    if observed_checks != EXPECTED_CHECKS:
        errors.append(f"enumerated offline checks differ: {observed_checks!r}")
    return errors


def fixture_manifest(path: Path, command: list[str], timeout: int = 5) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "checks": [
                    {"id": "control", "command": command, "timeout_seconds": timeout}
                ],
            }
        ),
        encoding="utf-8",
    )


def read_evidence(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def watched_red_errors() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sssf-ci-controls-") as raw_temp:
        temp = Path(raw_temp)

        empty_manifest = temp / "empty.json"
        empty_evidence = temp / "empty-evidence.json"
        empty_manifest.write_text('{"schema_version": 1, "checks": []}', encoding="utf-8")
        if ci_gate.execute(empty_manifest, empty_evidence) == 0:
            errors.append("empty check discovery did not go red")
        empty = read_evidence(empty_evidence)
        if (empty["conclusion"], empty["discovered_checks"]) != ("could-not-observe", 0):
            errors.append("empty check discovery lost CNO evidence")

        failing_manifest = temp / "failing.json"
        failing_evidence = temp / "failing-evidence.json"
        fixture_manifest(failing_manifest, ["{python}", "-c", "raise SystemExit(7)"])
        if ci_gate.execute(failing_manifest, failing_evidence) == 0:
            errors.append("deliberately failing validator did not go red")
        if read_evidence(failing_evidence)["conclusion"] != "observed-bad":
            errors.append("failing validator was not preserved as observed-bad")

        missing_manifest = temp / "missing.json"
        missing_evidence = temp / "missing-evidence.json"
        fixture_manifest(missing_manifest, ["sssf-tool-that-does-not-exist-6f65d2"])
        if ci_gate.execute(missing_manifest, missing_evidence) == 0:
            errors.append("missing tool did not go red")
        if read_evidence(missing_evidence)["conclusion"] != "could-not-observe":
            errors.append("missing tool was narrowed away from CNO")

        timeout_manifest = temp / "timeout.json"
        timeout_evidence = temp / "timeout-evidence.json"
        fixture_manifest(
            timeout_manifest,
            ["{python}", "-c", "import time; time.sleep(2)"],
            timeout=1,
        )
        if ci_gate.execute(timeout_manifest, timeout_evidence) == 0:
            errors.append("timeout did not go red")
        if read_evidence(timeout_evidence)["conclusion"] != "could-not-observe":
            errors.append("timeout was narrowed away from CNO")

        cancel_manifest = temp / "cancel.json"
        cancel_evidence = temp / "cancel-evidence.json"
        fixture_manifest(cancel_manifest, ["{python}", "-c", "import time; time.sleep(2)"])
        ci_gate._CANCEL_REQUESTED = True
        try:
            if ci_gate.execute(cancel_manifest, cancel_evidence) == 0:
                errors.append("cancellation did not go red")
        finally:
            ci_gate._CANCEL_REQUESTED = False
        cancelled = read_evidence(cancel_evidence)
        if cancelled["conclusion"] != "could-not-observe":
            errors.append("cancellation was narrowed away from CNO")

        contract_root = temp / "contract"
        (contract_root / ".github" / "workflows").mkdir(parents=True)
        (contract_root / "ci").mkdir()
        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        shutil.copy2(ROOT / MANIFEST, contract_root / MANIFEST)

        workflow_text = (contract_root / WORKFLOW).read_text(encoding="utf-8")
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace("pull_request:", "pull_request_target:", 1),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("trigger drift did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "os: [ubuntu-24.04, windows-2022]", "os: []", 1
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("empty OS matrix did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "          ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}\n",
                "",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("missing exact-head checkout did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "github.event.pull_request.head.sha || github.sha",
                "github.sha || github.sha",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("substituted exact-head checkout did not go red")

        # A trigger APPENDED after the pinned `push` block is invisible to a
        # contiguous-substring pin, so the exact trigger set is controlled too.
        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "  push:\n    branches: [main]\n",
                "  push:\n    branches: [main]\n  workflow_dispatch:\n",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("appended workflow trigger did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "    branches: [main, planning/future-sssf]\n",
                "    branches: [main, planning/future-sssf, planning/anything-else]\n",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("extra pull_request base branch did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "  push:\n    branches: [main]\n",
                "  push:\n    branches: [main]\n  schedule:\n    - cron: '0 0 * * *'\n",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("appended schedule trigger did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        if contract_errors(contract_root):
            errors.append("the unmodified workflow did not stay green after the trigger controls")

        (contract_root / WORKFLOW).unlink()
        shutil.copy2(ROOT / WORKFLOW, contract_root / ".github" / "workflows" / "drift.yml")
        if not contract_errors(contract_root):
            errors.append("workflow path drift did not go red")

    return errors


def main() -> int:
    errors = contract_errors(ROOT)
    if not errors:
        errors.extend(watched_red_errors())

    if errors:
        print("B4-001 deterministic CI contract: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("B4-001 deterministic CI contract: PASS")
    print(f"{len(EXPECTED_CHECKS)} offline checks enumerated; Linux and Windows matrix is nonempty")
    print("watched-red: empty discovery/matrix, validator failure, missing tool")
    print("watched-red: cancellation/timeout and workflow path/trigger drift")
    print(
        f"trigger set pinned to {list(EXPECTED_EVENTS)}; watched-red: appended "
        "workflow_dispatch, appended schedule, extra pull_request base branch"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
