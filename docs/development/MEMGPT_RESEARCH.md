# MemGPT Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **MemGPT: Towards LLMs as Operating Systems**
- arXiv: `2310.08560`

The paper is a memory/context-management research source, not an authorization to adopt MemGPT/Letta or create another agent-memory platform layer.

## Governing interpretation

SSSF should distinguish exact durable history, derived semantic memory, and active model projection as different state classes with different authority.

> **Give the model a memory workspace, not the power to rewrite history.**

## EXPLORE-1 — Exact history and derived semantic memory are separate

Authoritative evidence/history must remain distinct from model-curated semantic memory.

Illustrative classes:

1. authoritative state/evidence;
2. exact durable owner-emitted history;
3. derived semantic memory;
4. active model projection.

Derived memory may summarize, classify, or infer from history but cannot replace the underlying facts.

Routing: `FUT-001`, DSH runtime/context design, `FUT-012`.

## EXPLORE-2 — Active model context is a replaceable projection

The context presented to a model call is not durable memory or project truth. It is a bounded projection over authoritative inputs, exact history, derived memory, and task-specific state.

Compaction or projection changes must not destroy the underlying durable information required for replay, evidence, continuation, or later reinterpretation.

## EXPLORE-3 — Agents may curate derived memory, never authoritative history

A bounded semantic worker may propose/store derived memories such as hypotheses, summaries, learned heuristics, or useful facts with provenance.

It may not rewrite or erase authoritative requirements, exact historical events, validator results, source identity, Browser Sol rulings, acceptance evidence, or other protected truth.

CODE owns that authority boundary mechanically.

## EXPLORE-4 — Working/scratch context is ephemeral

Cell working memory/scratch state may hold current hypotheses, local plans, unresolved questions, and temporary semantic notes.

It is:

- cell-scoped;
- ephemeral;
- non-authoritative;
- replaceable.

Anything required for durable continuation or proof must cross into a typed owner-emitted result/event before scratch state is discarded.

## EXPLORE-5 — Context compression is non-destructive

Compression is not retention.

SSSF may produce summaries and compact projections to stay inside context budgets, but the exact durable history/evidence remains available according to its retention policy.

Recursive summaries must not become the only surviving representation of facts whose loss would matter.

## EXPLORE-6 — CODE owns context pressure and retrieval backpressure

CODE should own model context limits, reserved output capacity, hard projection budgets, pagination, and broad-query backpressure.

Agents may exercise semantic judgment over what information appears relevant inside those limits.

History/memory retrieval should support bounded operations and typed refinement such as `TOO_BROAD` rather than unbounded context flooding.

## EXPLORE-7 — Memory records require provenance and applicability

Derived memories and retrieved historical claims should preserve, as applicable:

- evidence classification (`OBSERVED`, `INFERRED`, etc.);
- producer/generation;
- source/evidence references;
- source or working generation;
- applicability/scope;
- staleness or unknown-applicability status.

A retrieved memory is not automatically current truth.

## EXPLORE-8 — Deterministic vs semantic retrieval

Where the runtime already knows a typed dependency or required historical artifact, CODE should retrieve/project it deterministically.

AGENT-directed retrieval is appropriate for emergent semantic uncertainty, but remains bounded and mediated by CODE.

Use the lowest sufficient autonomy.

## EXPLORE-9 — Context/memory policy is part of effective runtime identity

Materially different context projection, compaction, retrieval, or semantic-memory generations can materially change agent behavior.

Qualification should therefore bind behaviorally relevant context/memory policy identity where used.

## EXPLORE-10 — Retention authority differs from relevance judgment

AGENT may propose what seems semantically important.

CODE owns what must not be lost, retention requirements, provenance rules, context budgets, and projection mechanics.

Semantic importance and retention authority must not be conflated.

## EXPLORE-11 — Memory scope preserves maker/checker independence

Persistent semantic memory should be scoped by role/cell/profile where necessary. Independent reviewers should not automatically inherit maker cognition or communal memory.

Cross-unit information moves through explicit admissible typed results/evidence.

## EXPLORE-12 — Qualification requires memory-leakage controls

Persistent memory can contaminate replay/frontier evaluation if hidden historical patches, verifier answers, reviewer verdicts, or prior solution details leak into a later solver context.

Qualification episodes require explicit permitted-memory generations or an equivalent clean-state/isolation mechanism.

## Additional supporting observations

- Event/interrupt/function chaining may exist inside bounded DSH execution but cannot become SSSF outer workflow authority.
- Derived memories may later inform `Preserve -> Purify -> CODEward` analysis when repeated stable semantic observations can be mechanized.
- Memory quality/provenance matters more than maximizing remembered volume.
- Model-private reasoning transcripts are not required as durable memory; compact claims with provenance/evidence references are preferable.

## Non-decisions

This research does **not** authorize:

- adopting MemGPT or Letta as SSSF memory infrastructure;
- a generic shared-memory service across agents;
- agent mutation of authoritative evidence/history;
- persistent memory across qualification episodes without leakage controls;
- turning model events/interrupts into outer workflow authority;
- roadmap or candidate-state promotion.
