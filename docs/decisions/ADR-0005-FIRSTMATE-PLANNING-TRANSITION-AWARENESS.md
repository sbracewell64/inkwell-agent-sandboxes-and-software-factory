# ADR-0005 — FirstMate Planning-Transition Awareness

- **Status:** Accepted design direction; implementation unsequenced and inactive
- **Date:** 2026-08-18
- **Planning item:** FUT-003
- **FirstMate evaluation baseline:** `sbracewell64/firstmate@f4e69d6ce411750b55fc9f186f60ce0e8b0cd786`

## Context

SSSF future planning now uses an explicit lifecycle:

```text
EXPLORE -> PRESERVE -> CANDIDATE -> DECIDED -> SEQUENCED -> ACTIVE -> PROVEN
```

Browser Sol maintains the durable planning state with Captain authorization. FirstMate should learn about durable planning promotions without requiring the Captain to relay them manually, but it must not infer execution authority from prose, arbitrary document diffs, or roadmap presence.

FirstMate already has a hardened continuous watcher, authenticated custom checks, durable wake handling, and cursor/hash continuity patterns. A separate polling service or a model-driven scan of planning documents would duplicate existing machinery and weaken the planning/engineering boundary.

## Decision

### 1. FirstMate consumes typed planning transitions, not planning prose

The architectural invariant is:

> **FirstMate consumes typed planning transitions; it never derives execution authority from planning prose.**

SSSF planning will expose a small append-only transition feed when this design is implemented. The intended location is:

`docs/development/PLANNING_EVENTS.jsonl`

The feed is a notification index only. It is not a new source of architectural or engineering truth. Each event must identify the authoritative planning artifacts and exact Git source identity that govern the transition.

### 2. Reuse FirstMate's existing authenticated custom-check/watch path

The preferred detector is one registered FirstMate custom check running on the existing `fm-watch` cadence.

Do not create a second polling daemon.

The detector should:

- read only the configured SSSF planning source;
- validate the event schema mechanically;
- track an append-only cursor;
- emit no output when no unseen valid event exists;
- surface one bounded oldest-unseen event at a time;
- use the existing durable check wake path for nonempty results.

### 3. Reuse remote-delta continuity semantics without adopting process-event topology

The planning cursor should reuse the semantic contract already demonstrated by FirstMate's remote-delta reader:

- byte offset;
- prefix SHA-256;
- bounded complete-line payloads;
- explicit continuity failure on truncation, replacement, or changed prefix;
- no silent rebasing.

The blocking process-event runner is not the preferred primary detector because GitHub planning state is periodically checked repository state rather than a naturally blocking external process source.

### 4. Only `ACTIVE` may cross into engineering intake

Planning states have mechanically distinct effects in FirstMate:

- `PRESERVE`, `CANDIDATE`, `DECIDED`, `SEQUENCED`, `SUPERSEDED`, and `PROVEN`: awareness/constraint refresh only; no engineering task is created from the event;
- `ACTIVE`: eligible for normal FirstMate engineering intake.

Even an `ACTIVE` event is not itself executable authority. FirstMate must fetch the named increment and authoritative documents at the exact referenced source identity, verify applicability, and pass the work through ordinary admission/classification before acting.

`SEQUENCED` is explicitly not equivalent to `ACTIVE`.

### 5. Browser Sol retains planning-promotion authority

Browser Sol, under Captain authorization, owns:

- planning-state promotion;
- `FUTURE_CANDIDATES.md` maintenance;
- ADR creation/update for `DECIDED` architecture;
- roadmap placement for `SEQUENCED` work;
- future append of the corresponding typed planning-transition event.

FirstMate does not promote SSSF planning states through this mechanism and does not edit Browser-Sol-owned planning documents merely because it observed an event.

### 6. Continuity and stale-state failures fail closed

FirstMate must not advance its cursor when an event source is malformed, unavailable in a way that prevents verification, or continuity-broken.

A stale or malformed `ACTIVE` reference must not activate work.

Continuity failure should surface as a bounded operational failure for investigation; it must never cause an automatic reset to the current tail or a semantic guess about missed transitions.

## Intended event contract

The exact schema remains implementation work, but the design requires fields equivalent to:

```json
{
  "schema": "sssf-planning-event/v1",
  "event_id": "plan-...",
  "item_id": "FUT-...",
  "from": "CANDIDATE",
  "to": "DECIDED",
  "source_commit": "<exact Git SHA>",
  "authoritative_refs": ["<repo paths>"],
  "actionability": "awareness"
}
```

An activation event additionally identifies the named increment and uses `to: "ACTIVE"` with engineering actionability.

## Required implementation proofs before sequencing/admission

A future FirstMate increment must prove at least:

1. no appended event -> no wake;
2. ordered delivery of multiple events;
3. duplicate event -> no duplicate transition effect;
4. tampered/unregistered custom check -> rejected;
5. prefix change/truncation -> explicit continuity failure and no cursor advance;
6. malformed event -> no cursor advance and no inferred action;
7. non-`ACTIVE` states -> no engineering task;
8. stale or invalid `ACTIVE` source identity -> no activation;
9. valid `ACTIVE` -> enters only the existing normal FirstMate admission path;
10. retirement of the planning check cleanly restores manual inspection/transport without changing SSSF planning truth.

## Consequences

### Positive

- removes routine Captain relay of promoted planning state;
- preserves the explicit planning-to-engineering activation boundary;
- reuses FirstMate's existing watcher instead of adding another service;
- provides deterministic state classification rather than semantic inference from prose;
- gives continuity failures an explicit, fail-closed contract;
- keeps planning truth in SSSF's existing candidate/ADR/roadmap/increment documents.

### Costs and obligations

- SSSF will eventually need a small append-only transition feed and schema;
- FirstMate will need a bounded custom-check adapter plus private cursor/receipt state;
- source freshness and exact Git identity must be checked before `ACTIVE` intake;
- awareness refresh behavior must remain bounded so non-active planning changes do not become hidden work queues.

## Alternatives rejected

### Semantic reread of planning documents

Rejected. File changes and prose are not authority transitions. A model must not infer that `SEQUENCED` or an edited ADR means work should start.

### Separate planning daemon

Rejected. FirstMate already owns a continuous watcher and authenticated periodic checks. A second polling owner adds lifecycle and quiescence complexity without measured value.

### Process-event as the primary detector

Not selected. Its durability/cursor discipline is useful, but its blocking-source topology is unnecessary for a GitHub repository source already suited to the existing periodic check path.

## Sequencing

This decision is **not sequenced for implementation**.

Implementation should be considered only when the planning branch itself is ready to enter the accepted SSSF documentation surface and a bounded FirstMate increment is explicitly activated. Until then, manual inspection/transport remains acceptable and no FirstMate watcher behavior changes.

## Non-goals

This ADR does not:

- create `PLANNING_EVENTS.jsonl` yet;
- modify FirstMate;
- register a FirstMate custom check;
- create a FirstMate task or control-plane escalation;
- sequence implementation on the SSSF roadmap;
- allow FirstMate to promote planning state;
- make `SEQUENCED` work executable;
- bypass normal FirstMate admission for `ACTIVE` work.
