from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CHECKS = {
    "AGENTS.md": ["docs/README.md", "docs/baseline/BASELINE.md", "docs/development/INCREMENT_PROTOCOL.md", "SOURCE_OF_TRUTH.md"],
    "CLAUDE.md": ["AGENTS.md", "/prime", "/sssf", "/sssf-sandbox-orchestrator"],
    ".claude/commands/prime.md": ["docs/README.md", "docs/baseline/BASELINE.md", "five namespaces", "just --list inkwell"],
    ".claude/skills/sssf/SKILL.md": ["docs/README.md", "docs/baseline/BASELINE.md", "roster-driven", "visualizer is present"],
    ".claude/skills/sssf-sandbox-orchestrator/SKILL.md": ["docs/README.md", "docs/baseline/BASELINE.md", "Local system record"],
    "docs/README.md": ["AGENTS.md", "CLAUDE.md", "baseline/BASELINE.md", "development/INCREMENT_PROTOCOL.md"],
    "docs/baseline/BASELINE.md": ["sssf-local-b0", "sssf-proof-b0", "5573998b"],
}

errors = []
for rel, required in CHECKS.items():
    path = ROOT / rel
    if not path.is_file():
        errors.append(f"missing: {rel}")
        continue
    text = path.read_text(encoding="utf-8")
    for needle in required:
        if needle not in text:
            errors.append(f"{rel}: missing required reference: {needle}")

prime = (ROOT / ".claude/commands/prime.md").read_text(encoding="utf-8")
if "the one phase not yet exercised" in prime:
    errors.append("prime.md still contains the stale teardown claim")

skill = (ROOT / ".claude/skills/sssf/SKILL.md").read_text(encoding="utf-8")
if "visualizer app ships in a later pass" in skill:
    errors.append("SSSF skill still contains the stale visualizer claim")

if errors:
    print("B1 agent bootstrap: FAIL")
    for error in errors:
        print(f"- {error}")
    raise SystemExit(1)

print("B1 agent bootstrap: PASS")
print(f"validated {len(CHECKS)} durable entrypoints/references")
