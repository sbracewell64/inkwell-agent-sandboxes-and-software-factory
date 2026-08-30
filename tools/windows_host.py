from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(
    0,
    str(ROOT),
)

from tools.ci_gate import (  # noqa: E402
    CNO_REASON_PREFIX,
    COULD_NOT_OBSERVE_EXIT,
    child_cno_reason,
)

CANONICAL_ORIGIN = (
    "https://github.com/"
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
)

MIN_PYTHON = (3, 11)
MIN_JUST = (1, 56, 0)

DEFAULT_CHILD_TIMEOUT_SECONDS = 30.0


def child_timeout_seconds() -> float:
    value = os.environ.get("SSSF_CHILD_TIMEOUT_SECONDS", "30")

    try:
        timeout = float(value)
    except ValueError:
        return DEFAULT_CHILD_TIMEOUT_SECONDS

    if not math.isfinite(timeout) or timeout <= 0:
        return DEFAULT_CHILD_TIMEOUT_SECONDS

    return timeout


# Bound every child so a wedged tool is a timed-out observation rather than a
# doctor that never returns.
CHILD_TIMEOUT_SECONDS = child_timeout_seconds()


class ChildObservation:
    """One child-tool spawn's three-valued result.

    `returncode` is None exactly when this doctor never reached an
    observation: the tool was absent or unspawnable, the working
    environment was unreadable, the child stopped answering, or the
    child reported its own failure to observe. A predicate that was
    never evaluated is could-not-observe — neither `ok` nor `FAIL` is
    honest about it.
    """

    def __init__(
        self,
        returncode: int | None,
        stdout: str = "",
        reason: str = "",
    ) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.reason = reason

    @property
    def observed(self) -> bool:
        return self.returncode is not None


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    timeout: float = CHILD_TIMEOUT_SECONDS,
) -> ChildObservation:
    """Spawn one child tool and return its three-valued observation.

    This never raises for a child that could not run. Letting the
    spawn error escape reports nothing at all, and inventing a return
    code for it would report a judgement no child ever made; both are
    narrowings of could-not-observe.

    `COULD_NOT_OBSERVE_EXIT` is repository-reserved for every child this
    doctor spawns, not only validators. Any child exiting with that code is
    therefore could-not-observe by convention; named reasons are carried
    through, and a bare exit uses the shared fallback reason.
    """
    tool = args[0] if args else "<no command>"

    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
    except OSError as exc:
        return ChildObservation(
            None,
            reason=(
                f"tool unavailable: "
                f"{tool}: {exc}"
            ),
        )
    except subprocess.TimeoutExpired:
        return ChildObservation(
            None,
            reason=(
                f"{tool} did not answer "
                f"within {timeout:g}s"
            ),
        )

    output = completed.stdout or ""

    if (
        completed.returncode
        == COULD_NOT_OBSERVE_EXIT
    ):
        return ChildObservation(
            None,
            output,
            child_cno_reason(output),
        )

    return ChildObservation(
        completed.returncode,
        output,
    )


def normalized_path_key(value: str) -> str:
    expanded = os.path.expandvars(
        os.path.expanduser(value.strip().strip('"'))
    )
    return os.path.normcase(os.path.normpath(expanded))


def path_entries() -> list[str]:
    return [
        entry
        for entry in os.environ.get("PATH", "").split(os.pathsep)
        if entry.strip()
    ]


