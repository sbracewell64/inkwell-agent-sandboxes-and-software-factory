# Semi-Executable Stack Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **The Semi-Executable Stack: Agentic Software Engineering and the Expanding Scope of SE**
- arXiv: `2604.15468`

The paper is a conceptual/reference source, not an authorization to adopt a six-ring runtime model, document hierarchy, or governance subsystem.

## Governing interpretation

Consequential prompts, policies, context rules, workflow/search rules, evaluation logic, escalation rules, and other semi-executable inputs are engineering material when they materially alter behavior.

SSSF should not respond by creating more layers. The preferred direction is:

> **Preserve durable principles → Purify away obsolete ceremony → push stable/checkable behavior CODEward.**

## EXPLORE-1 — Preserve / Purify / CODEward

For every consequential process, instruction, or control:

1. **Preserve:** identify the real invariant/value it protects;
2. **Purify:** remove coordination ceremony or artifact structure that exists only because of obsolete manual/human constraints;
3. **CODEward:** move any now-stable/checkable surviving behavior into deterministic code, validators, typed state, or policy where it can be owned honestly.

Example:

```text
"Agent should avoid writing outside scope"
        ↓ preserve invariant
scope discipline
        ↓ purify prose ceremony
        ↓ CODEward
expected-write enforcement
```

Routing: `FUT-010`, Boundary Law work, general SSSF simplification discipline.

## EXPLORE-2 — Semi-executable behavior contributes to effective runtime identity

A behaviorally material execution identity is not only source code or package version.

Where applicable, effective runtime identity should bind the exact generations/digests of:

- prompts/instructions/protocols;
- context/projection policy;
- capability/tool registry;
- workflow/search policy;
- verifier/selection policy;
- effect/network/security policy;
- backend/model profile;
- dependency/runtime composition.

Changing one of these materially may require requalification even if the underlying model or source package is unchanged.

Routing: `FUT-001`, DSH effective-runtime generation, replay/qualification evidence.

## EXPLORE-3 — Behavioral qualification for instructional artifacts

Schema/syntax validity does not establish that a prompt, policy, workflow description, or other semi-executable instruction behaves as intended.

Where an artifact claims to influence agent behavior, qualification should progress as appropriate through:

```text
STRUCTURE
    ↓
APPLICABILITY / ROUTING
    ↓
BEHAVIORAL WATCHED-RED / FALSIFIABILITY
    ↓
COLLISION / INTERACTION
    ↓
PRODUCTION ELIGIBILITY
```

Mechanically enforceable parts should move into CODE instead of remaining prose requirements.

Routing: `FUT-011`.

## EXPLORE-4 — Explicit retirement / mechanization path

Instruction governance must not become an ever-growing prompt museum.

Periodically ask of each durable semantic rule:

```text
What behavior here has become deterministic?
```

Stable/checkable behavior should be:

- extracted;
- mechanized;
- tested;
- removed from semantic instruction where possible.

Retirement/supersession should preserve provenance while reducing active context and semantic burden.

Routing: `FUT-011`, `FUT-012`.

## EXPLORE-5 — Capability, system value, and operator value are distinct

Evaluation should separate at least:

- **inner capability:** localization/refinement/verifier/tool performance;
- **system engineering:** deterministic acceptance, latency, cost, retries, failure classes, reviewer burden;
- **operator value:** time-to-value, avoidable escalations, Captain interventions, decision burden.

A local agent benchmark gain does not prove the engineering system or operator experience improved.

A particularly important long-range SSSF metric is avoidable Captain interventions per accepted increment, separated from legitimate reserved-authority interventions.

Routing: harness scorecard / future system-generation evaluation.

## EXPLORE-6 — Purify ceremony; preserve authority/evidence boundaries

Not every phase/process boundary is legacy ceremony.

Preserve boundaries that protect:

- source/credential custody;
- maker/checker independence;
- mutation authority;
- evidence eligibility;
- irreversible effects;
- promotion/landing authority.

Purify boundaries that exist only for traditional human handoff/coordination overhead and provide no material authority, evidence, or uncertainty-reduction value.

DSH inner workflows may be fluid while SSSF outer authority remains explicit.

Routing: `FUT-010`, `ADR-0004`, DSH stage design.

## Additional supporting observations

- Important engineered interfaces such as FirstMate and Wayfinder do not become state authorities merely because they materially affect behavior.
- Owner-emitted typed facts are preferable to a monitoring/reconstruction layer for control-system observability.
- Traceability should bind behaviorally material prompt/context/policy/workflow generations to exact executions without requiring a proliferating artifact hierarchy.
- Expanded participation in system behavior does not flatten authority: contribution, semantic judgment, deterministic transition authority, and Captain-reserved authority remain distinct.
- Regulatory/institutional concerns should enter SSSF as concrete requirements when real, not as a generic governance subsystem without a consumer.

## Non-decisions

This research does **not** authorize:

- a six-ring SSSF runtime architecture;
- new registries/subsystems for every prompt/policy/workflow artifact class;
- weakening SSSF outer phase/authority boundaries;
- turning dashboards/monitors into execution truth;
- promoting FUT-010/011/012 state;
- changing the Docker-first / Wayfinder / DSH roadmap order.
