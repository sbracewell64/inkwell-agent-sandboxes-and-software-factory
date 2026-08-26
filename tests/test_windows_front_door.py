from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPOSITORY_ROOT / "bin" / "sssf-firstmate.cmd"
CANONICAL_WINDOWS_ROOT = r"E:\SSSF"
CANONICAL_REPOSITORY = (
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory"
)
PUBLIC_IDENTITY = (
    f"SSSF front door: project=sssf repository={CANONICAL_REPOSITORY} "
    f"root={CANONICAL_WINDOWS_ROOT} handoff=firstmate"
)


def _cmd_executable() -> str | None:
    if os.name == "nt":
        return shutil.which("cmd.exe") or shutil.which("cmd")
    for candidate in (shutil.which("cmd.exe"), "/mnt/c/WINDOWS/system32/cmd.exe"):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def _windows_path(path: Path) -> str | None:
    if os.name == "nt":
        return str(path)
    wslpath = shutil.which("wslpath")
    if not wslpath:
        return None
    result = subprocess.run(
        [wslpath, "-w", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def _caller_directories() -> list[Path]:
    if os.name == "nt":
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        public_root = Path(os.environ.get("PUBLIC", r"C:\Users\Public"))
    else:
        system_root = Path("/mnt/c/Windows")
        public_root = Path("/mnt/c/Users/Public")
    return [path for path in (system_root, public_root) if path.is_dir()]


def _launcher_shell_commands() -> tuple[str, str]:
    source = LAUNCHER.read_text(encoding="utf-8")
    commands = re.findall(r'--exec /bin/(?:ba)?sh -c "(.*)"', source)
    if len(commands) != 2:
        raise AssertionError("expected Bash preflight and handoff commands")
    return commands[0], commands[1].replace("%%", "%")


def _assert_public_identity(output: str) -> None:
    identity_lines = [
        line for line in output.splitlines() if line.startswith("SSSF front door: ")
    ]
    if identity_lines != [PUBLIC_IDENTITY]:
        raise AssertionError(f"unexpected public identity: {identity_lines!r}")
    for prohibited in ("head=", "branch="):
        if prohibited in output:
            raise AssertionError(f"prohibited public identity field: {prohibited}")


def _create_checkout_fixture(root: Path) -> tuple[Path, Path]:
    checkout = root / "checkout"
    firstmate = root / "firstmate"
    checkout.mkdir()
    (checkout / "bin").mkdir()
    (checkout / "AGENTS.md").write_text("fixture\n", encoding="utf-8")
    (checkout / "bin" / "sssf-windows.cmd").write_text("fixture\n", encoding="utf-8")
    subprocess.run(["git", "init", "-b", "fixture-branch"], cwd=checkout, check=True, capture_output=True)
    subprocess.run(
        ["git", "remote", "add", "origin", f"https://github.com/{CANONICAL_REPOSITORY}.git"],
        cwd=checkout,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=checkout, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture"],
        cwd=checkout,
        check=True,
        capture_output=True,
    )
    (firstmate / "bin").mkdir(parents=True)
    (firstmate / "data").mkdir()
    for name in ("fm-launch.sh", "fm-admission.sh", "fm-session-start.sh"):
        script = firstmate / "bin" / name
        script.write_text("#!/bin/sh\nprintf 'Firstmate fixture\\n'\n", encoding="utf-8")
        script.chmod(0o755)
    (firstmate / "data" / "projects.md").write_text("- sssf [fixture]\n", encoding="utf-8")
    return checkout, firstmate


def _run_handoff(
    command: str, checkout: Path, firstmate: Path, path: str
) -> subprocess.CompletedProcess[str]:
    fixture_command = command.replace(
        "case $root in /mnt/e/SSSF)",
        f"case $root in {shlex.quote(str(checkout.resolve()))})",
    ).replace("mode=%SSSF_LAUNCH_MODE%", "mode=print-menu")
    environment = os.environ.copy()
    environment.update(
        {
            "HOME": str(checkout),
            "PATH": path,
            "SSSF_FIRSTMATE_ROOT": str(firstmate),
        }
    )
    return subprocess.run(
        ["/bin/bash", "-c", fixture_command],
        cwd=checkout,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )


class WindowsFrontDoorContractTests(unittest.TestCase):
    def test_public_identity_executes_attached_and_detached_checkout_fixtures(self) -> None:
        _, handoff = _launcher_shell_commands()
        with tempfile.TemporaryDirectory() as temporary_directory:
            checkout, firstmate = _create_checkout_fixture(Path(temporary_directory))
            attached = _run_handoff(handoff, checkout, firstmate, os.environ["PATH"])
            self.assertEqual(attached.returncode, 0, attached.stderr)
            _assert_public_identity(attached.stdout)

            subprocess.run(
                ["git", "checkout", "--detach", "HEAD"],
                cwd=checkout,
                check=True,
                capture_output=True,
            )
            detached = _run_handoff(handoff, checkout, firstmate, os.environ["PATH"])
            self.assertEqual(detached.returncode, 0, detached.stderr)
            _assert_public_identity(detached.stdout)

            for prohibited in ("head=", "branch="):
                defective_command = handoff.replace(
                    "handoff=firstmate\\n'",
                    f"handoff=firstmate {prohibited}stale\\n'",
                )
                self.assertNotEqual(defective_command, handoff)
                defective = _run_handoff(
                    defective_command, checkout, firstmate, os.environ["PATH"]
                )
                with self.assertRaises(AssertionError):
                    _assert_public_identity(defective.stdout)

    def test_dependency_preflight_executes_missing_bash_git_and_grep_fixtures(self) -> None:
        bash_preflight, handoff = _launcher_shell_commands()
        with tempfile.TemporaryDirectory() as temporary_directory:
            fixture_root = Path(temporary_directory)
            checkout, firstmate = _create_checkout_fixture(fixture_root)
            missing_bash = fixture_root / "missing-bash"
            bash_command = bash_preflight.replace("/bin/bash", str(missing_bash))
            bash_result = subprocess.run(
                ["/bin/sh", "-c", bash_command], check=False, capture_output=True, text=True
            )
            self.assertEqual(bash_result.returncode, 127)
            self.assertIn("could not find Bash", bash_result.stdout)
            self.assertIn("Install Bash", bash_result.stdout)

            empty_path = fixture_root / "empty-path"
            empty_path.mkdir()
            git_result = _run_handoff(handoff, checkout, firstmate, str(empty_path))
            self.assertEqual(git_result.returncode, 127)
            self.assertIn("could not find Git", git_result.stdout)
            self.assertIn("Install Git", git_result.stdout)
            self.assertNotIn("non-canonical origin", git_result.stdout)

            git_path = fixture_root / "git-path"
            git_path.mkdir()
            (git_path / "git").symlink_to(shutil.which("git"))
            grep_result = _run_handoff(handoff, checkout, firstmate, str(git_path))
            self.assertEqual(grep_result.returncode, 127)
            self.assertIn("could not find grep", grep_result.stdout)
            self.assertIn("Install grep", grep_result.stdout)
            self.assertNotIn("not registered", grep_result.stdout)

            defective_bash = subprocess.run(
                ["/bin/sh", "-c", ":"], check=False, capture_output=True, text=True
            )
            defective_git_command = handoff.replace(
                "command -v git >/dev/null 2>&1 || { echo 'SSSF front door could not find Git in WSL.'; echo 'Install Git in the WSL distribution, then retry.'; exit 127; }; ",
                "",
            )
            grep_path = fixture_root / "grep-path"
            grep_path.mkdir()
            (grep_path / "grep").symlink_to(shutil.which("grep"))
            defective_git = _run_handoff(
                defective_git_command, checkout, firstmate, str(grep_path)
            )
            defective_grep_command = handoff.replace(
                "command -v grep >/dev/null 2>&1 || { echo 'SSSF front door could not find grep in WSL.'; echo 'Install grep in the WSL distribution, then retry.'; exit 127; }; ",
                "",
            )
            defective_grep = _run_handoff(
                defective_grep_command, checkout, firstmate, str(git_path)
            )
            self.assertEqual(defective_bash.returncode, 0)
            self.assertNotIn("could not find Bash", defective_bash.stdout)
            self.assertIn("non-canonical origin", defective_git.stdout)
            self.assertIn("not registered", defective_grep.stdout)

    def test_tracked_launcher_contract_is_canonical_and_transport_only(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('set "SSSF_ROOT=E:\\SSSF"', source)
        self.assertIn('--cd "%SSSF_ROOT%"', source)
        self.assertIn("--exec /bin/bash -c", source)
        self.assertIn(CANONICAL_REPOSITORY, source)
        self.assertIn("handoff=firstmate", source)
        self.assertIn("fm-admission.sh", source)
        self.assertIn("fm-session-start.sh", source)
        self.assertNotIn("%CD%", source)
        self.assertNotIn("head=", source)
        self.assertNotIn("branch=", source)
        self.assertNotIn("just local", source)
        self.assertNotIn("docker", source.lower())
        self.assertNotIn("wayfinder", source.lower())
        self.assertNotIn("dsh", source.lower())

    @unittest.skipUnless(_cmd_executable(), "could-not-observe: Windows cmd.exe is unavailable")
    def test_print_menu_reaches_canonical_root_from_independent_cwds(self) -> None:
        cmd = _cmd_executable()
        launcher = _windows_path(LAUNCHER)
        callers = _caller_directories()
        if not cmd or not launcher or len(callers) < 2:
            self.skipTest(
                "could-not-observe: Windows interop or two independent caller directories unavailable"
            )

        for caller in callers[:2]:
            result = subprocess.run(
                [cmd, "/d", "/c", "call", launcher, "--print-menu"],
                cwd=caller,
                check=False,
                capture_output=True,
                text=True,
            )
            output = f"{result.stdout}\n{result.stderr}"
            self.assertEqual(result.returncode, 0, output)
            self.assertIn(
                f"root={CANONICAL_WINDOWS_ROOT}",
                output,
            )
            self.assertIn("handoff=firstmate", output)
            self.assertIn(CANONICAL_REPOSITORY, output)
            self.assertIn("Firstmate", output)

    @unittest.skipUnless(_cmd_executable(), "could-not-observe: Windows cmd.exe is unavailable")
    def test_default_herdr_session_is_refused(self) -> None:
        cmd = _cmd_executable()
        launcher = _windows_path(LAUNCHER)
        callers = _caller_directories()
        if not cmd or not launcher or not callers:
            self.skipTest("could-not-observe: Windows command host unavailable")

        result = subprocess.run(
            [
                cmd,
                "/d",
                "/c",
                f"set SSSF_HERDR_LAB_SESSION=default&& call {launcher} --print-menu",
            ],
            cwd=callers[0],
            check=False,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\\n{result.stderr}"
        self.assertEqual(result.returncode, 2, output)
        self.assertIn("named non-default Herdr lab session", output)

    @unittest.skipUnless(_cmd_executable(), "could-not-observe: Windows cmd.exe is unavailable")
    def test_unknown_argument_fails_visibly(self) -> None:
        cmd = _cmd_executable()
        launcher = _windows_path(LAUNCHER)
        callers = _caller_directories()
        if not cmd or not launcher or not callers:
            self.skipTest("could-not-observe: Windows command host unavailable")

        result = subprocess.run(
            [cmd, "/d", "/c", "call", launcher, "--unexpected"],
            cwd=callers[0],
            check=False,
            capture_output=True,
            text=True,
        )
        output = f"{result.stdout}\n{result.stderr}"
        self.assertEqual(result.returncode, 2, output)
        self.assertIn("Unknown or extra command-line values were refused", output)


if __name__ == "__main__":
    unittest.main()