def dedupe_paths(entries: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for entry in entries:
        key = normalized_path_key(entry)

        if key in seen:
            continue

        seen.add(key)
        result.append(entry)

    return result


def discover_git_root() -> Path | None:
    candidates: list[Path] = []

    resolved = shutil.which("git")

    if resolved:
        candidates.append(Path(resolved).resolve())

    program_files = os.environ.get("ProgramFiles")

    if program_files:
        base = Path(program_files) / "Git"

        candidates.extend(
            [
                base / "cmd" / "git.exe",
                base / "bin" / "git.exe",
            ]
        )

    for candidate in candidates:
        if not candidate.is_file():
            continue

        parent = candidate.parent

        if parent.name.lower() in {"cmd", "bin"}:
            return parent.parent

    return None


def build_bootstrap_path() -> str:
    git_root = discover_git_root()

    if git_root is None:
        raise RuntimeError(
            "Git for Windows could not be located; "
            "install Git before bootstrap"
        )

    preferred = [
        str(git_root / "bin"),
        str(git_root / "usr" / "bin"),
        str(Path.home() / ".local" / "bin"),
        str(Path.home() / ".bun" / "bin"),
    ]

    existing_preferred = [
        entry
        for entry in preferred
        if Path(entry).is_dir()
    ]

    merged = existing_preferred + path_entries()

    return os.pathsep.join(
        dedupe_paths(merged)
    )


class Doctor:
    def __init__(self) -> None:
        self.failed = False
        self.could_not_observe = False

    def ok(
        self,
        label: str,
        detail: str = "",
    ) -> None:
        suffix = f" — {detail}" if detail else ""
        print(f"  ok    {label}{suffix}")

    def fail(
        self,
        label: str,
        detail: str = "",
    ) -> None:
        suffix = f" — {detail}" if detail else ""
        print(f"  FAIL  {label}{suffix}")
        self.failed = True

    def cno(
        self,
        label: str,
        detail: str = "",
    ) -> None:
        """Record a predicate this doctor could not evaluate.

        Could-not-observe is a real result and never a pass: the row
        stays visible and the doctor stays non-OK, without claiming
        the predicate was judged.
        """
        reason = (
            detail
            or "no reason reported"
        )
        print(
            f"  CNO   {label} — "
            f"{CNO_REASON_PREFIX}{reason}"
        )
        self.could_not_observe = True

    def warn(
        self,
        label: str,
        detail: str = "",
    ) -> None:
        suffix = f" — {detail}" if detail else ""
        print(f"  WARN  {label}{suffix}")

    def info(
        self,
        label: str,
        detail: str = "",
    ) -> None:
        suffix = f" — {detail}" if detail else ""
        print(f"  info  {label}{suffix}")


def terminal_disposition(
    doctor: Doctor,
) -> int:
    """Print the doctor's verdict and return its exit code.

    An observed defect outranks a failure to observe: a doctor that
    judged anything false reports FAILED even when part of its
    evidence was unavailable. Only a run that judged nothing false and
    left something unobserved reports could-not-observe, and that exit
    is red, never a pass.
    """
    if doctor.failed:
        print(
            "SSSF Windows host doctor: "
            "FAILED"
        )
        return 1

    if doctor.could_not_observe:
        print(
            "SSSF Windows host doctor: "
            "COULD-NOT-OBSERVE"
        )
        return COULD_NOT_OBSERVE_EXIT

    print(
        "SSSF Windows host doctor: OK"
    )

    return 0


def check_child_probe(
    doctor: Doctor,
    label: str,
    args: list[str],
    *,
    success_detail: str,
    cwd: Path = ROOT,
) -> ChildObservation:
    """Record one child-tool probe under the three-valued boundary.

    A child that answered decides the row. A child this doctor could
    not execute leaves the predicate unobserved, so the row is
    could-not-observe rather than a FAIL the child never earned.
    """
    result = run(args, cwd=cwd)

    if not result.observed:
        doctor.cno(
            label,
            result.reason,
        )
    elif result.returncode != 0:
        doctor.fail(
            label,
            result.stdout.strip(),
        )
    else:
        doctor.ok(
            label,
            success_detail,
        )

    return result


STRICT_LINE_ENDING_INVOCATION = (
    "python docs/validation/check_line_endings.py "
    "--require-worktree-lf"
)


def check_line_ending_contract(
    doctor: Doctor,
    *,
    root: Path = ROOT,
) -> None:
    args = [
        sys.executable,
        str(
            ROOT
            / "docs"
            / "validation"
            / "check_line_endings.py"
        ),
        "--require-worktree-lf",
    ]

    if root != ROOT:
        args.extend(["--root", str(root)])

    line_endings = run(args, cwd=root)
    detail = line_endings.stdout.strip()
    success_marker = "B3-002 strict line-ending contract: PASS"

    if not line_endings.observed:
        doctor.cno(
            "line-ending contract",
            line_endings.reason,
        )
    elif line_endings.returncode != 0:
        doctor.fail(
            "line-ending contract",
            f"{STRICT_LINE_ENDING_INVOCATION}\n{detail}",
        )
    elif success_marker not in detail:
        doctor.cno(
            "line-ending contract",
            "strict validator returned no "
            "positive success marker",
        )
    else:
        doctor.ok(
            "line-ending contract",
            STRICT_LINE_ENDING_INVOCATION,
        )


def executable_version(
    name: str,
    *args: str,
) -> tuple[str | None, str, str]:
    """Resolve one tool and read its version.

    Returns the resolved path, the version text, and the reason the
    version could not be read. An absent tool has no version to
    observe, and a tool that could not be spawned reported none: both
    are could-not-observe for the version, whatever the doctor decides
    about the tool itself.
    """
    resolved = shutil.which(name)

    if not resolved:
        return (
            None,
            "",
            f"{name} is not on PATH, so "
            "no version was read",
        )

    proc = run(
        [resolved, *args]
    )

    if not proc.observed:
        return resolved, "", proc.reason

    return (
        resolved,
        proc.stdout.strip(),
        "",
    )


def parse_version(
    text: str,
) -> tuple[int, int, int] | None:
    match = re.search(
        r"(\d+)\.(\d+)(?:\.(\d+))?",
        text,
    )

    if not match:
        return None

    return (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3) or 0),
    )


