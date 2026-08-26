"""Executable proof that a validator's observation failure is never a FAIL.

Every case drives the real executables: the validator scripts under
`docs/validation/` and `tools/ci_gate.py`. A validator that cannot spawn a
required child tool, or whose child stops answering, must report
could-not-observe with the tool named. A validator whose child *does* answer
and contradicts the predicate must still report observed-bad, so the boundary
cannot mask a genuine failure.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
VALIDATIONS = ROOT / "docs" / "validation"
OBS_VALIDATOR = VALIDATIONS / "check_obs_query.py"
LINE_ENDING_VALIDATOR = VALIDATIONS / "check_line_endings.py"
SOURCE_CONTRACT_VALIDATOR = VALIDATIONS / "check_sandbox_source_contract.py"
CI_GATE = ROOT / "tools" / "ci_gate.py"

# The reserved exit code tools/ci_gate.py reads as observation failure. Spelled
# out here on purpose: the test asserts the contract, it does not import it.
COULD_NOT_OBSERVE_EXIT = 125
POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="the child-tool stubs are POSIX executables",
)


def path_env(directory: Path, **extra: str) -> dict[str, str]:
    """An environment whose PATH is exactly one directory."""
    env = dict(os.environ)
    env["PATH"] = str(directory)
    env.update(extra)
    return env


def empty_path_dir(tmp_path: Path) -> Path:
    """A newly created, empty directory. Nothing is ever removed from PATH."""
    empty = tmp_path / "empty-path"
    empty.mkdir()
    return empty


def install_stub(directory: Path, name: str, body: str) -> Path:
    """A child tool that exists and is spawnable, but answers as instructed."""
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / name
    stub.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return stub


def run_validator(
    validator: Path,
    *args: str,
    env: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(validator), *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=180,
    )


def gate_row(
    tmp_path: Path,
    check_id: str,
    command: list[str],
    env: dict[str, str],
    timeout_seconds: int = 120,
) -> tuple[int, dict, dict]:
    """Run one check through the real gate runner and return its evidence row."""
    manifest = tmp_path / f"{check_id}-manifest.json"
    evidence = tmp_path / f"{check_id}-evidence.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "checks": [
                    {
                        "id": check_id,
                        "command": command,
                        "timeout_seconds": timeout_seconds,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    process = subprocess.run(
        [
            sys.executable,
            str(CI_GATE),
            "run",
            "--manifest",
            str(manifest),
            "--evidence",
            str(evidence),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=240,
    )
    document = json.loads(evidence.read_text(encoding="utf-8"))
    return process.returncode, document, document["results"][0]


# --- observation failure is could-not-observe, never a manufactured FAIL -----


def test_missing_just_makes_the_observability_validator_could_not_observe(
    tmp_path: Path,
) -> None:
    result = run_validator(OBS_VALIDATOR, env=path_env(empty_path_dir(tmp_path)))

    assert result.returncode == COULD_NOT_OBSERVE_EXIT, result.stdout
    assert "could-not-observe:" in result.stdout
    assert "just" in result.stdout
    assert "observability: PASS" not in result.stdout
    assert "observability: FAIL" not in result.stdout
    assert "Traceback" not in result.stdout


def test_missing_just_gate_row_is_could_not_observe_naming_the_tool(
    tmp_path: Path,
) -> None:
    code, document, row = gate_row(
        tmp_path,
        "sqlite-free-observability-validator",
        ["{python}", "docs/validation/check_obs_query.py"],
        path_env(empty_path_dir(tmp_path)),
    )

    assert row["status"] == "could-not-observe", row
    assert "just" in row["reason"]
    assert document["conclusion"] == "could-not-observe"
    # could-not-observe is a real result, and it is not a pass.
    assert code != 0


@POSIX_ONLY
def test_hanging_just_is_a_timed_out_observation_not_a_fail(tmp_path: Path) -> None:
    stubs = tmp_path / "hanging"
    install_stub(stubs, "just", "import time\ntime.sleep(600)\n")
    install_stub(stubs, "python", "raise SystemExit(0)\n")

    result = run_validator(
        OBS_VALIDATOR,
        env=path_env(stubs, SSSF_CHILD_TIMEOUT_SECONDS="1"),
    )

    assert result.returncode == COULD_NOT_OBSERVE_EXIT, result.stdout
    assert "check timed out" in result.stdout
    assert "observability: FAIL" not in result.stdout


def test_missing_git_makes_the_source_contract_validator_could_not_observe(
    tmp_path: Path,
) -> None:
    result = run_validator(
        SOURCE_CONTRACT_VALIDATOR,
        env=path_env(empty_path_dir(tmp_path)),
    )

    assert result.returncode == COULD_NOT_OBSERVE_EXIT, result.stdout
    assert "could-not-observe:" in result.stdout
    assert "git" in result.stdout
    assert "contract: FAIL" not in result.stdout
    assert "Traceback" not in result.stdout


def test_missing_git_makes_the_line_ending_validator_could_not_observe(
    tmp_path: Path,
) -> None:
    result = run_validator(
        LINE_ENDING_VALIDATOR,
        "--require-worktree-lf",
        env=path_env(empty_path_dir(tmp_path)),
    )

    assert result.returncode == COULD_NOT_OBSERVE_EXIT, result.stdout
    assert "could-not-observe:" in result.stdout
    assert "contract: CNO" in result.stdout
    assert "contract: FAIL" not in result.stdout


# --- the boundary must not swallow a real predicate failure -----------------


@POSIX_ONLY
def test_answering_just_that_contradicts_the_predicate_is_observed_bad(
    tmp_path: Path,
) -> None:
    stubs = tmp_path / "answering"
    install_stub(stubs, "just", "print('not the expected row')\n")
    install_stub(stubs, "python", "raise SystemExit(0)\n")

    result = run_validator(OBS_VALIDATOR, env=path_env(stubs))

    assert result.returncode == 1, result.stdout
    assert result.returncode != COULD_NOT_OBSERVE_EXIT
    assert "observability: FAIL" in result.stdout
    assert "observed-bad:" in result.stdout
    assert "not the expected row" in result.stdout


@POSIX_ONLY
def test_real_predicate_failure_gate_row_stays_observed_bad(tmp_path: Path) -> None:
    stubs = tmp_path / "answering-gate"
    install_stub(stubs, "just", "print('not the expected row')\n")
    install_stub(stubs, "python", "raise SystemExit(0)\n")

    _, document, row = gate_row(
        tmp_path,
        "sqlite-free-observability-validator",
        ["{python}", "docs/validation/check_obs_query.py"],
        path_env(stubs),
    )

    assert row["status"] == "observed-bad", row
    assert document["conclusion"] == "observed-bad"


# --- non-vacuity: the real integration predicate is still executed ----------


def test_present_just_executes_the_real_integration_predicate(tmp_path: Path) -> None:
    missing = [tool for tool in ("just", "python") if shutil.which(tool) is None]
    if missing:
        # Not a pass: the predicate simply could not be observed here.
        pytest.skip(
            f"{', '.join(missing)} unavailable on this host: the real "
            "`just obs` integration predicate could not be observed"
        )

    env = dict(os.environ)
    env.pop("SSSF_CHILD_TIMEOUT_SECONDS", None)
    result = run_validator(OBS_VALIDATOR, env=env)

    assert result.returncode == 0, result.stdout
    assert "B3-004 sqlite-free observability: PASS" in result.stdout
    assert "could-not-observe" not in result.stdout


# --- the gate runner's exit-code channel, with its negative controls --------


@pytest.mark.parametrize(
    ("exit_code", "expected_status"),
    [
        (0, "observed-good"),
        (1, "observed-bad"),
        (7, "observed-bad"),
        (COULD_NOT_OBSERVE_EXIT, "could-not-observe"),
    ],
)
def test_gate_maps_only_the_reserved_exit_code_to_could_not_observe(
    tmp_path: Path, exit_code: int, expected_status: str
) -> None:
    code, _, row = gate_row(
        tmp_path,
        f"exit-{exit_code}",
        [
            "{python}",
            "-c",
            "print('- could-not-observe: tool unavailable: fixture-child-tool'); "
            f"raise SystemExit({exit_code})",
        ],
        dict(os.environ),
        timeout_seconds=30,
    )

    assert row["status"] == expected_status, row
    if expected_status == "could-not-observe":
        assert row["reason"] == "tool unavailable: fixture-child-tool"
        assert code != 0
    else:
        # A validator that judged the predicate keeps its judgement, whatever
        # it happened to print.
        assert "reason" not in row
