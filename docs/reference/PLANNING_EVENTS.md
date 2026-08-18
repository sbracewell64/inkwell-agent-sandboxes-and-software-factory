# Planning Transition Feed — producer contract (FP-001)

Governing decision: [`../decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`](../decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md)
Increment: [`../increments/FP-001_FIRSTMATE_PLANNING_FEED.md`](../increments/FP-001_FIRSTMATE_PLANNING_FEED.md)
Feed: [`../development/PLANNING_EVENTS.jsonl`](../development/PLANNING_EVENTS.jsonl)
Schema: [`../development/planning_event.schema.json`](../development/planning_event.schema.json)
Executable contract: [`../validation/check_planning_events.py`](../validation/check_planning_events.py)

## The invariant

> **FirstMate consumes typed planning transitions and never derives execution authority from planning prose.**

The feed is a notification index. It is **not** a source of truth. `FUTURE_CANDIDATES.md`,
accepted ADRs, `ROADMAP.md`, and named increment records remain authoritative for their own
facts.

Nothing in this contract authorizes rereading `ROADMAP.md`, `FUTURE_CANDIDATES.md`, or any ADR
to *discover* that something changed. A planning change becomes visible only as a typed record
appended here. A document edit with no corresponding record is not a transition, and a consumer
must not infer one from a diff, a heading, or any prose.

## Authority vs. transport

Two distinct commits exist for every record, and conflating them is the failure this contract
exists to prevent:

| | Commit | Meaning |
|---|---|---|
| **Announced authority** | `source_commit` | The **already-existing** planning commit that established the state change. Immutable, historical. |
| **Transport provenance** | the commit that appends the record | Merely how the notification travelled. Carries no authority. |

`source_commit` is always an ancestor-in-fact of the record that names it. A consumer validates
against `source_commit`, never against the appending commit and never against the current tip.

Because CI and consumers may hold shallow checkouts, each record binds its authority on two
immutable axes: the full 40-hex `source_commit` **and** the full 40-hex Git blob id of every
`authoritative_ref` as it stood at that commit. The blob ids let a reader confirm exact
historical content even when the commit object is not local. Where neither object is present,
that axis is **could-not-observe** — explicitly reported, never silently treated as verified.

## The bootstrap record

The first record is exactly one non-actionable bootstrap snapshot. It establishes current
planning states and the consumer's cursor baseline. It exists so the bridge cannot activate
itself by replaying history.

It is **mechanically** non-actionable, not merely conventionally so:

- `actionability` is fixed to `awareness`;
- it may not carry `item_id`, `from`, `to`, or `increments`;
- the schema forbids those fields and the validator rejects them independently.

There is no field a bootstrap record can carry that names an intake binding. A second bootstrap,
a non-first bootstrap, or an actionable bootstrap is a hard failure.

## Record shape

One canonical JSON object per LF-terminated line. Canonical means compact separators
(`,` / `:`), keys sorted at every level, UTF-8, no BOM, no CR, no blank lines. That exact byte
representation is what keeps a consumer's byte-offset + prefix-SHA-256 cursor stable, so prefix
mutation stays observable.

| Field | Applies to | Rule |
|---|---|---|
| `schema` | all | `sssf-planning-event/v1` |
| `sequence` | all | integer, dense from 1, equal to the record's line number |
| `event_id` | all | `plan-YYYYMMDD-NNNN`, unique and strictly increasing |
| `kind` | all | `bootstrap` or `transition` |
| `source_commit` | all | full lowercase 40-hex commit id |
| `actionability` | all | `awareness` or `engineering` |
| `authoritative_refs` | all | sorted, unique, ≤16 bounded normalized paths under `docs/` |
| `authoritative_blobs` | all | sorted map binding **exactly** those refs to full 40-hex blob ids |
| `states` | bootstrap | sorted `FUT-NNN` → closed-set state, ≤64 entries |
| `item_id`, `from`, `to` | transition | `FUT-NNN` and closed-set states |
| `increments` | `to: ACTIVE` only | sorted, unique, ≤8 increment identities |