def first_config_value(
    text: str,
    key: str,
) -> str | None:
    prefix = key.lower() + " "

    for line in text.splitlines():
        lowered = line.lower()

        if lowered.startswith(prefix):
            return line[len(prefix):].strip()

    return None


def check_ssh_config(
    doctor: Doctor,
    host: str,
) -> None:
    proc = run(
        ["ssh", "-G", host]
    )

    if not proc.observed:
        doctor.cno(
            f"ssh config {host}",
            proc.reason,
        )
        return

    if proc.returncode != 0:
        doctor.fail(
            f"ssh config {host}",
            proc.stdout.strip()
            or "ssh -G failed",
        )
        return

    identities_only = first_config_value(
        proc.stdout,
        "identitiesonly",
    )

    strict = first_config_value(
        proc.stdout,
        "stricthostkeychecking",
    )

    identity = first_config_value(
        proc.stdout,
        "identityfile",
    )

    problems: list[str] = []

    if identities_only != "yes":
        problems.append(
            f"IdentitiesOnly={identities_only!r}"
        )

    if strict != "accept-new":
        problems.append(
            f"StrictHostKeyChecking={strict!r}"
        )

    if not identity:
        problems.append(
            "no IdentityFile"
        )

    if problems:
        doctor.fail(
            f"ssh config {host}",
            "; ".join(problems),
        )
        return

    doctor.ok(
        f"ssh config {host}",
        "dedicated identity + "
        "accept-new policy resolved",
    )


def check_tool(
    doctor: Doctor,
    name: str,
    *version_args: str,
) -> tuple[str | None, str, str]:
    """Judge whether one tool is installed, and read its version.

    The predicate on this row is "is this tool installed on the host",
    and an absent tool answers it: the finding stays a FAIL. The
    version it would have reported is a different predicate that was
    never reached — the reason is returned so
    `check_version_contract` can record that one as CNO instead of
    inventing a verdict for it.
    """
    resolved, version, reason = executable_version(
        name,
        *version_args,
    )

    if not resolved:
        doctor.fail(
            name,
            "not found on PATH",
        )
        return None, "", reason

    first_line = (
        version.splitlines()[0]
        if version
        else resolved
    )

    doctor.ok(
        name,
        f"{resolved} [{first_line}]",
    )

    return resolved, version, reason


def check_version_contract(
    doctor: Doctor,
    label: str,
    version_text: str,
    minimum: tuple[int, ...],
    *,
    unobserved_reason: str,
) -> None:
    """Judge one minimum-version contract, three-valued.

    A tool that never ran reported no version to compare. Parsing its
    empty output into "could not parse" would state a version defect
    this doctor never observed, so an unreached reading is CNO. A tool
    that did run and answered unparseably or too low still FAILs.
    """
    if unobserved_reason:
        doctor.cno(
            label,
            unobserved_reason,
        )
        return

    version = parse_version(
        version_text
    )

    if version is None:
        doctor.fail(
            label,
            "could not parse "
            f"{version_text!r}",
        )
    elif version < minimum:
        doctor.fail(
            label,
            f"{version} < required "
            f"{minimum}",
        )
    else:
        doctor.ok(
            label,
            ".".join(
                map(str, version)
            ),
        )


