# ADR-0004 — SSSF Outer Authority and DSH Inner Autonomy

- **Status:** Accepted design direction; implementation sequenced, not active
- **Date:** 2026-08-18
- **Planning item:** FUT-001

## Context

SSSF is evolving from the Super Simple Software Factory / Factory-In-A-Box lineage. The current system deliberately separates host sandbox orchestration, the in-sandbox supervisory layer, and the deterministic software-factory runtime. Within the factory, code owns workflow authority and agents perform bounded semantic work.

DeepSeek Harness (DSH) is being considered as the future harness/runtime for increasingly capable agent execution. A migration that makes SSSF deterministically schedule every model turn would unnecessarily limit DSH's scaling features. A migration that lets DSH own the outer SSSF graph, source custody, acceptance, or promotion would violate existing SSSF authority boundaries.

DSH internally uses Cordis today. SSSF does not need or want a second architectural dependency on Cordis concepts.

## Decision

### 1. SSSF owns outer authority

SSSF code remains authoritative for:

- the outer work graph and legal transitions;
- execution-domain creation and identity;
- source SHA and workspace custody;
- eligible role/model/backend policy;
- resource, time, token, and cost ceilings;
- permitted external effects;
- maker/checker independence requirements;
- outer attempt creation and retry decisions;
- deterministic verification;
- acceptance;
- Git commit, harvest, promotion, landing, and deployment authority;
- terminal workflow state.

### 2. DSH may own substantial bounded inner autonomy

SSSF authorizes a bounded execution domain and expects a typed result plus attributable evidence. Inside that domain, DSH may progressively qualify authority over internal cognition and coordination, including:

- model-turn sequencing;
- internal planning and decomposition;
- autonomous subagents;
- parallel subagents;
- bounded refinement and Ralph-style loops;
- DSH workflows and `tool-workflow`;
- goal-driven inner execution;
- tool choice within the admitted capability set;
- compaction;
- MCP, LSP, and code mode;
- long-running/multi-turn workers where justified;
- product subagents;
- adaptive inner orchestration;
- eventually governed self-evolving agent behavior.

Internal DSH retries, iterations, workflow nodes, and child agents remain descendants of one SSSF-owned outer attempt unless SSSF explicitly creates another outer attempt.

### 3. Use an execution-cell boundary

The mature target abstraction is a bounded DSH **execution cell**, not SSSF micromanagement of individual model turns.

Example authorization:

```text
Builder attempt A may use:
- up to 6 DSH subagents
- up to 8 refinement rounds
- 30 minutes wall time
- an explicit tool/capability allowlist
- one exact source SHA and sandbox/workspace
- fixed token/cost ceilings
- an explicit external-effect policy

Return the required typed result and attributable evidence.
```

SSSF verifies the returned work independently and decides whether the outer graph advances.

### 4. Cordis stays encapsulated inside DSH

SSSF must not separately import, expose, or build its public architecture around Cordis fibers, reactive provider lifecycle, HMR, rollback semantics, or Cordis-owned orchestration merely because DSH uses Cordis internally.

The SSSF/DSH boundary must be stable enough that if a future DSH version replaces Cordis, SSSF's public work graph, evidence model, authority model, and execution-cell protocol do not need architectural redesign.

Direct Cordis adoption requires a separate measured problem and evidence that the required value cannot reasonably be obtained through DSH itself.

## Feature admission test

A DSH autonomous feature may be promoted when all applicable answers are mechanically satisfactory:

1. Can its authority be strictly scoped to one SSSF-owned execution domain?
2. Can resource, time, token, and cost limits be fixed and enforced externally?
3. Can all children and relevant evidence be attributed to the domain?
4. Can SSSF force termination and prove quiescence?
5. Can the feature be prevented from committing, promoting, changing outer retry state, or advancing the SSSF graph?
6. Does its output still pass through SSSF-owned deterministic gates and acceptance?

The existence of an internal loop, goal, workflow, or subagent mechanism is not itself a rejection criterion.

## Consequences

### Positive

- preserves the constitutional SSSF authority boundary;
- avoids turning SSSF into a model-turn scheduler;
- permits DSH to exploit autonomy and parallelism where evidence supports it;
- keeps source custody, acceptance, and promotion deterministic and external;
- prevents SSSF from coupling to Cordis implementation details;
- supports progressive qualification from simple cells to complex autonomous cells.

### Costs and obligations

- execution-cell budgets and lineage must become first-class evidence;
- hierarchical child/session/process accounting is required before broad subagent autonomy;
- hard cancellation and quiescence proofs become more important as autonomy increases;
- product subagents and auxiliary model calls may introduce separate transcript/evidence authorities that must be reconciled;
- each higher-level DSH capability needs independent qualification and negative controls.

## Sequencing

Production DSH adoption remains downstream of the existing SSSF execution/isolation proofs, including the Docker Sandbox substrate, Claude/Codex/DeepSeek backend qualification, deterministic real-PR landing/merge, and lifecycle/evidence contracts.

See `docs/development/ROADMAP.md` for the long-range sequence and `docs/development/FUTURE_CANDIDATES.md` for planning state.

## Non-goals

This ADR does not:

- activate DSH implementation work;
- choose a specific DSH version or configuration;
- approve any plugin or product subagent;
- grant DSH outer Git or promotion authority;
- make Cordis part of SSSF architecture;
- weaken existing test, evidence, review, source-custody, or certification requirements.
