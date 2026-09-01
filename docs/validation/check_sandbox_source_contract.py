import os
from pathlib import Path
import re
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci_gate import COULD_NOT_OBSERVE_EXIT  # noqa: E402

CANONICAL = (
    "https://github.com/"
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
)

# Bound every child so a wedged git is a timed-out observation rather than a
# validator that never returns.
CHILD_TIMEOUT_SECONDS = float(os.environ.get("SSSF_CHILD_TIMEOUT_SECONDS", "30"))


class Unobservable(Exception):
    """A child tool could not run, so no predicate was observed."""


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ("git", *args),
            cwd=ROOT,
            text=True,
            timeout=CHILD_TIMEOUT_SECONDS,
        ).strip()
    except OSError as exc:
        raise Unobservable(f"tool unavailable: git: {exc}") from exc
    except subprocess.TimeoutExpired as exc:
        raise Unobservable(f"check timed out: git {' '.join(args)}") from exc


errors: list[str] = []

could_not_observe: list[str] = []

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

origin = ""
head = ""

try:
    origin = git("remote", "get-url", "origin")
    if origin.removesuffix(".git") != CANONICAL.removesuffix(".git"):
        errors.append(
            f"origin is {origin!r}, expected canonical repository"
        )

    head = git("rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        errors.append(f"HEAD is not an exact commit SHA: {head!r}")
except Unobservable as exc:
    could_not_observe.append(str(exc))

# An observed defect outranks a failure to observe; only a run that judged
# nothing reports could-not-observe. Neither is a pass.
if errors:
    print("B2-002 sandbox source contract: FAIL")
    for error in errors:
        print(f"- observed-bad: {error}")
    for reason in could_not_observe:
        print(f"- could-not-observe: {reason}")
    raise SystemExit(1)

if could_not_observe:
    print("B2-002 sandbox source contract: CNO")
    for reason in could_not_observe:
        print(f"- could-not-observe: {reason}")
    raise SystemExit(COULD_NOT_OBSERVE_EXIT)

print("B2-002 sandbox source contract: PASS")
print(f"canonical origin: {origin}")
print(f"current committed HEAD: {head}")
print("run record + FILL + SETUP provenance contract is present")