def doctor(
    *,
    sandbox: bool,
) -> int:
    d = Doctor()

    print(
        "SSSF Windows host doctor"
    )

    if os.name != "nt":
        d.fail(
            "Windows host",
            f"os.name={os.name!r}",
        )
    else:
        d.ok(
            "Windows host",
            os.environ.get(
                "OS",
                "Windows",
            ),
        )

    if not (ROOT / ".git").exists():
        d.fail(
            "repository checkout",
            f"{ROOT} is not a Git "
            "worktree root",
        )
    else:
        d.ok(
            "repository checkout",
            str(ROOT),
        )

    git_root = discover_git_root()

    if git_root is None:
        d.fail(
            "Git for Windows root",
            "could not derive "
            "installation root",
        )
    else:
        d.ok(
            "Git for Windows root",
            str(git_root),
        )

    entries = path_entries()
    deduped = dedupe_paths(entries)

    if len(entries) != len(deduped):
        d.fail(
            "PATH uniqueness",
            f"{len(entries) - len(deduped)} "
            "duplicate entries remain",
        )
    else:
        d.ok(
            "PATH uniqueness",
            f"{len(entries)} unique entries",
        )

    if git_root is not None:
        required_git_paths = [
            git_root / "bin",
            git_root / "usr" / "bin",
        ]

        path_keys = {
            normalized_path_key(entry)
            for entry in entries
        }

        for required in required_git_paths:
            if (
                normalized_path_key(
                    str(required)
                )
                in path_keys
            ):
                d.ok(
                    "PATH contains",
                    str(required),
                )
            else:
                d.fail(
                    "PATH contains",
                    f"missing {required}",
                )

    _, _, _ = check_tool(
        d,
        "git",
        "--version",
    )

    sh_path, _, _ = check_tool(
        d,
        "sh",
        "--version",
    )

    cygpath_path, _, _ = check_tool(
        d,
        "cygpath",
        "--version",
    )

    ssh_path, _, _ = check_tool(
        d,
        "ssh",
        "-V",
    )

    (
        _,
        python_version,
        python_reason,
    ) = check_tool(
        d,
        "python",
        "--version",
    )

    (
        _,
        python3_version,
        python3_reason,
    ) = check_tool(
        d,
        "python3",
        "--version",
    )

    check_tool(
        d,
        "bun",
        "--version",
    )

    check_tool(
        d,
        "uv",
        "--version",
    )

    (
        _,
        just_version,
        just_reason,
    ) = check_tool(
        d,
        "just",
        "--version",
    )

    check_tool(
        d,
        "gh",
        "--version",
    )

    if git_root is not None:
        expected_sh_paths = {
            normalized_path_key(
                str(
                    git_root
                    / "bin"
                    / "sh.exe"
                )
            ),
            normalized_path_key(
                str(
                    git_root
                    / "usr"
                    / "bin"
                    / "sh.exe"
                )
            ),
        }

        if (
            sh_path
            and normalized_path_key(
                sh_path
            )
            not in expected_sh_paths
        ):
            d.fail(
                "Git Bash selection",
                f"sh resolved to {sh_path}",
            )
        elif sh_path:
            d.ok(
                "Git Bash selection",
                sh_path,
            )

        expected_cygpath = (
            normalized_path_key(
                str(
                    git_root
                    / "usr"
                    / "bin"
                    / "cygpath.exe"
                )
            )
        )

        if (
            cygpath_path
            and normalized_path_key(
                cygpath_path
            )
            != expected_cygpath
        ):
            d.fail(
                "cygpath selection",
                f"resolved to "
                f"{cygpath_path}",
            )
        elif cygpath_path:
            d.ok(
                "cygpath selection",
                cygpath_path,
            )

        expected_ssh = (
            normalized_path_key(
                str(
                    git_root
                    / "usr"
                    / "bin"
                    / "ssh.exe"
                )
            )
        )

        if (
            ssh_path
            and normalized_path_key(
                ssh_path
            )
            != expected_ssh
        ):
            d.fail(
                "SSH selection",
                "expected Git SSH, "
                f"got {ssh_path}",
            )
        elif ssh_path:
            d.ok(
                "SSH selection",
                ssh_path,
            )

    for label, text, reason in (
        (
            "python compatibility",
            python_version,
            python_reason,
        ),
        (
            "python3 compatibility",
            python3_version,
            python3_reason,
        ),
    ):
        check_version_contract(
            d,
            label,
            text,
            MIN_PYTHON,
            unobserved_reason=reason,
        )

    check_version_contract(
        d,
        "just compatibility",
        just_version,
        MIN_JUST,
        unobserved_reason=just_reason,
    )

    origin = run(
        [
            "git",
            "remote",
            "get-url",
            "origin",
        ]
    )

    if not origin.observed:
        d.cno(
            "canonical origin",
            origin.reason,
        )
    elif origin.returncode != 0:
        d.fail(
            "canonical origin",
            origin.stdout.strip(),
        )
    elif (
        origin.stdout.strip()
        != CANONICAL_ORIGIN
    ):
        d.fail(
            "canonical origin",
            "got "
            f"{origin.stdout.strip()!r}",
        )
    else:
        d.ok(
            "canonical origin",
            CANONICAL_ORIGIN,
        )

    check_line_ending_contract(d)

    check_child_probe(
        d,
        "observability query contract",
        [
            sys.executable,
            "docs/validation/"
            "check_obs_query.py",
        ],
        success_detail=(
            "B3-004 validator PASS"
        ),
    )

    check_child_probe(
        d,
        "root `just` front door",
        ["just"],
        success_detail=(
            "default recipe runs"
        ),
    )

    check_child_probe(
        d,
        "`just local` front door",
        [
            "just",
            "local",
        ],
        success_detail=(
            "default recipe runs"
        ),
    )

    check_ssh_config(
        d,
        "exe.dev",
    )

    check_ssh_config(
        d,
        "b3-host-probe.exe.xyz",
    )

    external_sqlite = shutil.which(
        "sqlite3"
    )

    if external_sqlite:
        d.info(
            "external sqlite3",
            (
                f"{external_sqlite}; "
                "optional after B3-004"
            ),
        )
    else:
        d.info(
            "external sqlite3",
            (
                "absent; host observability "
                "uses Python stdlib sqlite3"
            ),
        )

    if shutil.which("zsh"):
        d.info(
            "zsh",
            shutil.which("zsh")
            or "",
        )
    else:
        d.info(
            "zsh",
            "absent; not required on "
            "Windows after B3-003",
        )

    for optional in (
        "claude",
        "pi",
        "herdr",
    ):
        resolved = shutil.which(
            optional
        )

        if resolved:
            d.info(
                optional,
                resolved,
            )
        else:
            d.info(
                optional,
                "not installed; optional "
                "for host portability",
            )

    if sandbox:
        check_child_probe(
            d,
            "sandbox doctor",
            [
                "just",
                "sbx",
                "manage",
                "doctor",
            ],
            success_detail=(
                "sbx doctor: OK"
            ),
        )

    return terminal_disposition(d)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "SSSF Windows bootstrap "
            "and host-doctor helper."
        )
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "emit-path",
        help=(
            "Print an idempotent "
            "Windows session PATH."
        ),
    )

    doctor_parser = sub.add_parser(
        "doctor",
        help=(
            "Validate the Windows "
            "host contract."
        ),
    )

    doctor_parser.add_argument(
        "--sandbox",
        action="store_true",
        help=(
            "Also run the network/"
            "credential sandbox doctor."
        ),
    )

    args = parser.parse_args()

    if args.command == "emit-path":
        try:
            print(
                build_bootstrap_path()
            )
        except RuntimeError as exc:
            print(
                str(exc),
                file=sys.stderr,
            )
            return 1

        return 0

    if args.command == "doctor":
        return doctor(
            sandbox=args.sandbox
        )

    return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
