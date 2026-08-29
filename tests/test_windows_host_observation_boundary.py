"""Executable proof that the Windows host doctor never manufactures a verdict.

`tools/windows_host.py` spawns child tools — `just`, `git`, `ssh` and the
repository's own validators — to observe host predicates. A child this doctor
cannot execute leaves its predicate unevaluated. Reporting that as FAIL claims a
judgement no child ever made, and crashing reports nothing at all; both are
narrowings of could-not-observe.

Every case drives the real module. The doctor's own installed-tool predicate is
deliberately unchanged: an absent tool stays a doctor finding. What changes is
everything derived from a child that never ran.
"""

from __future__ import annotations

import os
from contextlib import redirect_stdout
import io
from pathlib import Path
import stat
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.windows_host import (  # noqa: E402
    MIN_JUST,
    Doctor,
    check_child_probe,
    check_ssh_config,
    check_tool,
    check_version_contract,
    run,
    terminal_disposition,
)

# The reserved exit code tools/ci_gate.py reads as observation failure. Spelled
# out here on purpose: the test asserts the contract, it does not import it.
COULD_NOT_OBSERVE_EXIT = 125

POSIX_ONLY = pytest.mark.skipif(
    os.name != "posix",
    reason="the child-tool stubs are POSIX executables",
)

ABSENT_TOOL = "sssf-tool-that-does-not-exist-4c1f9a"


def empty_dir(tmp_path: Path, name: str) -> Path:
    """A newly created, empty directory. Nothing is ever removed from PATH."""
    created = tmp_path / name
    created.mkdir()
    return created


def install_stub(directory: Path, name: str, body: str) -> Path:
    """A child tool that exists and is spawnable, but answers as instructed."""
    directory.mkdir(parents=True, exist_ok=True)
    stub = directory / name
    stub.write_text(f"#!{sys.executable}\n{body}", encoding="utf-8")
    stub.chmod(
        stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    )
    return stub


def only_path(monkeypatch: pytest.MonkeyPatch, directory: Path) -> None:
    monkeypatch.setenv("PATH", str(directory))


def observe(
    call,
    *args,
    **kwargs,
) -> tuple[Doctor, str]:
    """Run one doctor check and capture the row it printed."""
    doctor = Doctor()
    printed = io.StringIO()

    with redirect_stdout(printed):
        call(doctor, *args, **kwargs)

    return doctor, printed.getvalue()


# --- the spawn boundary itself -------------------------------------------


@POSIX_ONLY
def test_watched_red_absent_child_tool_is_could_not_observe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unspawnable child returns a result; it does not raise."""
    workdir = empty_dir(tmp_path, "workdir")
    only_path(monkeypatch, empty_dir(tmp_path, "empty-path"))

    result = run(["just"], cwd=workdir)

    assert result.observed is False
    assert result.returncode is None
    assert "just" in result.reason


@POSIX_ONLY
def test_non_vacuity_present_child_tool_is_really_executed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The positive control: a real child answers and its answer is kept."""
    workdir = empty_dir(tmp_path, "workdir")
    binaries = empty_dir(tmp_path, "bin")
    witness = tmp_path / "witness.txt"
    install_stub(
        binaries,
        "just",
        "from pathlib import Path\n"
        f"Path({str(witness)!r}).write_text('ran', encoding='utf-8')\n"
        "print('default recipe')\n",
    )
    only_path(monkeypatch, binaries)

    result = run(["just"], cwd=workdir)

    assert witness.read_text(encoding="utf-8") == "ran"
    assert result.observed is True
    assert result.returncode == 0
    assert "default recipe" in result.stdout


