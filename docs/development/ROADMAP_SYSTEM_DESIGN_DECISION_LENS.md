# Roadmap Amendment — System Design Decision Lens for SSSF

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Purpose:** make system-design knowledge a standing decision methodology for SSSF maturation so FirstMate uses architecture mechanisms only when they solve an observed problem and their added complexity is justified by evidence.

This amendment does not authorize a queue, cache, load balancer, replication layer, sharding scheme, scheduler, database, daemon, or other distributed-systems mechanism merely because the concept is useful to study. System-design concepts are decision lenses, not implementation goals.

## Governing principle

For every material architecture proposal, FirstMate should answer three questions before recommending adoption:

1. **What exact problem does this mechanism solve?**
2. **What evidence says SSSF needs it now?**
3. **What new complexity, state, failure modes, ownership, reconciliation, and operator concepts does it introduce?**

If the existing architecture already satisfies the need, or the measured benefit does not justify the new failure surface, prefer `DEFER` or `REJECT`.

The roadmap should reward knowing when **not** to use a system-design mechanism.

## SSSF-specific learning order

FirstMate should apply system-design reasoning in approximately this order:

1. **End-to-end task lifecycle** — Captain intent -> FirstMate supervision -> workflow selection -> Python ADW -> bounded AGENT/CODE phases -> verification -> review -> landing -> exact-main/post-effect proof.
2. **Ownership and typed machine seams** — explicit producer/consumer contracts, identities, normalization, applicability and fail-closed behavior.
3. **Durable state and source-of-truth rules** — distinguish authoritative state, durable evidence, caches, projections and transient runtime state.
4. **Queues and asynchronous work** — durable enqueue/receipt/ownership, dependency-cone blocking, restart/recovery and duplicate suppression.
5. **Retries, idempotency and exactly-once-effect semantics** — bounded attempts, duplicate delivery, one-use authority, effect identity, crash/replay handling.
6. **Concurrency, locks and backpressure** — worker/sandbox limits, write/resource conflicts, deterministic fan-out/join, capacity exhaustion and quiescence.
7. **Caching and freshness** — cache may accelerate reads but never outrank current authoritative state; all authority-relevant cache use needs bounded freshness/revalidation.
8. **Failure recovery and reconciliation** — restart from durable identities, partial completion, stale state, cleanup uncertainty, recovery ownership.
9. **Observability, provenance and lineage** — reconstruct what acted, what it knew, what it could do, what it did, why the result is believed, and how much it cost.
10. **Advanced distribution only on demonstrated need** — replication, partitioning/sharding, complex load balancing or additional distributed state require measured scale/contention/failure evidence before admission.

## Conventional system-design concepts mapped to SSSF

| Concept | SSSF interpretation | Default posture |
|---|---|---|
| End-to-end request | Captain -> FirstMate -> SSSF -> ADW -> agents/CODE -> verification/review/landing | understand completely |
| APIs / databases | typed seams/contracts; JSONL durable history + SQLite query projection | extend current owners |
| Caching | context/history/provider/config caches | useful only with explicit freshness; never authority |
| Load balancing | qualified worker/model/sandbox admission and capacity routing | deterministic admission before generic balancing |
| Queues / async | backlog, Browser Sol queue, CI/watchers, future parallel work | important; require durable identity/recovery |
| Replication / sharding | worktrees, parallel workers, project partitioning | defer until actual need |
| Rate limiting | worker caps, quotas, token/cost/resource ceilings | explicit backpressure/refusal |
| Retries / idempotency | attempts, duplicate suppression, exact-head/effect identity, one-use authority | highest-priority correctness area |
| Observability | JSONL/SQLite, lineage, REF-1, Praxist, proof records | mandatory for autonomous maturation |

## Required system-design assessment

For a material roadmap proposal, FirstMate should produce or incorporate a concise assessment with semantics equivalent to:

```text
SYSTEM_DESIGN_ASSESSMENT

Problem:
  What observable limitation exists?

Current owner:
  What currently handles this property?

Trigger/evidence:
  Why is the current design insufficient now?

Candidate mechanism:
  Queue / cache / retry / parallelism / backpressure / etc.

Added complexity:
  - new durable/transient state
  - new lifecycle transitions
  - new failure modes
  - new authority/security/cost surface
  - new reconciliation/recovery paths
  - new operator concepts

Failure behavior:
  duplicate / timeout / crash / restart / stale state / partial effect /
  unavailable dependency / capacity exhaustion / conflicting concurrency /
  unavailable evidence, as applicable

Simpler alternative:
  Can an existing type, function, validator, ADW, owner, trace projection,
  or deterministic policy satisfy the requirement?

Measurement:
  How will exact tests plus REF-1/Praxist/direct metrics establish value?

Disposition:
  ADOPT | DEFER | REJECT | CNO
```

Do not create a separate bureaucracy or state machine for this template. It may be embedded in existing roadmap/increment/architecture reports where that is simpler.

## Failure-first design law

