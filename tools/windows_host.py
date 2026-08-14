from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

CANONICAL_ORIGIN = (
    "https://github.com/"
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
)

MIN_PYTHON = (3, 11)
MIN_JUST = (1, 56, 0)


def run(
    args: list[str],
    *,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
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


def executable_version(
    name: str,
    *args: str,
) -> tuple[str | None, str]:
    resolved = shutil.which(name)

    if not resolved:
        return None, ""

    proc = run(
        [resolved, *args]
    )

    return resolved, proc.stdout.strip()


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
) -> tuple[str | None, str]:
    resolved, version = executable_version(
        name,
        *version_args,
    )

    if not resolved:
        doctor.fail(
            name,
            "not found on PATH",
        )
        return None, ""

    first_line = (
        version.splitlines()[0]
        if version
        else resolved
    )

    doctor.ok(
        name,
        f"{resolved} [{first_line}]",
    )

    return resolved, version


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

    _, _ = check_tool(
        d,
        "git",
        "--version",
    )

    sh_path, _ = check_tool(
        d,
        "sh",
        "--version",
    )

    cygpath_path, _ = check_tool(
        d,
        "cygpath",
        "--version",
    )

    ssh_path, _ = check_tool(
        d,
        "ssh",
        "-V",
    )

    _, python_version = check_tool(
        d,
        "python",
        "--version",
    )

    _, python3_version = check_tool(
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

    _, just_version = check_tool(
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

    for label, text in (
        (
            "python compatibility",
            python_version,
        ),
        (
            "python3 compatibility",
            python3_version,
        ),
    ):
        version = parse_version(text)

        if version is None:
            d.fail(
                label,
                f"could not parse {text!r}",
            )
        elif version < MIN_PYTHON:
            d.fail(
                label,
                f"{version} < required "
                f"{MIN_PYTHON}",
            )
        else:
            d.ok(
                label,
                ".".join(
                    map(str, version)
                ),
            )

    parsed_just = parse_version(
        just_version
    )

    if parsed_just is None:
        d.fail(
            "just compatibility",
            "could not parse "
            f"{just_version!r}",
        )
    elif parsed_just < MIN_JUST:
        d.fail(
            "just compatibility",
            f"{parsed_just} < required "
            f"{MIN_JUST}",
        )
    else:
        d.ok(
            "just compatibility",
            ".".join(
                map(str, parsed_just)
            ),
        )

    origin = run(
        [
            "git",
            "remote",
            "get-url",
            "origin",
        ]
    )

    if origin.returncode != 0:
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

    line_endings = run(
        [
            sys.executable,
            "docs/validation/"
            "check_line_endings.py",
        ]
    )

    if line_endings.returncode != 0:
        d.fail(
            "line-ending contract",
            line_endings.stdout.strip(),
        )
    else:
        d.ok(
            "line-ending contract",
            "B3-002 validator PASS",
        )

    obs_query = run(
        [
            sys.executable,
            "docs/validation/"
            "check_obs_query.py",
        ]
    )

    if obs_query.returncode != 0:
        d.fail(
            "observability query contract",
            obs_query.stdout.strip(),
        )
    else:
        d.ok(
            "observability query contract",
            "B3-004 validator PASS",
        )

    root_front = run(
        ["just"]
    )

    if root_front.returncode != 0:
        d.fail(
            "root `just` front door",
            root_front.stdout.strip(),
        )
    else:
        d.ok(
            "root `just` front door",
            "default recipe runs",
        )

    local_front = run(
        [
            "just",
            "local",
        ]
    )

    if local_front.returncode != 0:
        d.fail(
            "`just local` front door",
            local_front.stdout.strip(),
        )
    else:
        d.ok(
            "`just local` front door",
            "default recipe runs",
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
        sandbox_doctor = run(
            [
                "just",
                "sbx",
                "manage",
                "doctor",
            ]
        )

        if (
            sandbox_doctor.returncode
            != 0
        ):
            d.fail(
                "sandbox doctor",
                sandbox_doctor.stdout.strip(),
            )
        else:
            d.ok(
                "sandbox doctor",
                "sbx doctor: OK",
            )

    if d.failed:
        print(
            "SSSF Windows host doctor: "
            "FAILED"
        )
        return 1

    print(
        "SSSF Windows host doctor: OK"
    )

    return 0


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