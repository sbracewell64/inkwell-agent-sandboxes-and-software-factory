from pathlib import Path
import re
import runpy
import subprocess

ROOT = Path(__file__).resolve().parents[2]

CANONICAL = (
    "https://github.com/"
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
)


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(
        ("git", *args),
        cwd=ROOT,
        text=True,
    ).strip()


errors: list[str] = []

record = runpy.run_path(
    str(ROOT / "sandbox_mount/host/run_record.py")
)
fields = record["FIELDS"]

for field in ("source_repo", "source_sha", "commit_sha"):
    if field not in fields:
        errors.append(f"run record missing {field}")

fill = read("just/sandbox/lifecycle/fill.just")

if (
    "https://github.com/disler/"
    "inkwell-agent-sandboxes-and-software-factory.git"
    in fill
):
    errors.append("fill.just still hard-codes Disler clone authority")

for required in (
    "git remote get-url origin",
    "https://github.com/*",
    "git status --porcelain",
    "git rev-parse HEAD",
    'source_repo="$REPO"',
    'source_sha="$PIN"',
    'commit_sha="$HEAD_SHA"',
):
    if required not in fill:
        errors.append(f"fill.just missing contract element: {required}")

setup = read("just/sandbox/lifecycle/setup.just")

for required in (
    'get {{RUN_ID}} source_repo',
    'get {{RUN_ID}} source_sha',
    '"$SOURCE_SHA" = "$SHA"',
    "git remote get-url origin",
    "origin does not match recorded source_repo",
):
    if required not in setup:
        errors.append(f"setup.just missing provenance gate: {required}")

origin = git("remote", "get-url", "origin")
if origin.removesuffix(".git") != CANONICAL.removesuffix(".git"):
    errors.append(
        f"origin is {origin!r}, expected canonical repository"
    )

head = git("rev-parse", "HEAD")
if not re.fullmatch(r"[0-9a-f]{40}", head):
    errors.append(f"HEAD is not an exact commit SHA: {head!r}")

if errors:
    print("B2-002 sandbox source contract: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("B2-002 sandbox source contract: PASS")
print(f"canonical origin: {origin}")
print(f"current committed HEAD: {head}")
print("run record + FILL + SETUP provenance contract is present")
