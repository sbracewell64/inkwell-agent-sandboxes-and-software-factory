# AutoCodeRover Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **AutoCodeRover: Autonomous Program Improvement**
- arXiv: `2404.05427`

The paper is a program-analysis / agent-localization research source, not an adoption decision for AutoCodeRover itself.

## Governing interpretation

Structural code intelligence should be available as deterministic narrowing before open-ended DSH cognition. Program-analysis outputs remain attributable diagnostic evidence, not workflow or acceptance authority.

## EXPLORE-1 — Structural code intelligence before open-ended cognition

Prefer deterministic repository/program structure to reduce the search space before spending broad agent cognition.

Potential source-intelligence capabilities may expose semantic entities and relations such as classes, methods, symbols, inheritance, references, callers, dependencies, and bounded source projections.

Do not hard-code `AST` as public SSSF architecture. AST, LSP, code indexes, call graphs, or future mechanisms are replaceable implementations behind qualified code-intelligence capabilities.

Routing: `FUT-001`, especially DSH-5.

## EXPLORE-2 — Stratified context retrieval

Avoid both one-shot context selection and maximal repository/file dumps.

Preferred pattern:

```text
cheap deterministic structure
        ↓
agent selects relevant semantic uncertainty
        ↓
bounded structural query
        ↓
new facts/entities
        ↓
progressively narrower query if justified
```

Context should be progressively earned by relevance and stop expanding when additional retrieval no longer justifies its cognition/cost burden.

This strengthens the previously preserved hierarchical-context-narrowing principle.

## EXPLORE-3 — Typed localization handoff artifact

A localization phase should terminate with a typed evidence handoff rather than requiring a downstream builder to inherit the prior agent's narrative reasoning history.

Potential fields include:

- exact source identity;
- candidate entities/locations;
- structural evidence refs;
- execution/fault-localization evidence refs;
- issue/specification references;
- relevant source projections;
- alternative hypotheses;
- unresolved semantic uncertainty.

The handoff is evidence and state, not acceptance authority.

Routing: DSH phase handoffs, replay/trace evidence, harness scorecard.

## EXPLORE-4 — Multi-channel localization evidence

Keep localization channels separately attributable rather than collapsing them into one score or opaque search result.

Potential channels:

- issue/WorkPackage clues;
- deterministic structural code intelligence;
- execution traces / failing-test context;
- spectrum-based or other dynamic fault-localization signals;
- text / embedding retrieval;
- later LSP/static-analysis/data-flow signals;
- semantic agent interpretation.

CODE emits/collects observable facts and candidate sets. AGENT reconciles ambiguity where deterministic evidence cannot settle the question.

Dynamic/program-analysis suspiciousness scores remain diagnostic evidence, not proof of defect location.

## EXPLORE-5 — Specification provenance remains explicit

Program structure and analogous code can provide strong evidence of likely intended behavior, but this remains inferred specification unless independently documented or observed.

Preserve distinctions such as:

- `DOCUMENTED` — accepted requirement/design/contract;
- `OBSERVED` — tests/code/runtime facts;
- `INFERRED` — likely intent/convention derived from structure or analogues.

Structural similarity must never silently rewrite Engineer intent or authoritative acceptance criteria.

## Additional supporting findings

- Unsupported code-intelligence operations should return typed capability/backpressure results with available alternatives rather than generic errors that invite repeated invalid calls.
- Correct localization is necessary but not sufficient; implementation failures remain substantial even when the right methods are found.
- Test PASS does not establish semantic correctness; independent semantic review remains applicable where policy requires it.
- Structural code-intelligence changes should be evaluated through the harness scorecard/replay corpus rather than admitted because a specific analysis technology appears sophisticated.
- Bounded mutation retries remain CODE-controlled and budgeted; retry exhaustion never implies acceptance of a best-so-far candidate.
- Difficult tasks do not become Captain questions merely because localization or implementation is hard; FirstMate/Browser Sol/DSH should exhaust delegated engineering authority first.

## Non-decisions

This research does **not** authorize:

- AutoCodeRover adoption;
- a new AST subsystem or code-graph source of truth;
- immediate LSP/call-graph/data-flow implementation;
- DSH activation;
- program-analysis outputs as acceptance authority;
- roadmap or FUT-state promotion.
