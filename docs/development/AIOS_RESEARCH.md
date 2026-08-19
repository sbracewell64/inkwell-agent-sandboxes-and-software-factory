# AIOS Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **AIOS: LLM Agent Operating System**
- arXiv: `2403.16971`

The paper is a runtime/resource-management research source, not an authorization to adopt AIOS or insert an agent operating system between SSSF and Docker.

## Governing interpretation

AIOS identifies several legitimate deterministic runtime services for multi-agent systems, but SSSF should extract only those services that have a clear owner and consumer.

> **Borrow the operating-systems discipline, not the operating system. Resource arbitration may live underneath DSH; source custody, engineering workflow, authority, retry, review, promotion, and acceptance remain SSSF-owned.**

## EXPLORE-1 — Separate resource scheduling from engineering workflow sequencing

Distinguish two nested schedulers:

- SSSF/WorkNode scheduling: decides which engineering work is ready based on dependency, authority, and acceptance state;
- DSH runtime resource scheduling: arbitrates already-admitted LLM/tool/runtime requests under capacity/fairness limits.

A resource scheduler must never decide engineering phase progression, retries, review requirements, promotion, or acceptance.

Routing: `FUT-001`, DSH runtime services, SBX-7.

## EXPLORE-2 — Typed runtime requests and responses

Semantic workers should request admitted runtime capabilities through typed CODE-mediated calls rather than manipulating provider SDKs, tools, memory stores, or runtime state directly.

Potential request identity includes:

- `execution_cell_id` / `inner_unit_id`;
- capability identity;
- authority/effect policy;
- budget reference;
- runtime policy generation;
- request payload.

Responses should report resulting-state facts, output/effect refs, and resource usage rather than only an unstructured success message.

## EXPLORE-3 — Provider-neutral model backend, exact effective identity

A provider-neutral model/backend seam is useful, but qualification binds the complete behaviorally material execution generation rather than only model name.

Material identity may include model/backend, ACI/tool representation, context policy, compiled instruction generation, limits, scheduler/runtime policy, and other qualified configuration.

## EXPLORE-4 — CODE-owned resource admission, capacity, and fairness

Once semantic work is admitted, CODE may deterministically arbitrate scarce model/tool capacity, queue order, concurrency, and fairness.

Resource scheduling policy becomes qualification-relevant only when it materially changes cost, latency, fairness, or execution outcome.

## EXPLORE-5 — Inference suspension/resumption is a backend capability

Suspending and resuming model inference is an implementation/backend capability, not durable workflow state.

Any claim of equivalent resumed inference requires backend-specific qualification. Where equivalence cannot be proven, cancellation followed by a fresh call is a new semantic execution with new identity/evidence.

## EXPLORE-6 — Durable history is distinct from active context/cache state

Runtime memory/cache residency may be optimized, but cache eviction never determines whether durable evidence/history exists or whether an item is semantically important.

Preferred ownership:

```text
durable typed history
        ↓
CODE-owned context budgeting/projection
        ↓
model-facing active context
```

Physical cache/storage policy remains below this semantic boundary.

## EXPLORE-7 — Runtime storage must not compete with source/evidence custody

AIOS-like runtime storage may provide scratch/cache support, but SSSF already has stronger authoritative owners:

- Git owns source truth;
- admitted Docker workspaces own working mutation state;
- proof/evidence records own durable qualification evidence.

Do not introduce a second file-versioning, rollback, or source-authority layer beneath DSH.

## EXPLORE-8 — Tool dispatch has separate capacity, effect, and authority checks

Do not collapse tool unavailability into one generic state.

CODE should distinguish at least:

- capacity conflict: provider/tool concurrency exhausted;
- effect/resource conflict: overlapping exclusive mutable state;
- authority conflict: the current cell/invocation is not permitted to use the capability/effect.

Typed distinctions support correct retry/backpressure and diagnostic evidence.

## EXPLORE-9 — Access mediation and least privilege are CODE-owned

Agent-to-resource and cross-unit access should be mediated. Prefer per-cell capability/effect authority over coarse ambient privilege groups.

A worker should receive only the capabilities, source visibility, mutation scope, network policy, and effect authority explicitly admitted for its ExecutionCell.

## EXPLORE-10 — No ambient shared agent memory by default

Cross-unit information should move through explicit, provenance-bearing typed results rather than shared conversational cognition or communal memory.

This preserves context control, replayability, and maker/checker independence.

## Additional supporting observations

- Consequential effects require pre-effect authority checks; generic user-confirmation prompts must not reintroduce the Captain into routine engineering.
- Owner-emitted query/response facts are preferable to reconstructing runtime activity from opaque agent conversation.
- Conventional OS techniques can improve agent-runtime efficiency without becoming the solver or workflow authority.
- AIOS throughput results are workload- and deployment-specific; do not add a scheduler layer until SSSF measurements demonstrate meaningful contention.

## Non-decisions

This research does **not** authorize:

- adoption of AIOS;
- an AIOS kernel/VM/storage layer in SSSF;
- replacement of Docker/SandboxProvider custody;
- AIOS storage as source truth;
- shared agent memory as a default collaboration mechanism;
- resource scheduler ownership of SSSF engineering sequencing;
- roadmap or FUT-state promotion.
