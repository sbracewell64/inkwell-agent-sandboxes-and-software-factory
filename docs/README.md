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

## Future architecture planning

Future ideas do not become implementation work merely because they were discussed.

Use these records when the task concerns long-range design rather than current proven behavior:

- [`development/PLANNING_LIFECYCLE.md`](development/PLANNING_LIFECYCLE.md) — promotion states from `EXPLORE` through `PROVEN`.
- [`development/FUTURE_CANDIDATES.md`](development/FUTURE_CANDIDATES.md) — preserved/candidate/decided/sequenced/active future items.
- [`development/ROADMAP.md`](development/ROADMAP.md) — dependency sequencing for approved implementation intent.
- [`decisions/`](decisions/) — accepted architectural decisions.

FUT-003 adds a transport surface for planning promotions without changing planning authority:

- [`development/PLANNING_EVENTS.jsonl`](development/PLANNING_EVENTS.jsonl) — append-only typed notification index; never the planning source of truth.
- [`reference/PLANNING_EVENTS.md`](reference/PLANNING_EVENTS.md) — producer/consumer contract, bootstrap rule, actionability, and continuity semantics.
- [`increments/FP-001_PLANNING_EVENT_PRODUCER.md`](increments/FP-001_PLANNING_EVENT_PRODUCER.md) — bounded producer increment and acceptance criteria.
- [`validation/check_planning_events.py`](validation/check_planning_events.py) — deterministic producer validator and watched-red controls.

Planning state is not proof state. `PRESERVE`, `CANDIDATE`, `DECIDED`, and `SEQUENCED` records must not be read as claims about current executable behavior. `ACTIVE` authorizes bounded engineering under the increment protocol but is still not `PROVEN`.

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

Future-planning promotions update only the smallest applicable planning surface until the item becomes `ACTIVE` under the increment protocol.
