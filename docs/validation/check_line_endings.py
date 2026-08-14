from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

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


def git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args),
        cwd=ROOT,
        text=True,
    ).strip()


def attr_value(path: str, attr: str) -> str:
    output = git("check-attr", attr, "--", path)
    prefix = f"{path}: {attr}: "

    if not output.startswith(prefix):
        return ""

    return output[len(prefix):]


def eol_state(path: str) -> tuple[str, str, str]:
    output = git("ls-files", "--eol", "--", path)

    if not output:
        return "", "", ""

    parts = output.split()

    if len(parts) < 3:
        return "", "", ""

    return parts[0], parts[1], parts[2]


def active_attribute_rules(path: Path) -> tuple[str, ...]:
    text = path.read_text(encoding="utf-8-sig")

    rules: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        rules.append(line)

    return tuple(rules)


parser = argparse.ArgumentParser(
    description="Validate the B3-002 repository line-ending contract."
)

parser.add_argument(
    "--require-worktree-lf",
    action="store_true",
    help=(
        "Also require representative text files to be materialized "
        "as LF in the current working tree."
    ),
)

args = parser.parse_args()

errors: list[str] = []

attributes_path = ROOT / ".gitattributes"

if not attributes_path.is_file():
    errors.append(".gitattributes is missing")
else:
    rules = active_attribute_rules(attributes_path)

    if rules != EXPECTED_RULES:
        errors.append(
            "active .gitattributes rules are "
            f"{rules!r}, expected {EXPECTED_RULES!r}"
        )

for path in REPRESENTATIVE_FILES:
    full_path = ROOT / path

    if not full_path.is_file():
        errors.append(f"representative file is missing: {path}")
        continue

    text_attr = attr_value(path, "text")
    eol_attr = attr_value(path, "eol")

    if text_attr != "auto":
        errors.append(
            f"{path}: text attribute is {text_attr!r}, expected 'auto'"
        )

    if eol_attr != "lf":
        errors.append(
            f"{path}: eol attribute is {eol_attr!r}, expected 'lf'"
        )

    index_eol, worktree_eol, _ = eol_state(path)

    if index_eol != "i/lf":
        errors.append(
            f"{path}: index state is {index_eol!r}, expected 'i/lf'"
        )

    if args.require_worktree_lf and worktree_eol != "w/lf":
        errors.append(
            f"{path}: working-tree state is {worktree_eol!r}, "
            "expected 'w/lf'"
        )

if errors:
    print("B3-002 line-ending contract: FAIL")

    for error in errors:
        print(f"- {error}")

    raise SystemExit(1)

print("B3-002 line-ending contract: PASS")
print("policy: * text=auto eol=lf")
print("representative tracked text files have LF index state")

if args.require_worktree_lf:
    print("representative working-tree files are LF")
else:
    print(
        "working-tree LF was not required in this checkout; "
        "use --require-worktree-lf for fresh-checkout proof"
    )

autocrlf = subprocess.run(
    ("git", "config", "--get", "core.autocrlf"),
    cwd=ROOT,
    text=True,
    stdout=subprocess.PIPE,
).stdout.strip()

print(f"observed core.autocrlf: {autocrlf or '<unset>'}")