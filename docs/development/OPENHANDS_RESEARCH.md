# OpenHands Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **OpenHands: An Open Platform for AI Software Developers as Generalist Agents**
- arXiv: `2407.16741`

The paper is a research/architecture source, not an OpenHands adoption decision.

## Governing interpretation

The strongest SSSF lesson is to stabilize and qualify the machinery around uncertain agent cognition: typed actions/observations, isolated runtime execution, durable attributable events, explicit delegation, and harness tests. SSSF retains stronger outer authority, source custody, acceptance, capability admission, and security semantics than the paper's generalist platform.

## EXPLORE-1 — Typed Action / Observation inner protocol

Inside one admitted execution cell, agent cognition should interact with CODE through typed action/observation units:

```text
model / inner policy
      ↓
typed Action
      ↓
CODE validates authority/budget/state and dispatches
      ↓
typed Observation
      ↓
model / inner policy
```

The `Action` is a request, not authority. Dispatch remains subject to capability policy, budget, effect/network policy, stale-state protection, and exact execution identity.

`ExecutionCellRequest/Result` remain the outer DSH boundary; Action/Observation is an inner protocol.

Routing: FUT-001, DSH-1/3/5.

## EXPLORE-2 — Event history is evidence, not outer workflow authority

Actions, observations, child results, mutations and other execution facts may be emitted as immutable/append-only attributable events for audit, replay and projections.

Event existence does not itself advance SSSF workflow state. Canonical source/work/increment/verification/ruling/landing owners remain authoritative.

Preserve the distinction:

```text
execution fact
    ≠
model-visible projection
    ≠
semantic interpretation
```

Routing: shared trace/evidence spine, replay corpus, FUT-008 analytics.

## EXPLORE-3 — Deterministic agent-harness conformance tests

Agent infrastructure is software and should have deterministic integration/conformance tests using model fixtures/mocks where possible.

Examples:

- action serialization/deserialization;
- tool schema and observation formatting;
- wrong/stale generation rejection;
- timeout/cancellation mapping;
- child-lineage preservation;
- event/evidence emission;
- sandbox dispatch/result transport;
- context-projection behavior.

Mocked-model PASS proves harness mechanics, not real-model capability. Real model seam qualification, replay/regression and fresh-frontier evaluation remain separate higher layers.

Potential hierarchy:

```text
A deterministic unit/protocol tests
B deterministic harness conformance with model fixtures
C real-model seam qualification
D historical replay/regression
E fresh-frontier/generalization
```

Routing: DSH qualification, harness scorecard, AgentBackend/ACI qualification.

## EXPLORE-4 — Typed delegation requests under CODE-owned policy

Delegation should be an explicit attributable action/request, for example binding parent identity, requested role, objective and authority subset.

CODE admits or denies delegation based on:

- allowed structural edge;
- child role/profile qualification;
- maximum depth/child count;
- remaining aggregate budget;
- equal-or-narrower authority;
- required workspace/reviewer isolation;
- effect/network policy.

Child results are evidence/data with provenance/trust/authority classification. They do not grant the parent additional authority.

Routing: DSH-3 and DSH-6.

## EXPLORE-5 — Harness correctness and agent capability are different qualification layers

Separate failures in deterministic transport/runtime machinery from failures of semantic agent capability.

**Harness correctness** includes protocol, serialization, stale-state guards, process lifecycle, tool dispatch, lineage, event/evidence production and sandbox behavior.

**Agent capability** includes localization, semantic implementation, strategy selection, research and other uncertain reasoning.

Do not spend real-model benchmark budget to diagnose failures that deterministic conformance tests can establish cheaply.

## Additional supporting observations

- Runtime mechanics remain separate from agent reasoning; this reinforces `AgentBackend` versus `SandboxProvider`.
- Prefer qualified semantic tools for routine work, with shell/general code as bounded fallback rather than the only interface.
- Maintain a capability catalog separately from private per-cell capability admission; availability is not authority.
- Stable semantic capability contracts may support specialized worker profiles rather than one universal generalist profile.
- Human trace inspection may support progressive disclosure, but Captain authority must travel through explicit durable decision contracts rather than UI/event-stream implication.
- Agent-generated/adaptive inner workflows belong inside bounded DSH cells and do not become SSSF outer workflow authority.

## Non-decisions

This research does **not** authorize:

- adopting/installing OpenHands as the SSSF/DSH runtime;
- making an event stream the SSSF source of truth;
- exposing the canonical host checkout to workers;
- granting all catalog capabilities to all agents;
- model-owned security/permission decisions;
- opaque/unbounded delegation;
- automatic DSH activation or roadmap reordering.
