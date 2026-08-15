from __future__ import annotations

import argparse
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import re


MARKER = "SSSF_CDE_RESULT "
DIMENSIONS = ("roster", "cost", "credit")
DIAGNOSTIC_FAILURE = re.compile(r"(?m)^\s*(?:FAIL|CNO)\b")


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CNO = "CNO"


@dataclass(frozen=True)
class Acceptance:
    verdict: Verdict
    reason: str
    states: dict[str, str] | None = None


def classify(remote_exit: int, output: str) -> Acceptance:
    """Reconcile remote C/D/E evidence without trusting transport status alone."""
    markers = [
        line[len(MARKER):]
        for line in output.splitlines()
        if line.startswith(MARKER)
    ]
    if len(markers) != 1:
        return Acceptance(
            Verdict.CNO,
            f"expected exactly one result marker, observed {len(markers)}",
        )

    try:
        payload = json.loads(markers[0])
    except (TypeError, ValueError):
        return Acceptance(Verdict.CNO, "result marker is not valid JSON")

    if not isinstance(payload, dict) or set(payload) != set(DIMENSIONS):
        return Acceptance(
            Verdict.CNO,
            "result marker does not contain exactly roster/cost/credit",
        )

    states = {name: payload[name] for name in DIMENSIONS}
    if any(state not in {item.value for item in Verdict} for state in states.values()):
        return Acceptance(Verdict.CNO, "result marker contains an unknown state")

    if Verdict.FAIL.value in states.values():
        return Acceptance(Verdict.FAIL, "at least one remote dimension failed", states)

    if Verdict.CNO.value in states.values():
        return Acceptance(
            Verdict.CNO,
            "at least one remote dimension could not be observed",
            states,
        )

    if remote_exit != 0:
        return Acceptance(
            Verdict.CNO,
            f"all-PASS marker contradicted remote exit {remote_exit}",
            states,
        )

    evidence_without_marker = "\n".join(
        line for line in output.splitlines() if not line.startswith(MARKER)
    )
    if DIAGNOSTIC_FAILURE.search(evidence_without_marker):
        return Acceptance(
            Verdict.FAIL,
            "all-PASS marker contradicted failure diagnostics",
            states,
        )

    return Acceptance(Verdict.PASS, "all dimensions passed", states)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reconcile sandbox SETUP C/D/E evidence."
    )
    parser.add_argument("--remote-exit", type=int, required=True)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    if not args.output.is_file():
        print("setup C/D/E acceptance: CNO/HOLD")
        print(f"reason: evidence file unavailable: {args.output}")
        return 3

    acceptance = classify(
        args.remote_exit,
        args.output.read_text(encoding="utf-8", errors="replace"),
    )
    label = "CNO/HOLD" if acceptance.verdict is Verdict.CNO else acceptance.verdict.value
    print(f"setup C/D/E acceptance: {label}")
    print(f"reason: {acceptance.reason}")
    if acceptance.states is not None:
        print(
            "states: "
            + " ".join(f"{name}={acceptance.states[name]}" for name in DIMENSIONS)
        )

    if acceptance.verdict is Verdict.PASS:
        return 0
    if acceptance.verdict is Verdict.FAIL:
        return 1
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
