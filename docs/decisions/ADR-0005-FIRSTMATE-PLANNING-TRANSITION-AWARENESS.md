# ADR-0005 — FirstMate Planning-Transition Awareness

- **Status:** Accepted design direction; implementation sequenced, activation deferred; not active or proven
- **Date:** 2026-08-20
- **Planning item:** FUT-003
- **Lifecycle owner:** [`PLANNING_LIFECYCLE.md`](../development/PLANNING_LIFECYCLE.md)
- **Durable state record:** [`PLANNING_STATE.json`](../development/PLANNING_STATE.json)
- **FirstMate evaluation baseline:** `sbracewell64/firstmate@f4e69d6ce411750b55fc9f186f60ce0e8b0cd786`

## Context

SSSF future planning needs a durable distinction between architectural intent,
sequenced work, bounded engineering authorization, and proof. The canonical
state machine and all legal edges are owned by
[`PLANNING_LIFECYCLE.md`](../development/PLANNING_LIFECYCLE.md); this ADR does
not define another graph.

FirstMate may eventually learn about deliberate planning promotions without a
Captain relay, but it must not infer execution authority from prose, arbitrary
planning-document diffs, roadmap presence, or an ADR edit. A future transport
must remain source-bound and pass through ordinary admission.

## Decision

### 1. Typed planning awareness, not semantic planning interpretation

A future implementation may expose a bounded typed planning signal that points
to the authoritative planning documents and exact Git source identity. The
signal would be a notification index, not a new source of architectural,
engineering, runtime, or acceptance truth. It must use normal FirstMate
admission and exact referenced source identity checks.

This repair adds no signal/feed, watcher, FirstMate custom check, producer,
consumer, task, or runtime behavior. Manual inspection remains the current
transport.

### 2. Existing admission machinery remains the boundary

Any future consumer must use the existing authenticated admission/check path
rather than creating a second polling owner. It must mechanically validate the
signal, preserve cursor/continuity failure closed, and refuse malformed,
stale, unavailable, or source-mismatched input.

Observation of a planning record never bypasses ordinary FirstMate admission,
classification, permissions, exact source validation, review, acceptance, or
SSSF PRE_CERTIFICATION constraints. A planning record does not create
execution authority, and any implementation must not be merged merely because
branch-local tests pass.

### 3. `ACTIVE` has a narrow meaning

`ACTIVE` is engineering authorization and intake eligibility only. Even a
future valid ACTIVE record would never be task creation, execution authority,
landing authority, a PRE_CERTIFICATION exit, acceptance, certification, live
enablement, or `PROVEN`.

A future ACTIVE record must bind every named increment to an exact branch,
exact PR URL/identity, exact source commit SHA, exact source tree SHA, and
bounded authoritative references. If any identity is missing, the durable
current state is `SEQUENCED` and activation is deferred. No unbound or partial
ACTIVE record is valid.

### 4. Browser Sol retains planning authority

Browser Sol/Captain-controlled planning records own promotion through
`SEQUENCED` and maintain the candidate register, ADR, roadmap, and durable
state record. FirstMate does not promote planning state and does not edit those
records merely because it observes them.

### 5. `PROVEN` remains downstream proof

`PROVEN` means implementation, deterministic proof, retained evidence,
required documentation, and immutable accepted source identity agree under the
canonical lifecycle contract. It is not proven merely because a planning state
or local test says so. It cannot be inferred from `ACTIVE`, local tests,
a planning row, a commit subject, or a validation message.

## Required future admission proofs

A future bounded implementation would need, at minimum, deterministic proof
that malformed/duplicate/unknown/illegal or source-mismatched signals fail
closed; continuity failures do not advance state; non-ACTIVE records do not
create work; and a valid ACTIVE record enters only the existing normal FirstMate
admission path after exact source validation. Those proofs are not implemented
by this planning repair.

## Consequences

- The planning/engineering boundary is explicit and remains fail-closed.
- No current FirstMate, SSSF producer, watcher, credential, sandbox, provider,
  ADW, Docker, Wayfinder, DSH, or live-enablement behavior changes.
- The durable current state remains `SEQUENCED` because the exact identities
  needed for an honest ACTIVE record do not yet exist.
- Future implementation must be separately bounded, reviewed, accepted, and
  requalified against current surfaces.

## Sequencing status

FUT-003 is durably `SEQUENCED`, not `ACTIVE`. The planned names `FP-001` and
`FM-FP-001` are not implementation identity bindings. The ACTIVE transition is
legal only from the durable `SEQUENCED` record and is deferred until all exact
identities and ordinary acceptance inputs exist.

## Non-goals

This ADR does not:

- create a planning event feed or runtime consumer;
- modify FirstMate or register a watcher/check;
- create a task or control-plane wake;
- make `SEQUENCED` executable;
- grant planning records runtime, landing, PRE_CERTIFICATION-exit,
  acceptance, certification, or live-enablement authority;
- make FUT-003 `ACTIVE` or `PROVEN`; or
- bypass exact source validation or normal admission.
