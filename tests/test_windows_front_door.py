from __future__ import annotations

import os
import shutil
import subprocess
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = REPOSITORY_ROOT / "bin" / "sssf-firstmate.cmd"
CANONICAL_WINDOWS_ROOT = r"E:\SSSF"
CANONICAL_REPOSITORY = (
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory"
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


class WindowsFrontDoorContractTests(unittest.TestCase):
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