Planning states are closed: `EXPLORE`, `PRESERVE`, `CANDIDATE`, `DECIDED`, `SEQUENCED`,
`ACTIVE`, `PROVEN`, plus side exits `DEFERRED`, `REJECTED`, `SUPERSEDED`. Legal edges follow
[`../development/PLANNING_LIFECYCLE.md`](../development/PLANNING_LIFECYCLE.md). `REJECTED` and
`SUPERSEDED` are terminal. `DEFERRED` never silently resumes: re-entry is itself an explicit
transition.

A transition's declared `from` must equal the state the feed itself has already established for
that item, so a stale or replayed record cannot pass. An item the feed has not seen must enter
from `EXPLORE`.

## Actionability

`actionability` is mechanical classification, not a judgement:

- **`awareness`** — every non-`ACTIVE` record. Constraint/knowledge refresh only. No engineering
  task is created from the event. Carrying `increments` here is a hard failure.
- **`engineering`** — `to: ACTIVE` only, and it means **intake eligibility, not execution
  authority**. An `ACTIVE` record must name at least one increment identity and reference that
  increment's record under `docs/increments/`. The consumer still fetches the named increment and
  authoritative documents at the exact `source_commit`, then passes them through ordinary
  admission and classification before any work begins.

`SEQUENCED` is not `ACTIVE`.

## Continuity

The feed is append-only. Already-published bytes never change. Truncation, replacement, or an
in-place edit of any published byte is a continuity failure the consumer must surface rather than
silently rebase, and it must never advance its cursor across one.

The producer validator checks current bytes against the feed as it stands at the accepted
baseline — the merge-base with the default branch. While the feed is unpublished (no feed exists
at that baseline) the comparison is reported as **`unpublished`**, which is a stated third value,
not a pass. Prefix-mutation detection itself is proven independently by deterministic controls
over synthetic published/current byte pairs, so the guarantee does not depend on the branch
happening to have history.

Pre-publication rewrites of an unpublished feed are legitimate and are not continuity failures;
once a baseline exists, any mutation of those bytes fails closed.

## Running the validator

```bash
python3 docs/validation/check_planning_events.py                       # CI form
python3 docs/validation/check_planning_events.py --require-git-witness  # full-depth qualification
```

| Exit | Meaning |
|---|---|
| 0 | observed-good — every observable axis verified; any unobservable axis reported explicitly |
| 1 | observed-bad — a contract violation was observed |
| 2 | could-not-observe — the feed itself could not be read |

The default form keeps unresolvable git objects as reported could-not-observe axes so a
`fetch-depth: 1` CI checkout is not mistaken for a violation. `--require-git-witness` upgrades
every such axis to a failure and is the form to use when full history is present.

Each run executes the full watched-red matrix in-process and prints one line per control with the
diagnostic it asserted. A control counts only when its mutation produces the *specific* expected
error, so a red caused by unrelated breakage cannot be mistaken for proof. Before any control
runs, the honest feed and an honest multi-record chain must pass under the same code path; if
they do not, the run fails as vacuous rather than reporting reds.

## Appending a record

Browser Sol owns planning promotion and appends the record **after** the authoritative planning
commit already exists.

1. Land the authoritative planning change (candidate register, ADR, roadmap, or increment record).
2. Record that commit's full 40-hex id and the full blob id of each `authoritative_ref` at it
   (`git rev-parse <commit>:<path>`).
3. Append one canonical line with the next `sequence` and a strictly greater `event_id`.
4. Run the validator with `--require-git-witness`.

Never rewrite an existing line. Never reorder. Never remove.

FirstMate does not append to this feed, does not promote planning states, and does not edit
Browser-Sol-owned planning documents because it observed an event.