@POSIX_ONLY
def test_watched_red_wedged_child_is_a_timed_out_observation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A child that stops answering is unobserved, not failed."""
    workdir = empty_dir(tmp_path, "workdir")
    binaries = empty_dir(tmp_path, "bin")
    install_stub(binaries, "just", "import time\ntime.sleep(30)\n")
    only_path(monkeypatch, binaries)

    result = run(["just"], cwd=workdir, timeout=0.75)

    assert result.observed is False
    assert "just" in result.reason


@POSIX_ONLY
def test_watched_red_child_declared_cno_is_not_narrowed_to_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A validator that reported its own observation failure is believed."""
    workdir = empty_dir(tmp_path, "workdir")
    binaries = empty_dir(tmp_path, "bin")
    install_stub(
        binaries,
        "just",
        "print('- could-not-observe: fixture child named its own gap')\n"
        f"raise SystemExit({COULD_NOT_OBSERVE_EXIT})\n",
    )
    only_path(monkeypatch, binaries)

    result = run(["just"], cwd=workdir)

    assert result.observed is False
    assert result.reason == "fixture child named its own gap"


@POSIX_ONLY
def test_watched_red_unreadable_working_directory_is_could_not_observe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An environment this doctor cannot enter is unobserved, not failed."""
    binaries = empty_dir(tmp_path, "bin")
    install_stub(binaries, "just", "print('default recipe')\n")
    only_path(monkeypatch, binaries)

    result = run(["just"], cwd=tmp_path / "no-such-directory")

    assert result.observed is False
    assert result.reason


# --- the front-door probes the sweep names -------------------------------


@POSIX_ONLY
def test_watched_red_absent_front_door_tool_is_cno_not_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    only_path(monkeypatch, empty_dir(tmp_path, "empty-path"))

    doctor, printed = observe(
        check_child_probe,
        "root `just` front door",
        ["just"],
        success_detail="default recipe runs",
        cwd=empty_dir(tmp_path, "workdir"),
    )

    assert doctor.could_not_observe is True
    assert doctor.failed is False
    assert "CNO" in printed
    assert "could-not-observe:" in printed
    assert "just" in printed
    assert "FAIL" not in printed


@POSIX_ONLY
def test_front_door_tool_that_contradicts_the_predicate_is_still_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The boundary cannot mask a genuine failure."""
    binaries = empty_dir(tmp_path, "bin")
    install_stub(
        binaries,
        "just",
        "print('error: recipe is broken')\nraise SystemExit(1)\n",
    )
    only_path(monkeypatch, binaries)

    doctor, printed = observe(
        check_child_probe,
        "root `just` front door",
        ["just"],
        success_detail="default recipe runs",
        cwd=empty_dir(tmp_path, "workdir"),
    )

    assert doctor.failed is True
    assert doctor.could_not_observe is False
    assert "FAIL" in printed
    assert "recipe is broken" in printed


@POSIX_ONLY
def test_non_vacuity_front_door_probe_reports_the_real_predicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """With the tool present the doctor still observes and still passes."""
    binaries = empty_dir(tmp_path, "bin")
    witness = tmp_path / "front-door-witness.txt"
    install_stub(
        binaries,
        "just",
        "from pathlib import Path\n"
        f"Path({str(witness)!r}).write_text('ran', encoding='utf-8')\n"
        "print('default recipe')\n",
    )
    only_path(monkeypatch, binaries)

    doctor, printed = observe(
        check_child_probe,
        "root `just` front door",
        ["just"],
        success_detail="default recipe runs",
        cwd=empty_dir(tmp_path, "workdir"),
    )

    assert witness.read_text(encoding="utf-8") == "ran"
    assert doctor.failed is False
    assert doctor.could_not_observe is False
    assert "ok" in printed
    assert "default recipe runs" in printed


