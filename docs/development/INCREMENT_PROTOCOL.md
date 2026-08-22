# Increment Protocol

Every post-baseline change is a named, independently provable increment.

## Required lifecycle

### 1. Intent

Record:

- increment ID,
- problem,
- desired outcome,
- non-goals,
- affected boundary.

### 2. Baseline reference

State the exact starting tag/SHA.

Example:

`starts_from: sssf-local-b0`

### 3. Design

Identify:

- code owner of sequencing,
- agent role if reasoning is required,
- state changes,
- failure modes,
- rollback,
- deterministic acceptance.

Architectural changes require an ADR.

Every implementation increment must also declare its boundedness effect under [`BOUNDEDNESS_LAW.md`](BOUNDEDNESS_LAW.md):

```text
boundedness_delta:
  added: [...surface_ids]
  changed: [...surface_ids]
  retired: [...surface_ids]
```

or, only when the diff cannot create or change a growing surface:

```text
boundedness_delta: none
boundedness_reason: <specific justification>
```

Lists, queues, logs/event streams, retries/refinement loops, child/subagent sets, caches, retained artifacts and any other state that grows with input, work or time are in scope. A changed growth owner with an undeclared boundedness delta makes the increment incomplete.

### 4. Implement

Keep the diff inside the increment scope.

Do not mix:

- infrastructure replacement,
- model retuning,
- observability redesign,
- unrelated app changes

in one increment merely because they are convenient.

New or changed growth surfaces must use the boundedness registry/owner mechanism once that mechanism is commissioned. The implementation must define what happens at the boundary; a numeric limit without overflow/backpressure/retention semantics is incomplete.

### 5. Prove

Use the strongest available verifier:

1. deterministic unit/integration test,
2. filesystem/state gate,
3. process/network health assertion,
4. trace reconciliation,
5. independent semantic review only where executable proof cannot decide.

For an added or changed dynamic bound, prove the effective limit and the intended boundary behavior at `limit - 1`, `limit`, and `limit + 1`, or the closest meaningful equivalents. Where the boundedness validator is applicable, it is a required deterministic verifier rather than an optional documentation check.

### 6. Retain evidence

Record:

- commands,
- outputs,
- run IDs,
- ADW IDs,
- commit SHAs,
- artifact paths,
- test counts,
- known unresolved observations.

For growth surfaces, retain the bound/policy identity, observed high-water or boundary evidence where applicable, and any overflow/backpressure/eviction outcome relied upon for acceptance.

### 7. Document

Update:

- increment ledger,
- proof matrix,
- affected runbook/architecture docs,
- ADR if applicable,
- boundedness registry for every added/changed/retired growth surface once commissioned.

### 8. Freeze

Commit the increment and tag a milestone when it establishes a reusable trusted state.

## Increment completion rule

An increment is not complete when the code is written.

It is complete when:

**code + proof + evidence + docs + immutable source identity agree.**

After boundedness enforcement is commissioned, that agreement also requires the increment's declared boundedness delta to match the machine-readable boundedness registry and the canonical boundedness validator to be PASS (or an explicitly permitted CNO where the governing acceptance policy allows it).
