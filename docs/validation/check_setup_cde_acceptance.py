from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.setup_cde_acceptance import Verdict, classify  # noqa: E402


def marker(roster: str, cost: str, credit: str) -> str:
    return (
        'SSSF_CDE_RESULT {'
        f'"roster":"{roster}",'
        f'"cost":"{cost}",'
        f'"credit":"{credit}"'
        '}\n'
    )


def require(expected: Verdict, remote_exit: int, output: str, name: str) -> None:
    actual = classify(remote_exit, output)
    if actual.verdict is not expected:
        raise AssertionError(
            f"{name}: expected {expected.value}, got "
            f"{actual.verdict.value}: {actual.reason}"
        )


require(Verdict.PASS, 0, marker("PASS", "PASS", "PASS"), "clean pass")
require(
    Verdict.FAIL,
    0,
    "   FAIL model: insufficient credits\n" + marker("PASS", "PASS", "PASS"),
    "contradictory diagnostics",
)
require(
    Verdict.CNO,
    0,
    "   FAIL model: insufficient credits\n",
    "legacy missing marker",
)
require(Verdict.CNO, 21, marker("CNO", "CNO", "PASS"), "credit unavailable")
require(Verdict.FAIL, 20, marker("FAIL", "PASS", "PASS"), "model failure")
require(Verdict.CNO, 7, marker("PASS", "PASS", "PASS"), "transport contradiction")
require(Verdict.CNO, 0, "", "empty evidence")
require(Verdict.CNO, 0, "SSSF_CDE_RESULT not-json\n", "malformed marker")
require(
    Verdict.CNO,
    0,
    marker("PASS", "PASS", "PASS") + marker("PASS", "PASS", "PASS"),
    "duplicate marker",
)

setup = (ROOT / "just/sandbox/lifecycle/setup.just").read_text(encoding="utf-8")
for required in (
    "SSSF_CDE_RESULT",
    "CDE_REMOTE_RC=$?",
    'python tools/setup_cde_acceptance.py --remote-exit "$CDE_REMOTE_RC"',
    'gate_fail "assertions C/D/E — CNO/HOLD;',
):
    if required not in setup:
        raise AssertionError(f"setup.just missing acceptance integration: {required}")

windows_host = (ROOT / "tools/windows_host.py").read_text(encoding="utf-8")
if "check_setup_cde_acceptance.py" not in windows_host:
    raise AssertionError("Windows host doctor does not run the B3-005 validator")

with tempfile.TemporaryDirectory(prefix="sssf-b3-005-cde-") as tmp:
    evidence = Path(tmp) / "cde.txt"
    evidence.write_text(marker("CNO", "CNO", "PASS"), encoding="utf-8")
    result = subprocess.run(
        (
            sys.executable,
            str(ROOT / "tools/setup_cde_acceptance.py"),
            "--remote-exit",
            "21",
            str(evidence),
        ),
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if result.returncode != 3 or "CNO/HOLD" not in result.stdout:
        raise AssertionError(
            "CLI did not preserve CNO/HOLD: "
            f"exit={result.returncode} stdout={result.stdout!r} "
            f"stderr={result.stderr!r}"
        )

print("B3-005 setup C/D/E acceptance: PASS")
print("contradictory failure diagnostics cannot produce PASS")
print("missing, malformed, and unavailable evidence classify CNO/HOLD")