@POSIX_ONLY
def test_watched_red_absent_ssh_makes_the_ssh_config_probe_cno(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    only_path(monkeypatch, empty_dir(tmp_path, "empty-path"))

    doctor, printed = observe(check_ssh_config, "exe.dev")

    assert doctor.could_not_observe is True
    assert doctor.failed is False
    assert "ssh" in printed


# --- the version contracts derived from a tool that never ran ------------


def test_absent_tool_remains_a_doctor_finding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The host-doctor predicate is honest: installed-or-not is judged."""
    only_path(monkeypatch, empty_dir(tmp_path, "empty-path"))

    doctor, printed = observe(check_tool, ABSENT_TOOL, "--version")

    assert doctor.failed is True
    assert "FAIL" in printed
    assert "not found on PATH" in printed


def test_watched_red_absent_tool_version_contract_is_cno_not_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A version that was never read is not a version that failed."""
    only_path(monkeypatch, empty_dir(tmp_path, "empty-path"))

    finder = Doctor()
    with redirect_stdout(io.StringIO()):
        _, version, reason = check_tool(finder, ABSENT_TOOL, "--version")

    assert reason

    doctor, printed = observe(
        check_version_contract,
        "just compatibility",
        version,
        MIN_JUST,
        unobserved_reason=reason,
    )

    assert doctor.could_not_observe is True
    assert doctor.failed is False
    assert "could not parse" not in printed
    assert "could-not-observe:" in printed


def test_unparseable_version_from_a_tool_that_ran_is_still_fail() -> None:
    doctor, printed = observe(
        check_version_contract,
        "just compatibility",
        "not a version at all",
        MIN_JUST,
        unobserved_reason="",
    )

    assert doctor.failed is True
    assert doctor.could_not_observe is False
    assert "could not parse" in printed


def test_version_below_the_minimum_is_still_fail() -> None:
    doctor, printed = observe(
        check_version_contract,
        "just compatibility",
        "just 1.0.0",
        MIN_JUST,
        unobserved_reason="",
    )

    assert doctor.failed is True
    assert "< required" in printed


def test_non_vacuity_version_at_the_minimum_passes() -> None:
    doctor, printed = observe(
        check_version_contract,
        "just compatibility",
        "just " + ".".join(str(part) for part in MIN_JUST),
        MIN_JUST,
        unobserved_reason="",
    )

    assert doctor.failed is False
    assert doctor.could_not_observe is False
    assert "ok" in printed


# --- the doctor's terminal disposition -----------------------------------


def test_could_not_observe_is_a_finding_and_never_a_pass() -> None:
    doctor = Doctor()
    printed = io.StringIO()

    with redirect_stdout(printed):
        doctor.cno("root `just` front door", "tool unavailable: just")
        exit_code = terminal_disposition(doctor)

    assert exit_code == COULD_NOT_OBSERVE_EXIT
    assert exit_code != 0
    assert "COULD-NOT-OBSERVE" in printed.getvalue()
    assert "OK" not in printed.getvalue()


def test_an_observed_defect_outranks_a_failure_to_observe() -> None:
    doctor = Doctor()
    printed = io.StringIO()

    with redirect_stdout(printed):
        doctor.cno("root `just` front door", "tool unavailable: just")
        doctor.fail("PATH uniqueness", "2 duplicate entries remain")
        exit_code = terminal_disposition(doctor)

    assert exit_code == 1
    assert "FAILED" in printed.getvalue()


def test_a_clean_doctor_still_passes() -> None:
    doctor = Doctor()
    printed = io.StringIO()

    with redirect_stdout(printed):
        doctor.ok("root `just` front door", "default recipe runs")
        exit_code = terminal_disposition(doctor)

    assert exit_code == 0
    assert "SSSF Windows host doctor: OK" in printed.getvalue()


# --- end to end, against the real executable -----------------------------


@POSIX_ONLY
def test_watched_red_doctor_never_crashes_with_every_child_tool_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The whole doctor still returns a three-valued report, not a traceback."""
    environment = dict(os.environ)
    environment["PATH"] = str(empty_dir(tmp_path, "empty-path"))

    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "windows_host.py"), "doctor"],
        cwd=ROOT,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=300,
    )

    assert "Traceback" not in completed.stdout
    assert "FileNotFoundError" not in completed.stdout
    assert completed.returncode in (0, 1, COULD_NOT_OBSERVE_EXIT)

    for label in (
        "root `just` front door",
        "`just local` front door",
    ):
        row = next(
            line
            for line in completed.stdout.splitlines()
            if label in line
        )
        assert row.strip().startswith("CNO"), row
