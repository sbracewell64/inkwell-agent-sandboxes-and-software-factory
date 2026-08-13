# ADR-0001 — Proven Increments Are the Unit of SSSF Evolution

**Status:** Accepted  
**Date:** 2026-08-13

## Context

The system will be augmented substantially. Agent-generated code can make changes quickly, but speed without provenance makes it difficult to distinguish a working baseline from an accumulation of assumptions.

## Decision

SSSF evolution will use a proven-increment protocol.

Each accepted increment must bind together:

- intent,
- bounded implementation,
- deterministic or explicit semantic acceptance,
- retained evidence,
- documentation,
- immutable Git identity.

## Consequences

Positive:

- regressions can be bisected,
- agents can recover system intent from files,
- architectural changes retain rationale,
- a known-good state is always nameable.

Cost:

- more documentation and evidence discipline,
- changes that cannot be proved remain open rather than being declared complete.

## Rejected alternative

Treating the latest working tree as the system of record.

Reason:

a working tree cannot distinguish accepted design from experiments, fixes, or unverified changes.
