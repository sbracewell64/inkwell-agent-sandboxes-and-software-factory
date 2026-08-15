from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

DEFAULT_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_RULES = (
    "* text=auto eol=lf",
)

REPRESENTATIVE_FILES = (
    "justfile",
    "just/sandbox/lifecycle/fill.just",
    "just/sandbox/lifecycle/setup.just",
    "sandbox_mount/guest/provision.sh",
    "sandbox_mount/host/run_record.py",
    "docs/baseline/PROOF_MATRIX.md",
)

STRICT_INVOCATION = (
    "python docs/validation/check_line_endings.py "
    "--require-worktree-lf"
)


def git(root: Path, *args: str) -> tuple[str, str | None]:
    try:
        proc = subprocess.run(
            ("git", *args),
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    except OSError as exc:
        return "", str(exc)

    output = proc.stdout.strip()

    if proc.returncode != 0:
        return output, output or f"git exited {proc.returncode} without output"

    return output, None


def attr_value(
    root: Path,
    path: str,
    attr: str,
) -> tuple[str, str | None]:
    output, error = git(root, "check-attr", attr, "--", path)

    if error:
        return "", error

    prefix = f"{path}: {attr}: "

    if not output.startswith(prefix):
        return "", f"unexpected git check-attr output: {output!r}"

    return output[len(prefix):], None


def eol_state(
    root: Path,
    path: str,
) -> tuple[tuple[str, str, str] | None, str | None]:
    output, error = git(root, "ls-files", "--eol", "--", path)

    if error:
        return None, error

    if not output:
        return None, "git ls-files --eol returned no tracked entry"

    parts = output.split(maxsplit=3)

    if len(parts) < 3:
        return None, f"unexpected git ls-files --eol output: {output!r}"

    return (parts[0], parts[1], parts[2]), None


def active_attribute_rules(path: Path) -> tuple[str, ...]:
    text = path.read_text(encoding="utf-8-sig")

    rules: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        rules.append(line)

    return tuple(rules)


def print_remediation() -> None:
    watched = " ".join((".gitattributes", *REPRESENTATIVE_FILES))
    print("remediation (explicit; this validator never rewrites the working tree):")
    print("1. Save or commit local work; require `git status --short` to be empty.")
    print("2. Re-materialize watched files from the unchanged index:")
    print(f"   git checkout-index --force -- {watched}")
    print("3. Re-run the strict owner:")
    print(f"   {STRICT_INVOCATION}")


def validate(root: Path) -> int:
    observed_bad: list[str] = []
    could_not_observe: list[str] = []

    attributes_path = root / ".gitattributes"

    if not attributes_path.is_file():
        could_not_observe.append(".gitattributes is missing or unreadable")
    else:
        try:
            rules = active_attribute_rules(attributes_path)
        except (OSError, UnicodeError) as exc:
            could_not_observe.append(f"could not read .gitattributes: {exc}")
        else:
            if rules != EXPECTED_RULES:
                observed_bad.append(
                    "active .gitattributes rules are "
                    f"{rules!r}, expected {EXPECTED_RULES!r}"
                )

    for path in REPRESENTATIVE_FILES:
        full_path = root / path

        if not full_path.is_file():
            could_not_observe.append(
                f"representative file is missing or unreadable: {path}"
            )
            continue

        text_attr, text_error = attr_value(root, path, "text")
        eol_attr, eol_error = attr_value(root, path, "eol")

        if text_error:
            could_not_observe.append(
                f"{path}: could not observe text attribute: {text_error}"
            )
        elif text_attr != "auto":
            observed_bad.append(
                f"{path}: text attribute is {text_attr!r}, expected 'auto'"
            )

        if eol_error:
            could_not_observe.append(
                f"{path}: could not observe eol attribute: {eol_error}"
            )
        elif eol_attr != "lf":
            observed_bad.append(
                f"{path}: eol attribute is {eol_attr!r}, expected 'lf'"
            )

        state, state_error = eol_state(root, path)

        if state_error or state is None:
            could_not_observe.append(
                f"{path}: could not observe index/worktree state: "
                f"{state_error or 'unknown error'}"
            )
            continue

        index_eol, worktree_eol, _ = state

        if index_eol != "i/lf":
            observed_bad.append(
                f"{path}: index state is {index_eol!r}, expected 'i/lf'"
            )

        if worktree_eol != "w/lf":
            observed_bad.append(
                f"{path}: working-tree state is {worktree_eol!r}, "
                "expected 'w/lf'"
            )

    if observed_bad or could_not_observe:
        outcome = "FAIL" if observed_bad else "CNO"
        print(f"B3-002 strict line-ending contract: {outcome}")

        for error in observed_bad:
            print(f"- observed-bad: {error}")

        for error in could_not_observe:
            print(f"- could-not-observe: {error}")

        print_remediation()
        return 1

    print("B3-002 strict line-ending contract: PASS")
    print("policy: * text=auto eol=lf")
    print("representative index/worktree states: i/lf w/lf")

    autocrlf, autocrlf_error = git(root, "config", "--get", "core.autocrlf")

    if autocrlf_error and "exited 1" not in autocrlf_error:
        print(f"observed core.autocrlf: could-not-observe ({autocrlf_error})")
    else:
        print(f"observed core.autocrlf: {autocrlf or '<unset>'}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the strict B3-002 repository line-ending contract."
    )
    parser.add_argument(
        "--require-worktree-lf",
        action="store_true",
        help=(
            "Explicit spelling of the strict contract. Working-tree LF is "
            "always required, including when this option is omitted."
        ),
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    return validate(args.root.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