For any stateful or asynchronous mechanism, FirstMate should evaluate the failure path before treating the happy path as sufficient.

Questions to consider where applicable:

- What if the request/event/task is delivered twice?
- What if the worker dies before effect?
- What if it dies after effect but before acknowledgement/publication?
- What if the acknowledgement/result is lost?
- What if cached/history state is stale?
- What if the supervisor restarts?
- What if the consumer observes a different generation than the producer intended?
- What if multiple workers contend for the same write/resource surface?
- What if capacity, quota or external dependency is unavailable?
- What if cleanup/recovery cannot be observed?
- Can the exact state be reconstructed after restart without transcript inference?

The goal is not theoretical completeness. Apply only fault classes relevant to the subsystem.

## Common deterministic fault vocabulary

Use this as a reusable qualification vocabulary where applicable:

```text
normal execution
duplicate delivery
timeout before effect
timeout after effect
worker crash
supervisor crash
restart
stale state
wrong identity
partial completion
capacity exhaustion
concurrent conflicting work
dependency unavailable
evidence unavailable
```

Each subsystem maps only the applicable faults to positive/watched-red fixtures. Examples:

- queue -> duplicate delivery, restart, lost acknowledgement;
- cache -> stale state, wrong generation, source conflict;
- parallel ADW -> conflicting writes, branch failure, cancellation/quiescence, capacity exhaustion;
- landing authority -> replay, stale head, one-use consumption, crash around commit point;
- provider/model routing -> capacity/price/identity freshness and lawful fallback;
- observability -> missing/partial evidence must remain CNO rather than false PASS/zero.

## Evidence-backed architecture adoption

Architecture is not credited because it is conventional or elegant.

Preferred maturation loop:

```text
START SIMPLE
    |
    v
observe concrete limitation
    |
    v
identify system-design problem class
    |
    v
choose smallest mechanism preserving existing owners
    |
    v
fault-test positive + watched-red behavior
    |
    v
measure with REF-1 / Praxist / direct metrics where material
    |
    +-- value proven -> retain
    |
    +-- value mixed -> revise / narrow applicability
    |
    +-- value unproven or negative -> remove / defer / reject
```

The burden is especially high for mechanisms that introduce another durable state owner, database, daemon, scheduler, cache authority, distributed lock service, replicated store, or generic orchestration layer.

## Relationship to REF-1 and Praxist

When a significant SSSF advancement is justified partly by a system-design mechanism, the existing REF-1/Praxist maturation policy should test the claimed value where the reference workload is applicable.

Examples:

- caching -> tokens/latency versus stale-state/CNO/reconciliation effects;
- parallel ADW -> elapsed time versus tokens, rework, conflicts, final quality and resource use;
- retry-policy change -> success/recovery versus duplicate effects and wasted attempts;
- new queue/async handoff -> latency/autonomy versus stuck/duplicate/lost-work incidence;
- routing/backpressure -> throughput versus admission errors/starvation/resource waste;
- observability enhancement -> reduced diagnosis/reviewer burden versus trace/storage/operator complexity.

Do not allow lower token use or lower wall time to override correctness, security, provenance, maker/checker, quiescence, acceptance or authority regressions.

Praxist may strengthen experimental design/replication/negative-result tracking but remains an external sandboxed measurement instrument unless separately promoted under its own roadmap law.

## Relationship to simplification hierarchy

This amendment is subordinate to and reinforces the existing SSSF simplification hierarchy:

- Python ADWs remain visible and understandable;
- one deterministic outer execution-graph owner;
- one JSONL + SQLite observability spine;
- one lifecycle owner per resource class;
- agents are bounded reasoning nodes;
- orchestrators recommend; CODE admits;
- reuse one deterministic fan-out/join mechanism for parallelism;
- DSH capabilities admitted one-by-one on demonstrated need;
- extend existing owners before creating new systems;
- every abstraction must remove more complexity than it adds.

A system-design pattern is not an exception to these rules.

## FirstMate roadmap obligation

Whenever FirstMate performs material roadmap design, architecture reconciliation, or phase planning, it should:

1. identify which system-design problem class, if any, is actually present;
2. state the current owner and why it is or is not sufficient;
3. evaluate the smallest candidate mechanism and a simpler alternative;
4. identify applicable failure modes and deterministic controls;
5. identify the new complexity/authority/state/recovery surface;
6. state how value would be measured;
7. prefer `DEFER/REJECT` when the mechanism is premature;
8. after significant implementation, use the normal REF-1/Praxist longitudinal comparison obligation when applicable;
9. record negative findings so a rejected pattern is not repeatedly rediscovered without materially new evidence.

## Success condition

System-design knowledge is being used correctly when SSSF becomes **more predictable and understandable**, not when it contains more distributed-systems components.

A successful review may conclude that no cache, queue, sharding layer, replication mechanism, load balancer or new database is needed.

**Default:** start simple, observe the limitation, select the smallest mechanism, prove failure behavior, measure the value, and remove complexity that does not earn its existence.
