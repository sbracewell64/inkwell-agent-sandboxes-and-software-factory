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

EXPECTED = {
    "upstream/main": "92f1701810993b8303562265ba04c727468fe070",
    "origin/main": "49342bd3851cb71a79c69b8438d2b5062836b08d",
    "sssf-local-b0": "c54b7b9ae83802023a52c46f8e960567c1e946f0",
    "sssf-proof-b0": "042dfb9d34a14fe5952538fedddbd136b334947e",
    "sssf-b1-agent-doc-discovery": (
        "49342bd3851cb71a79c69b8438d2b5062836b08d"
    ),
}


def run(*args: str) -> str:
    return subprocess.check_output(
        args,
        cwd=ROOT,
        text=True,
    ).strip()


errors: list[str] = []

if run("git", "remote", "get-url", "origin") != CANONICAL:
    errors.append("origin is not the canonical repository")

if run("git", "remote", "get-url", "upstream") != UPSTREAM:
    errors.append("upstream fetch URL is incorrect")

if run("git", "remote", "get-url", "--push", "upstream") != "DISABLED":
    errors.append("upstream push URL is not disabled")

for ref, expected in EXPECTED.items():
    actual = run("git", "rev-list", "-n", "1", ref)
    if actual != expected:
        errors.append(
            f"{ref}: expected {expected}, got {actual}"
        )

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
        f"GitHub default branch is {default_branch!r}, expected 'main'"
    )

local_main_upstream = run(
    "git",
    "for-each-ref",
    "--format=%(upstream:short)",
    "refs/heads/main",
)

if local_main_upstream != "origin/main":
    errors.append(
        f"local main tracks {local_main_upstream!r}, expected 'origin/main'"
    )

if errors:
    print("B2-001 repository ownership: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("B2-001 repository ownership: PASS")
print("origin is canonical")
print("upstream is reference-only")
print("main tracks origin/main")
print("all previously proven refs resolve exactly")