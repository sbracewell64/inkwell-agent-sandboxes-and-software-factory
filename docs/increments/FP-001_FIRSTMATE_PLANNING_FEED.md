# FP-001 — FirstMate Planning Transition Feed

## Planning identity

- Parent item: `FUT-003`
- Governing decision: `docs/decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`
- Planning state: `ACTIVE`
- SSSF implementation branch: `implementation/fut-003-planning-feed`
- FirstMate companion increment: `FM-FP-001`
- FirstMate implementation branch: `fm/sssf-planning-awareness`
- Production enablement: **not authorized by this record**
- Canonical landing: **held by current SSSF PRE_CERTIFICATION constraints**

## Intent

Create the SSSF-owned producer side of the planning-transition bridge without allowing planning prose, Git diffs, or non-`ACTIVE` planning states to become engineering authority.

The producer emits a small append-only notification index at:

`docs/development/PLANNING_EVENTS.jsonl`

The feed is transport metadata only. `FUTURE_CANDIDATES.md`, accepted ADRs, the roadmap, named increment records, executable code/tests, and retained evidence remain authoritative for their respective facts.

## Required contract

1. The first feed record is exactly one non-actionable bootstrap snapshot.
2. The bootstrap snapshot may establish current planning states and cursor position but can never create work.
3. Later records are ordered state transitions with unique event identities.
4. Each transition names a full Git source commit that already contains the authoritative state change. The later commit that appends the event is transport provenance, not the authority being announced.
5. Planning states are closed-set and transitions are checked against the planning lifecycle.
6. `ACTIVE` must name at least one concrete increment identity and bounded authoritative repository path.
7. Non-`ACTIVE` records are awareness-only.
8. A feed rewrite, truncation, prefix mutation, duplicate event identity, malformed record, illegal transition, stale/missing authority reference, or invalid path must fail closed.

## Producer acceptance

The implementation must provide a deterministic offline validator proving at minimum:

- honest feed passes non-vacuously;
- bootstrap snapshot is unique, first, and mechanically non-actionable;
- every record is one JSON object on one complete line;
- event IDs are unique and monotonically ordered by their declared sequence;
- states and event kinds are closed-set;
- transition edges are legal;
- source commit identities are full 40-hex Git object IDs;
- authoritative refs are repository-relative, normalized, non-traversing paths under governed documentation roots;
- `ACTIVE` transitions carry an increment binding;
- malformed JSON, duplicate IDs, illegal edges, invalid refs, missing full source identity, and a second bootstrap snapshot produce non-pass;
- a bounded defective feed demonstrates each required watched-red control.

## Consumer acceptance dependency

`FM-FP-001` owns the FirstMate consumer. It must use the existing authenticated custom-check/watch lifecycle and private cursor/receipt state. It may not add a second polling daemon.

The consumer must prove:

- no new event means silence;
- continuity mismatch never advances the cursor;
- bootstrap creates no task;
- duplicate/malformed/stale events cannot create duplicate/stale effects;
- all non-`ACTIVE` states are awareness-only;
- `ACTIVE` is intake eligibility, not direct execution authority;
- referenced increment/docs are fetched and admitted normally before work begins;
- retiring the check/cursor restores pre-bridge behavior without changing SSSF planning truth.

## Sequencing

```text
FP-001 contract + validator
    -> FM-FP-001 consumer against fixed producer fixtures
    -> rebase each side onto settled acceptance surfaces
    -> independent review / validation
    -> live enablement
    -> PROVEN only after accepted immutable identities agree
```

## Current implementation candidates

These identities record the current isolated implementation candidates only. They are **not accepted/proven heads**, and no validation result may be carried forward automatically after either branch moves.

- SSSF producer candidate: `implementation/fut-003-planning-feed` at `fa435c6ae58c2f4d0d610ba8135b49e128f26699`
  - adds `PLANNING_EVENTS.jsonl` with the non-actionable bootstrap snapshot;
  - adds `planning_event.schema.json`;
  - adds `docs/validation/check_planning_events.py` with closed-state/edge, exact-source/ref, append-only, and watched-red controls.
- FirstMate consumer candidate: `fm/sssf-planning-awareness` at `92be0b407ab4952bfe1e2d3c499391b41daf17a6`
  - adds the SSSF planning-awareness adapter;
  - binds the registered watcher shim to the exact adapter digest in addition to FirstMate's existing custom-check trust binding;
  - keeps a private offset/prefix-hash cursor and pending generation;
  - adds the agent-only handling skill;
  - adds a hermetic regression for bootstrap pending/acknowledgement, unchanged-feed silence, prefix mutation refusal, and `ACTIVE` intake-without-direct-task creation;
  - replaces the initial function-level `RETURN` cleanup with a check-owned subshell/`EXIT` cleanup so helper returns cannot destroy staging mid-check.

No CI, independent review, watcher-suite rebase, live enablement, landing, or canonical proof is claimed by recording these heads.

## Current restrictions

This increment may be implemented and tested on its isolated branch now. It must not be merged, tagged, frozen, or represented as trusted/canonical while the governing PRE_CERTIFICATION constraints remain in force.

The FirstMate consumer may likewise be implemented on its isolated branch, but must not be production-enabled until rebased and requalified against the settled FirstMate watcher/test surface.
