# LLMCompiler Parallelism Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **An LLM Compiler for Parallel Function Calling**
- arXiv: `2312.04511`

The paper is a semantic-planning / deterministic-scheduling research source, not an authorization to adopt LLMCompiler itself.

## Governing interpretation

Agent-generated orchestration is a candidate intermediate representation. CODE must compile, validate, schedule, and execute it.

> **Let the agent write the plan as an intermediate program. Let CODE decide whether that program is legal to run.**

## EXPLORE-1 — Agent-generated task graph is candidate IR

Semantic planning may produce a typed task-graph candidate with nodes, objectives, dependencies, required capabilities, expected outputs, and requirement lineage.

The graph is derived execution planning, not workflow authority and not a replacement for the authoritative WorkPackage.

## EXPLORE-2 — CODE compiles and validates task graphs

Before execution, CODE validates at least:

- schema and unique node identities;
- dependency existence and acyclicity;
- capability existence and qualification;
- authority/effect/network compatibility;
- budget feasibility;
- source/workspace bindings;
- required input/output contracts;
- resource/write conflicts;
- deterministic graph invariants.

Mechanical graph validity remains distinct from semantic requirement coverage.

## EXPLORE-3 — Parallelism is mechanically derived

Do not rely on a model's `parallel=true` suggestion.

CODE derives concurrency from admitted dependencies plus resource/effect conflicts, source/workspace policy, and authority.

Once dependency semantics are admitted, ready-task scheduling is deterministic CODE work.

## EXPLORE-4 — Deterministic ready-task scheduling

A task becomes executable only when all admitted prerequisites hold and no current resource/effect conflict prevents execution.

CODE owns ready-queue admission, backpressure, scheduling, result collection, failure folding, cancellation, and peer-survival policy.

Routing: `SBX-7` and future DSH workflow execution.

## EXPLORE-5 — Separate typed node outputs

Parallel node results remain separate attributable evidence units. Downstream nodes consume explicit producer/output refs and digests rather than inheriting one merged conversational context.

Dependency bindings may also carry trust/authority class where relevant.

## EXPLORE-6 — Immutable graph generations

A validated graph generation is immutable while executing.

If new evidence requires replanning, produce a new graph generation with explicit `supersedes` and trigger-observation provenance; do not silently mutate a live plan.

Inner graph generations remain descendants of one `execution_cell_id` / outer attempt unless outer SSSF policy explicitly terminates/retries.

## EXPLORE-7 — Capability/authority checks are compilation concerns

A semantically plausible graph can still be illegal to execute.

The compiler must reject nodes that request unavailable/unqualified capabilities, exceed authority, violate effect/network policy, or cannot satisfy required resource/budget constraints.

Capability availability is not authority.

## EXPLORE-8 — Mechanical validity vs semantic requirement coverage

A DAG can be structurally valid while omitting an authoritative requirement.

Therefore graph qualification separates:

- mechanical graph validity; and
- semantic requirement coverage against the authoritative requirement ledger.

Derived graph nodes should retain requirement lineage where applicable.

## EXPLORE-9 — Static DAG before adaptive/streamed replanning

Qualify complete-plan / validate / freeze / execute semantics before considering streamed planning or adaptive graph extension.

Streaming semantic plans can introduce dependency/authority races if work begins before the complete relevant frontier is understood. Admit streamed/adaptive planning only after stronger graph-frontier correctness is proven and measured latency value justifies the complexity.

## EXPLORE-10 — Parallel mutation workers remain isolated

Parallel engineering nodes should use isolated disposable workspaces/sandboxes by default rather than concurrently mutating one shared checkout.

Shared-state parallel mutation requires a separately qualified transactional concurrency mechanism and is not implied by graph-level independence.

## Additional supporting observations

- Planner tool catalog, prompt/protocol, interface generation, and graph-policy generation are part of effective execution identity when materially behavior-changing.
- Duplicate mechanically equivalent graph nodes should be deduplicated or require an explicit semantic distinction where CODE can establish equivalence safely.
- Parallelism should be evaluated using wall-time gain, straggler cost, total compute, admission delay, failed-peer effects, and cleanup burden—not assumed beneficial.
- Intermediate node outputs should carry trust/authority classification when they are not authoritative observations.

## Non-decisions

This research does **not** authorize:

- adopting LLMCompiler;
- agent-owned outer scheduling;
- streamed graph execution before complete-graph qualification;
- dynamic DSH replanning before the relevant DSH stage;
- shared mutable workspaces for parallel mutation agents;
- graph plans superseding authoritative requirements;
- any change to the Docker-first / baseline / Wayfinder / DSH roadmap order.
