from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

CANONICAL = (
    "https://github.com/"
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
)

UPSTREAM = (
    "https://github.com/"
    "disler/inkwell-agent-sandboxes-and-software-factory.git"
)

# Immutable historical refs. These must never move.
EXPECTED = {
    "upstream/main": "92f1701810993b8303562265ba04c727468fe070",
    "sssf-local-b0": "c54b7b9ae83802023a52c46f8e960567c1e946f0",
    "sssf-proof-b0": "042dfb9d34a14fe5952538fedddbd136b334947e",
    "sssf-b1-agent-doc-discovery": (
        "49342bd3851cb71a79c69b8438d2b5062836b08d"
    ),
    "sssf-b2-001-canonical-repository": (
        "e6fa1d125013daefce8cd5628052a86c2c463615"
    ),
}


def run(*args: str) -> str:
    return subprocess.check_output(
        args,
        cwd=ROOT,
        text=True,
    ).strip()


errors: list[str] = []

# Remote roles.
if run("git", "remote", "get-url", "origin") != CANONICAL:
    errors.append("origin is not the canonical repository")

if run("git", "remote", "get-url", "upstream") != UPSTREAM:
    errors.append("upstream fetch URL is incorrect")

if run("git", "remote", "get-url", "--push", "upstream") != "DISABLED":
    errors.append("upstream push URL is not disabled")

# Immutable proven history.
for ref, expected in EXPECTED.items():
    actual = run("git", "rev-list", "-n", "1", ref)
    if actual != expected:
        errors.append(
            f"{ref}: expected {expected}, got {actual}"
        )

# Canonical main is allowed to advance as later increments are accepted.
# It must agree locally/remotely and must never move behind proven B2-001.
local_main = run(
    "git",
    "rev-list",
    "-n",
    "1",
    "main",
)

origin_main = run(
    "git",
    "rev-list",
    "-n",
    "1",
    "origin/main",
)

if local_main != origin_main:
    errors.append(
        f"local main {local_main} != origin/main {origin_main}"
    )

remote_main_line = run(
    "git",
    "ls-remote",
    "origin",
    "refs/heads/main",
)

remote_main = (
    remote_main_line.split()[0]
    if remote_main_line
    else ""
)

if not remote_main:
    errors.append("origin has no refs/heads/main")
elif remote_main != origin_main:
    errors.append(
        f"remote main {remote_main} != local origin/main {origin_main}"
    )

ancestor = subprocess.run(
    (
        "git",
        "merge-base",
        "--is-ancestor",
        "sssf-b2-001-canonical-repository",
        "origin/main",
    ),
    cwd=ROOT,
).returncode

if ancestor != 0:
    errors.append(
        "origin/main does not descend from proven B2-001"
    )

# Local main must explicitly track canonical origin/main.
local_main_upstream = run(
    "git",
    "for-each-ref",
    "--format=%(upstream:short)",
    "refs/heads/main",
)

if local_main_upstream != "origin/main":
    errors.append(
        f"local main tracks {local_main_upstream!r}, "
        "expected 'origin/main'"
    )

# GitHub itself must expose main as the default branch.
default_branch = run(
    "gh",
    "repo",
    "view",
    "sbracewell64/inkwell-agent-sandboxes-and-software-factory",
    "--json",
    "defaultBranchRef",
    "--jq",
    ".defaultBranchRef.name",
)

if default_branch != "main":
    errors.append(
        f"GitHub default branch is {default_branch!r}, "
        "expected 'main'"
    )

if errors:
    print("B2-001 repository ownership: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("B2-001 repository ownership: PASS")
print("origin is canonical")
print("upstream is reference-only")
print("local main tracks canonical origin/main")
print("canonical main descends from proven B2-001")
print("all immutable proven refs resolve exactly")