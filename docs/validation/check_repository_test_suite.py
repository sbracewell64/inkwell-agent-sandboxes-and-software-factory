#!/usr/bin/env python3
"""Run the repository test suite as a registered, three-valued gate row.

`ci/checks.json` drove ten validators and never ran `tests/`, so the suite was
outside the gate entirely: a branch could carry failing tests and still show a
green CI, which is exactly what happened to the SDLC-L2 candidate — the pushed
head reported `checks-passed` while three of its own controls failed.

The suite needs dependencies the offline gate deliberately does not ship
(`pydantic`, `pyyaml`, `python-dotenv`, `rich`, `pytest`), so this check cannot
simply run `pytest` and read the exit code: on a host without them, an
unrunnable suite would be reported as a semantic FAIL — an observation failure
narrowed into a judgement, the precise defect HD-09 closed.

So it is three-valued, in the shape `tools/ci_gate.py` owns:

  * every dependency present and the suite green -> exit 0, observed-good;
  * the suite executed and something failed  -> exit 1, observed-bad;
  * no interpreter carrying the dependencies, pytest absent, or a run that
    collected nothing -> `COULD_NOT_OBSERVE_EXIT`, could-not-observe.

Collecting zero tests is could-not-observe rather than success, so deleting or
un-collecting the suite can never be the thing that makes this row green.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci_gate import COULD_NOT_OBSERVE_EXIT  # noqa: E402

REQUIRED = ("pydantic", "yaml", "dotenv", "rich", "pytest")
SUITE = "tests"
# The suite imports the ADW modules by package name, the same way the increment
# records run it: PYTHONPATH=.:adws.
PYTHONPATH = os.pathsep.join([str(ROOT), str(ROOT / "adws")])
# Inside the manifest ceiling (`ci/checks.json` caps a row at 300s), so the
# suite times out as a named could-not-observe here rather than being killed
# by the gate runner with no reason recorded.
TIMEOUT_SECONDS = int(os.environ.get("SSSF_CHILD_TIMEOUT_SECONDS", "240"))
COUNTS = re.compile(r"(\d+) (passed|failed|error|errors|skipped)")


def _candidates() -> list[Path]:
    """Interpreters worth asking, most repository-specific first."""
    found = [ROOT / ".venv" / "bin" / "python", ROOT / ".venv" / "bin" / "python3",
             ROOT / ".venv" / "Scripts" / "python.exe", Path(sys.executable)]
    return [path for path in found if path.exists()]


def _missing(interpreter: Path) -> list[str] | None:
    """Which required modules this interpreter lacks, or None if it cannot say."""
    probe = ("import importlib.util,sys;"
             "print(','.join(m for m in sys.argv[1:] "
             "if importlib.util.find_spec(m) is None))")
    try:
        result = subprocess.run([str(interpreter), "-c", probe, *REQUIRED],
                                capture_output=True, text=True,
                                timeout=TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return [name for name in result.stdout.strip().split(",") if name]


def _could_not_observe(reasons: list[str]) -> int:
    print("repository test suite: COULD-NOT-OBSERVE")
    for reason in reasons:
        print(f"- could-not-observe: {reason}")
    return COULD_NOT_OBSERVE_EXIT


def main() -> int:
    if not (ROOT / SUITE).is_dir():
        return _could_not_observe([f"no {SUITE}/ directory to run"])

    interpreters = _candidates()
    if not interpreters:
        return _could_not_observe(["no python interpreter available to run the suite"])

    chosen, unmet = None, []
    for interpreter in interpreters:
        missing = _missing(interpreter)
        if missing is None:
            unmet.append(f"{interpreter}: could not be asked for its modules")
            continue
        if missing:
            unmet.append(f"{interpreter}: missing {', '.join(missing)}")
            continue
        chosen = interpreter
        break

    if chosen is None:
        return _could_not_observe(
            ["no interpreter carries the suite's declared dependencies "
             f"({', '.join(REQUIRED)})", *unmet])

    environment = dict(os.environ, PYTHONPATH=PYTHONPATH)
    try:
        result = subprocess.run(
            [str(chosen), "-m", "pytest", "-q", SUITE],
            cwd=ROOT, capture_output=True, text=True,
            timeout=TIMEOUT_SECONDS, env=environment)
    except subprocess.TimeoutExpired:
        return _could_not_observe(
            [f"the suite did not finish within {TIMEOUT_SECONDS}s"])
    except OSError as error:
        return _could_not_observe([f"could not launch the suite: {error}"])

    output = f"{result.stdout}\n{result.stderr}".strip()
    tail = "\n".join(output.splitlines()[-25:])
    counts = {kind: int(number) for number, kind in COUNTS.findall(output)}
    executed = sum(counts.get(kind, 0)
                   for kind in ("passed", "failed", "error", "errors"))

    # An empty result set is could-not-observe, never a pass: a suite that
    # collected nothing has judged nothing, however cleanly pytest exited.
    if executed == 0:
        return _could_not_observe(
            ["the suite collected no executable tests", tail])

    if result.returncode != 0:
        print(f"repository test suite: FAIL ({chosen})")
        print(tail)
        return 1

    print(f"repository test suite: PASS ({chosen})")
    print(f"- executed: {executed} test(s)"
          + (f", {counts['skipped']} skipped" if counts.get("skipped") else ""))
    print("- a skipped case is could-not-observe for its own claim and is "
          "never counted as a pass for it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
