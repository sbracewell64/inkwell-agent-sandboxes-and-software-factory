# Definition of Done

A change to SSSF is accepted only when all applicable criteria pass.

## Source

- diff is scoped,
- no unexplained changes,
- protected machinery changed only when intentionally in scope,
- working tree is clean after commit.

## Verification

- deterministic tests pass where available,
- gates validate generated artifacts/state,
- negative/failure path is tested for safety-sensitive lifecycle changes,
- no acceptance depends only on model self-report.

## Runtime

- start/retry/failure/cleanup semantics are known,
- resource leaks are checked,
- credentials remain inside intended boundary,
- run identity remains recoverable after failure.

## Evidence

- run ID / ADW ID recorded,
- relevant logs/traces retained,
- exact commit SHA recorded.

## Documentation

- increment ledger updated,
- affected reference docs updated,
- ADR added for architectural decisions,
- known limitations remain explicit.

## Acceptance

- independent review is required when semantic correctness cannot be decided deterministically,
- irreversible/destructive actions follow their explicit authority rule,
- the accepted source state has an immutable Git reference when it forms a new baseline.
