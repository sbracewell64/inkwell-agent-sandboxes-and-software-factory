# FP-001 — Planning Event Producer

Status: `ACTIVE / PRE_CERTIFICATION`

## Intent

Create the SSSF-owned producer half of FUT-003 so Browser-Sol-managed planning promotions can be transported to FirstMate as typed, deterministic events without turning arbitrary planning prose into execution authority.

Problem:

- durable planning state now exists in `FUTURE_CANDIDATES.md`, ADRs, and `ROADMAP.md`;
- FirstMate has no deterministic signal that distinguishes a semantic promotion from an ordinary documentation edit;
- manual Captain relay is therefore still required;
- semantic polling of planning prose would weaken the explicit planning/engineering authority boundary.

Desired outcome:

- one append-only JSONL notification feed;
- one deterministic offline validator;
- one non-actionable bootstrap snapshot that prevents historical replay from activating work;
- exact source-commit and authoritative-document references on every record;
- a contract that allows the consumer to enforce ordered cursor/prefix continuity.

Non-goals:

- no FirstMate implementation in this increment;
- no live FirstMate enablement;
- no merge/main advancement while PRE_CERTIFICATION constraints remain in force;
- no attempt to make the feed a second planning source of truth;
- no semantic interpretation of planning prose;
- no changes to SSSF execution, ADWs, agents, sandboxes, credentials, acceptance, or promotion authority.

Affected boundary:

`Browser Sol planning authority -> typed notification feed -> future FirstMate deterministic transport`

## Baseline reference

`starts_from: 56b4542a38af8e4435da0fa32ac12497aa6f6016`

That commit is the authoritative planning state where FUT-003 is `ACTIVE` and the roadmap names `FP-001` and `FM-FP-001`.

Implementation branch:

`fm/fut-003-planning-events-producer`

## Design

### Sequencing owner

CODE owns record syntax validation, state-machine legality, provenance-shape checks, and offline acceptance.

Browser Sol owns the planning promotion itself and appends the corresponding event only after the authoritative planning commit exists.

### State

Durable producer state:

`docs/development/PLANNING_EVENTS.jsonl`

The feed is append-only in contract. It is a notification index only; authoritative planning meaning remains in the referenced candidate/ADR/roadmap/increment documents at `source_commit`.

### Bootstrap

The first record is exactly one `snapshot` event with `actionability=baseline`.

It establishes the initial planning states and consumer cursor. It cannot create work and is the explicit bootstrap exception to historical transition replay.

### Transition events

Later records use `kind=transition` and bind:

- unique ordered `event_id`;
- `item_id`;
- exact `from` and `to` states;
- full 40-hex `source_commit` that already contains the authoritative state change;
- bounded repository-relative `authoritative_refs`;
- `actionability=awareness` except `to=ACTIVE`, which uses `actionability=engineering`;
- a concrete `increment_id` for `to=ACTIVE`.

The event-append commit is transport provenance. It is deliberately later than `source_commit` and is not the authority being announced.

### Failure modes

The validator fails closed on:

- malformed or non-object JSON;
- blank records or missing final newline;
- unknown/extra fields;
- duplicate or out-of-order event IDs;
- missing/multiple bootstrap snapshots;
- unknown planning states;
- stale `from` states;
- illegal transition edges;
- invalid item/increment identities;
- unsafe/absolute/traversing authoritative paths;
- missing or non-ancestor source commits;
- authoritative files absent at their source commit;
- `ACTIVE` without exact engineering actionability and a concrete increment;
- engineering actionability on any non-`ACTIVE` transition.

Observation gaps in local Git/source availability are reported separately and remain non-pass.

### Rollback

Before canonical adoption, remove the feed, validator, CI registration, and FP-001 documentation. The planning lifecycle remains fully usable from its authoritative documents; only automatic transport is lost.

After canonical adoption, retire the producer only together with a replacement notification transport and a migration/continuity decision for consumers.

## Deterministic acceptance

The increment is eligible for acceptance only when:

1. the honest feed passes with a unique bootstrap snapshot and current FUT states;
2. malformed JSON turns red;
3. duplicate IDs turn red;
4. out-of-order IDs turn red;
5. a second snapshot turns red;
6. an illegal transition turns red;
7. a stale `from` state turns red;
8. an unsafe authoritative path turns red;
9. a missing/non-ancestor source commit is non-pass;
10. an authoritative ref missing at the bound source commit is non-pass;
11. `ACTIVE` without an increment turns red;
12. non-`ACTIVE` engineering actionability turns red;
13. the bootstrap snapshot is mechanically non-actionable;
14. CI enumerates and runs the producer validator on Linux and Windows.

## Evidence to retain

Retain:

- validator output and watched-red control output;
- exact branch/head SHA;
- CI run IDs for Linux and Windows when available;
- the bootstrap feed bytes and digest;
- any unresolved observation or rebase requirement.

## Acceptance boundary

Branch-local green is not `PROVEN`.

Current SSSF PRE_CERTIFICATION constraints prohibit using this increment to advance `main`, merge, tag, freeze, or claim trusted production enablement. Final acceptance requires rebase/revalidation on the then-current canonical SSSF source and the normal independent review/certification path.
