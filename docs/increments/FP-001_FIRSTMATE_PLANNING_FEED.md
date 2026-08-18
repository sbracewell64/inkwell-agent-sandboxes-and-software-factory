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

## Producer surface

| Artifact | Role |
|---|---|
| `docs/development/PLANNING_EVENTS.jsonl` | the append-only typed notification index |
| `docs/development/planning_event.schema.json` | record schema |
| `docs/reference/PLANNING_EVENTS.md` | producer contract and append procedure |
| `docs/validation/check_planning_events.py` | deterministic offline validator and watched-red controls |
| `ci/checks.json` / `docs/validation/check_ci_contract.py` | enumerate the validator as `planning-event-producer-validator` |

Each record binds its authority on two immutable axes — the full `source_commit` plus the full
Git blob id of every `authoritative_ref` at that commit — because CI checks out at
`fetch-depth: 1` and consumers may hold shallow clones. An object that is genuinely absent is
reported as could-not-observe rather than passed or failed; `--require-git-witness` upgrades
every such axis to a failure for full-depth qualification.

## Executed proof matrix

Recorded from the validator's own output on this branch. Every control is a named mutation that
must produce its own specific diagnostic; a red caused by unrelated breakage does not count.

- **56 controls executed, 56 watched reds observed**, in-process on every run
  (49 record-grammar, 7 continuity).
- **Non-vacuity partners** (proven able to pass before any red is trusted): the honest feed; an
  honest bootstrap + awareness-transition + `ACTIVE`-transition chain; an honest append; an
  unchanged feed. If any partner fails, the run reports vacuity instead of reds.

| Required control | Named reds |
|---|---|
| honest feed passes non-vacuously | the four non-vacuity partners above |
| bootstrap unique, first, non-actionable | `second-bootstrap`, `bootstrap-not-first`, `bootstrap-actionable`, `bootstrap-carries-increments`, `bootstrap-carries-transition`, `bootstrap-missing-states` |
| canonical one-object-per-line | `malformed-json`, `duplicate-object-key`, `non-canonical-key-order`, `non-compact-separators`, `non-object-line`, `blank-record`, `missing-trailing-lf`, `cr-framing`, `utf8-bom` |
| unique, ordered ids and sequences | `duplicate-event-id`, `non-increasing-event-id`, `sequence-gap`, `sequence-not-integer` |
| closed-set states and kinds | `unknown-kind`, `unknown-actionability`, `unknown-bootstrap-state`, `unknown-to-state` |
| legal transitions only | `illegal-edge`, `terminal-state-exit`, `stale-from-state`, `unknown-item-not-from-explore` |
| full exact Git source identities | `short-source-commit`, `uppercase-source-commit`, `symbolic-source-commit`, `missing-blob-binding`, `short-blob-id`, `blob-ref-set-mismatch` |
| bounded, normalized authoritative refs | `ref-traversal`, `ref-absolute`, `ref-outside-docs`, `ref-double-slash`, `ref-dot-segment`, `ref-trailing-slash`, `ref-backslash`, `ref-over-length`, `refs-unsorted`, `refs-empty` |
| `ACTIVE` requires an increment binding | `active-without-increments`, `active-awareness-actionability`, `active-bad-increment-identity`, `active-increment-not-referenced`, `non-active-carries-increments`, `non-active-engineering` |
| prefix mutation observable | `truncation`, `record-removal`, `prefix-byte-mutation-first`, `prefix-byte-mutation-middle`, `prefix-byte-mutation-last`, `historical-replacement`, `prefix-mutation-with-honest-append` |

Controls executed outside the process, against the live repository, because they mutate real Git
or CI state:

| Control | Mutation | Observed |
|---|---|---|
| blob-binding-mismatch | declared blob id for `ROADMAP.md` set to `0`×40 | RED — `blob binding mismatch` |
| ref-absent-at-source | `source_commit` moved to `56b4542`, which predates the FP-001 record | RED — `authoritative ref absent at source_commit` |
| require-git-witness | unresolvable `source_commit` under `--require-git-witness` | RED — gaps upgraded to failures |
| ci-enumeration | validator removed from `ci/checks.json` only | RED — `enumerated offline checks differ` |
| shallow-checkout | depth-1 clone of this worktree | GREEN, 56 reds still observed, 5 axes reported could-not-observe |

Continuity against the accepted baseline currently reports **`unpublished`** — `origin/main`
holds no feed, so there are no published bytes to compare. That is a stated third value, not a
pass. Prefix-mutation detection is therefore proven by the seven synthetic continuity controls
above rather than by branch history.

The consumer-side matrix (`FM-FP-001`) is not proven by this increment.

## Current restrictions

This increment may be implemented and tested on its isolated branch now. It must not be merged, tagged, frozen, or represented as trusted/canonical while the governing PRE_CERTIFICATION constraints remain in force.

The FirstMate consumer may likewise be implemented on its isolated branch, but must not be production-enabled until rebased and requalified against the settled FirstMate watcher/test surface.
