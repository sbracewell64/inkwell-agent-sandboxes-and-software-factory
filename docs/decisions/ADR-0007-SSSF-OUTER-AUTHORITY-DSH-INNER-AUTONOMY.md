# ADR-0007 — SSSF Outer Authority and DSH Inner Autonomy

authoritative planning source: planning/future-sssf; commit: eab880656b4ef00174ea514cca128f6336632fcf; tree: 5328b8a437d894682f4ac1c5d7ae581694410c43; generation: planning/future-sssf@eab880656b4ef00174ea514cca128f6336632fcf:5328b8a437d894682f4ac1c5d7ae581694410c43

- **Status:** Accepted design direction; implementation sequenced, not active
- **Date:** 2026-08-20
- **Planning item:** FUT-001
- **Lifecycle owner:** [`PLANNING_LIFECYCLE.md`](../development/PLANNING_LIFECYCLE.md)
- **Current state record:** [`PLANNING_STATE.json`](../development/PLANNING_STATE.json)
- **Authoritative planning source:** `planning/future-sssf@eab880656b4ef00174ea514cca128f6336632fcf:5328b8a437d894682f4ac1c5d7ae581694410c43`

## Identity allocation

The current-main ADR identity inventory was examined at
`991d3a64f1b96a8b9637f97060d692af3518228f`. It already owns Windows front-door
ADR-0004 and SandboxProvider ADR-0006. Existing historical ADR-0003 filename
collisions are outside this increment's scope and are not renumbered.

ADR-0007 is the next unique identity for this DSH decision. The current-main
ADR-0004 and ADR-0006 files are preserved byte-for-byte; this successor does
not reuse either identity.

## Context

SSSF may eventually use DeepSeek Harness (DSH) for increasingly capable inner
agent execution. The outer SSSF graph, source custody, acceptance, promotion,
and terminal state must remain deterministic and externally governed. DSH
internals must not become a second SSSF architecture merely because DSH uses
Cordis internally.

## Decision

### 1. SSSF owns outer authority

SSSF remains authoritative for:

- the outer work graph and legal transitions;
- execution-domain creation and identity;
- exact source and workspace custody;
- eligible role/model/backend policy;
- resource, time, token, and cost ceilings;
- permitted external effects;
- maker/checker independence requirements;
- outer attempts and retry decisions;
- deterministic verification and acceptance;
- Git commit, harvest, promotion, landing, and deployment authority; and
- terminal workflow state.

### 2. DSH may qualify bounded inner autonomy later

Inside one SSSF-owned execution domain, a separately qualified DSH may
eventually provide bounded multi-turn reasoning, refinement, subagents, inner
workflows, or adaptive coordination. Internal retries, iterations, and child
agents remain descendants of one SSSF-owned outer attempt unless SSSF creates
another outer attempt.

An inner feature cannot commit, promote, change the SSSF graph, alter outer
retry state, or own acceptance merely because it is capable of doing so.

### 3. Use an execution-cell boundary

The future target is a bounded execution cell with an exact source identity,
fixed resource/time/token/cost ceilings, explicit tools and external-effect
policy, forceable termination, attributable evidence, and a typed result.
SSSF independently verifies the result and decides whether its outer graph may
advance.

### 4. Cordis stays encapsulated inside DSH

SSSF must not separately import, expose, or build its public architecture
around Cordis implementation details. A future DSH replacement of Cordis must
not require redesign of SSSF's public graph, evidence, or authority model.

## Feature admission test

A future DSH capability may be considered only when it can be scoped to one
SSSF execution domain, externally budgeted, attributed, force-terminated,
quiesced, and passed through SSSF-owned deterministic verification and
acceptance without outer-graph or promotion authority.

## Sequencing and boundary

FUT-001 is `SEQUENCED`, not `ACTIVE`, under the authoritative planning
source/generation. Production DSH adoption remains downstream
of the existing SSSF execution/isolation, backend, source-custody,
lifecycle/evidence, termination, quiescence, and acceptance proofs. This ADR
does not authorize DSH implementation, a provider, Docker, Wayfinder, or live
execution.

## Non-goals

This ADR does not:

- activate DSH implementation work;
- choose a DSH version or configuration;
- approve a plugin or product subagent;
- grant DSH outer Git, acceptance, landing, or promotion authority;
- make Cordis part of SSSF architecture; or
- weaken source custody, evidence, review, test, certification, or acceptance
  requirements.
