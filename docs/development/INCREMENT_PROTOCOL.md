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

### 4. Implement

Keep the diff inside the increment scope.

Do not mix:

- infrastructure replacement,
- model retuning,
- observability redesign,
- unrelated app changes

in one increment merely because they are convenient.

### 5. Prove

Use the strongest available verifier:

1. deterministic unit/integration test,
2. filesystem/state gate,
3. process/network health assertion,
4. trace reconciliation,
5. independent semantic review only where executable proof cannot decide.

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

### 7. Document

Update:

- increment ledger,
- proof matrix,
- affected runbook/architecture docs,
- ADR if applicable.

### 8. Freeze

Commit the increment and tag a milestone when it establishes a reusable trusted state.

## Increment completion rule

An increment is not complete when the code is written.

It is complete when:

**code + proof + evidence + docs + immutable source identity agree.**
