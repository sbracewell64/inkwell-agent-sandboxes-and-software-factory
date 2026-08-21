# SSSF Documentation

This directory is the durable, engineer- and agent-readable reference for the local SSSF installation.

## Purpose

SSSF is being developed in **proven increments**. A change is not part of the trusted system merely because code exists. It becomes trusted only when:

1. the intended change is recorded,
2. the implementation is bounded,
3. deterministic validation or an explicit gate proves the claim,
4. evidence is retained,
5. the documentation is updated,
6. the accepted state is frozen with an immutable Git reference.

## Agent bootstrap

Repository-level agents enter through `AGENTS.md`; Claude Code additionally receives `CLAUDE.md`. Both route here rather than duplicating the system record. This file is the documentation router: read the frozen baseline, then lazy-load only task-relevant references.

## Start here

Read in this order:

1. [`baseline/BASELINE.md`](baseline/BASELINE.md) — exactly what is proven now.
2. [`architecture/SYSTEM_OVERVIEW.md`](architecture/SYSTEM_OVERVIEW.md) — the three-tier system.
3. [`architecture/BOUNDARY_LAW.md`](architecture/BOUNDARY_LAW.md) — what code owns and what agents own.
4. [`operations/RUNBOOK.md`](operations/RUNBOOK.md) — how to operate it.
5. [`development/INCREMENT_PROTOCOL.md`](development/INCREMENT_PROTOCOL.md) — how to change it without losing provenance.
6. [`reference/COMMANDS.md`](reference/COMMANDS.md) — command surface.
7. [`reference/GLOSSARY.md`](reference/GLOSSARY.md) — canonical terms.
8. [`reference/EVIDENCE_MANIFEST.md`](reference/EVIDENCE_MANIFEST.md) — offline run-bound evidence manifest v1 (not runtime acceptance).
9. [`reference/SANDBOX_PROVIDER.md`](reference/SANDBOX_PROVIDER.md) — SBX-1 provider-neutral sandbox contract and owner boundary.
10. [`reference/SBX-0_SEMANTICS_INVENTORY.json`](reference/SBX-0_SEMANTICS_INVENTORY.json) — exact SBX-0 source-bound handoff inventory and classification-compatible owner-per-fact coverage.

## Future architecture planning

Future ideas do not become implementation work merely because they were
discussed. The canonical closed planning transition contract is
[`development/PLANNING_LIFECYCLE.md`](development/PLANNING_LIFECYCLE.md); the
durable current state and transition evidence is
[`development/PLANNING_STATE.json`](development/PLANNING_STATE.json). The
candidate register, roadmap, ADRs, and manifest point to that owner rather than
restating a competing lifecycle.

authoritative planning source: planning/future-sssf; commit: d75103fb7ef8dd4ca40f62d40fc7479369bbdf0b; tree: e29628eb5754a032dce989166f287b82d5c877dc; generation: planning/future-sssf@d75103fb7ef8dd4ca40f62d40fc7479369bbdf0b:e29628eb5754a032dce989166f287b82d5c877dc

`ACTIVE` is engineering authorization only. `ACTIVE` is intake eligibility
only. `ACTIVE` is never task creation. `ACTIVE` is never execution authority.
`ACTIVE` is never landing authority. `ACTIVE` is never PRE_CERTIFICATION exit.
`ACTIVE` is never acceptance. `ACTIVE` is never certification. `ACTIVE` is
never live enablement. `ACTIVE` is never PROVEN. PROVEN is proof state requiring
accepted implementation, retained evidence, documentation, and immutable source
identity. No planning record is
runtime authority; an ADR, manifest, roadmap row, or validation result is not
runtime, landing, acceptance, certification, or live-enable authority.

The authoritative planning generation records FUT-001/DSH as `SEQUENCED`,
FUT-003 as `ACTIVE` but not `PROVEN`, and SBX-2 as `HELD`. The machine-readable
projection also retains FUT-004..013, the named LAUNCH/SBX/Wayfinder/DSH
identities, and BOUND-1 as `SEQUENCED`; BOUND-1 must complete and qualify before
SBX-2 can leave `HELD`. The exact source identity/generation is observed from
`refs/remotes/origin/planning/future-sssf` and bound in `PLANNING_STATE.json`.
This planning state is never task creation, execution, landing, acceptance,
certification, live enablement, or runtime authority, and it cannot answer
SBX-2 readiness.

## Documentation authority

When sources disagree, use this precedence:

1. executable code and deterministic tests,
2. captured run evidence and immutable Git objects,
3. current configuration,
4. these `docs/` references,
5. README/TREE/skills and generated narrative artifacts.

A document must not silently overrule code. If a mismatch is found, record it as an increment or defect.

## Existing repository documentation

These remain important and are not replaced:

- `README.md` — public overview and end-to-end usage.
- `TREE.md` — file-by-file map.
- `.claude/skills/sssf/` — portable factory skill, cookbooks, and references.
- `.claude/skills/sssf-sandbox-orchestrator/` — host sandbox recipes and measured gotchas.
- `ai_docs/` — measured technical notes.
- `specs/` — plans produced by factory runs.
- `app_docs/` — application documentation produced by factory runs.

The root `docs/` tree is the **long-lived system record** for this local SSSF evolution.

## Required update rule

Every accepted increment must update at least:

- `baseline/INCREMENT_LEDGER.md`
- the affected architecture/operations/reference document
- `baseline/PROOF_MATRIX.md` when a new claim is proven
- an ADR when an architectural choice changes
