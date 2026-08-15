from __future__ import annotations

from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from check_line_endings import REPRESENTATIVE_FILES

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "docs" / "validation" / "check_line_endings.py"

sys.path.insert(0, str(ROOT))
from tools.windows_host import Doctor, check_line_ending_contract  # noqa: E402


class LineEndingContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.fixture = Path(self._temporary.name) / "fixture"
        self.fixture.mkdir()
        self.git("init", "--quiet")
        self.git("config", "user.name", "Line Ending Test")
        self.git("config", "user.email", "line-ending-test@example.invalid")
        self.git("config", "core.autocrlf", "false")
        (self.fixture / ".gitattributes").write_text(
            "# One repository-owned text rule.\n"
            "* text=auto eol=lf\n",
            encoding="utf-8",
            newline="\n",
        )

        for relative in REPRESENTATIVE_FILES:
            path = self.fixture / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"fixture for {relative}\nsecond line\n",
                encoding="utf-8",
                newline="\n",
            )

        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "fixture")

    def tearDown(self) -> None:
        self._temporary.cleanup()

    def git(
        self,
        *args: str,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *args),
            cwd=cwd or self.fixture,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )

    def validate(
        self,
        *,
        root: Path | None = None,
        explicit: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        args = [
            sys.executable,
            str(VALIDATOR),
            "--root",
            str(root or self.fixture),
        ]

        if explicit:
            args.append("--require-worktree-lf")

        return subprocess.run(
            args,
            cwd=root or self.fixture,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def assert_green_fixture(self) -> None:
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("strict line-ending contract: PASS", result.stdout)

    def assert_terminal_non_pass(
        self,
        result: subprocess.CompletedProcess[str],
        evidence: str,
    ) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("PASS", result.stdout)
        self.assertIn(evidence, result.stdout)

    def materialize_crlf(self, relative: str = "justfile") -> None:
        path = self.fixture / relative
        data = path.read_bytes()
        self.assertNotIn(b"\r\n", data)
        path.write_bytes(data.replace(b"\n", b"\r\n"))

    def test_watched_red_crlf_is_not_masked_by_default_or_doctor(self) -> None:
        self.assert_green_fixture()
        self.materialize_crlf()

        default_result = self.validate()
        self.assert_terminal_non_pass(default_result, "observed-bad")
        self.assertIn("working-tree state is 'w/crlf'", default_result.stdout)

        doctor = Doctor()
        output = io.StringIO()

        with redirect_stdout(output):
            check_line_ending_contract(doctor, root=self.fixture)

        self.assertTrue(doctor.failed)
        self.assertNotIn("PASS", output.getvalue())
        self.assertIn(
            "python docs/validation/check_line_endings.py "
            "--require-worktree-lf",
            output.getvalue(),
        )
        self.assertIn("observed-bad", output.getvalue())

    def test_watched_red_missing_file_is_could_not_observe(self) -> None:
        self.assert_green_fixture()
        (self.fixture / "justfile").unlink()
        result = self.validate(explicit=True)
        self.assert_terminal_non_pass(result, "could-not-observe")
        self.assertIn("representative file is missing", result.stdout)

    def test_watched_red_wrong_attribute_is_observed_bad(self) -> None:
        self.assert_green_fixture()
        (self.fixture / ".gitattributes").write_text(
            "* text=auto eol=crlf\n",
            encoding="utf-8",
            newline="\n",
        )
        result = self.validate(explicit=True)
        self.assert_terminal_non_pass(result, "observed-bad")
        self.assertIn("expected 'lf'", result.stdout)

    def test_explicit_rematerialization_preserves_index(self) -> None:
        self.assert_green_fixture()
        self.materialize_crlf()
        (self.fixture / ".gitattributes").write_text(
            "* text=auto eol=crlf\n",
            encoding="utf-8",
            newline="\n",
        )
        red = self.validate(explicit=True)
        self.assert_terminal_non_pass(red, "observed-bad")
        tree_before = self.git("write-tree").stdout.strip()
        self.git(
            "checkout-index",
            "--force",
            "--",
            ".gitattributes",
            *REPRESENTATIVE_FILES,
        )
        tree_after = self.git("write-tree").stdout.strip()
        self.assertEqual(tree_before, tree_after)
        self.assertEqual(self.git("status", "--short").stdout, "")
        self.assertEqual(self.validate(explicit=True).returncode, 0)

    def test_hostile_autocrlf_fresh_clone_materializes_lf(self) -> None:
        clone = Path(self._temporary.name) / "hostile-clone"
        subprocess.run(
            (
                "git",
                "clone",
                "--quiet",
                "--config",
                "core.autocrlf=true",
                str(self.fixture),
                str(clone),
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=True,
        )
        self.assertEqual(
            self.git("config", "--get", "core.autocrlf", cwd=clone).stdout.strip(),
            "true",
        )
        result = self.validate(root=clone, explicit=True)
        self.assertEqual(result.returncode, 0, result.stdout)

        for relative in REPRESENTATIVE_FILES:
            state = self.git(
                "ls-files",
                "--eol",
                "--",
                relative,
                cwd=clone,
            ).stdout
            self.assertIn("i/lf", state, state)
            self.assertIn("w/lf", state, state)
            self.assertIn("attr/text=auto eol=lf", state, state)


if __name__ == "__main__":
    unittest.main()
