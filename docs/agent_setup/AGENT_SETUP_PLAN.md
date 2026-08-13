# Agent Setup Plan After Baseline Freeze

This is the recommended order after `sssf-local-b0` exists.

## Increment B1 — agent documentation discovery

Make every orchestrator entrypoint explicitly read:

1. `docs/README.md`
2. `docs/baseline/BASELINE.md`
3. only the task-relevant docs after that

Do not load the whole documentation tree into every context.

Targets to evaluate:

- `.claude/commands/prime.md`
- `.claude/skills/sssf/SKILL.md`
- `.claude/skills/sssf-sandbox-orchestrator/SKILL.md`
- future `AGENTS.md` for non-Claude harnesses

Acceptance:

a fresh orchestrator can answer:
- what is the current baseline?
- what is unproven?
- what command surface owns each tier?
- how is a new increment accepted?

without chat history.

## Increment B2 — Browser Sol supervisory seam

Define a machine-readable escalation artifact, for example:

`docs/runtime/escalations/<id>.json`

Browser Sol receives architecture/uncertainty questions and returns a ruling that can be recorded, but local code remains execution authority.

## Increment B3 — Claude Code when quota is available

Use Claude Code primarily as:

- host/in-sandbox orchestrator,
- repository reader,
- operator of deterministic recipes.

Do not give it authority to bypass ADW gates or rewrite run evidence.

## Increment B4 — Pi role roster qualification

Maintain explicit fixtures for:

- planner
- builder
- scout
- reviewer
- documenter

A model can be assigned to a role only after passing that role's fixture.

## Current zero-cost starting point

The baseline proved North Mini Code free for:

- planner
- builder

Do not infer qualification for scout/reviewer/documenter from that result.

## Separation of duties

Where independent semantic review matters, use a distinct session and preferably a distinct model profile from the maker.

Deterministic tests/gates remain preferred whenever they can decide the claim exactly.
