# SSSF Planning Event Contract

Schema: `sssf-planning-event/v1`

This contract defines the machine-readable notification surface used to tell FirstMate that Browser Sol has durably changed SSSF planning state.

The feed is **not** the planning source of truth. The authoritative meaning remains in the planning documents named by each record at the exact `source_commit` and exact Git blob identities recorded for those paths.

## Location

`docs/development/PLANNING_EVENTS.jsonl`

One compact JSON object per line. The file ends with exactly one LF and contains no blank records.

## Historical-source witness

SSSF deterministic CI intentionally checks out the exact candidate at depth 1 and runs its validators offline. A historical `source_commit` is therefore not assumed to be present in the CI object store.

Each event binds historical authority with **both**:

- `source_commit` — the full 40-hex commit that already contains the planning decision/state;
- `authoritative_blobs` — a path-to-40-hex Git blob map that binds every `authoritative_refs` path to its exact bytes at that source commit.

The producer validator can prove the event has a complete, closed immutable witness without changing checkout depth or adding network access to offline CI. FirstMate independently re-observes the exact commit and each exact path through GitHub and requires the returned blob ID to match the event before it accepts the snapshot/transition.

Thus an event does not ask either side to trust a branch name or a later copy of a document.

## Record kinds

### `snapshot`

The first record only.

Required fields, in canonical order:

- `schema`: exactly `sssf-planning-event/v1`;
- `event_id`: ordered unique ID `plan-YYYYMMDD-NNNN`;
- `kind`: `snapshot`;
- `source_commit`: full 40-hex Git commit containing the authoritative planning state;
- `states`: nonempty object mapping `FUT-NNN` IDs to closed planning states;
- `authoritative_refs`: sorted nonempty list of safe `docs/...` file paths;
- `authoritative_blobs`: sorted object whose keys equal `authoritative_refs` exactly and whose values are full 40-hex Git blob IDs;
- `actionability`: exactly `baseline`.

A snapshot establishes the initial consumer cursor and current state map. It is mechanically non-actionable and cannot create engineering work.

There is exactly one snapshot and it must be the first record.

### `transition`

Required fields, in canonical order:

- `schema`;
- `event_id`;
- `kind`: `transition`;
- `item_id`: `FUT-NNN`;
- `from`;
- `to`;
- `source_commit`;
- `authoritative_refs`;
- `authoritative_blobs`;
- `actionability`;
- `increment_id` only when `to` is `ACTIVE`.

The `source_commit` must already contain the authoritative planning change. The later Git commit that appends the notification line is transport provenance, not the authority being announced.

## Closed planning states

Primary lifecycle:

`EXPLORE -> PRESERVE -> CANDIDATE -> DECIDED -> SEQUENCED -> ACTIVE -> PROVEN`

Side states:

- `DEFERRED`
- `REJECTED`
- `SUPERSEDED`

The validator owns the exact legal edge set. It reconciles each transition's `from` value against the state established by the snapshot and earlier transitions.

## Actionability

The mapping is mechanical:

- `snapshot` -> `baseline`;
- transition to `ACTIVE` -> `engineering`;
- every other transition -> `awareness`.

`engineering` means **eligible for normal FirstMate intake**, not executable authority. FirstMate must still fetch the named increment and authoritative refs at `source_commit`, verify their blob identities, and pass the work through ordinary admission/classification.

No planning event can waive tests, validators, independent review, maker/checker separation, expected-head checks, provenance, security constraints, cost constraints, or acceptance criteria.

## `ACTIVE` binding

A transition to `ACTIVE` must name one concrete `increment_id` and must include a corresponding path under `docs/increments/<increment_id>...` in both its reference list and blob map.

The increment identifier is transport metadata that tells FirstMate what bounded work to fetch. It does not replace the increment record.

## Authoritative references

Every reference must:

- be a repository-relative path under `docs/`;
- contain no `.` or `..` traversal component;
- contain no empty path component;
- have exactly one matching entry in `authoritative_blobs`.

The blob map may contain no extra path and no missing path.

FirstMate fetches each file at the exact bound source commit and requires GitHub's observed blob SHA to equal the event witness before using the event semantically.

## Continuity

The producer contract is append-only.

The FirstMate consumer maintains:

- byte offset;
- SHA-256 of the exact prefix through that offset;
- last handled event identity;
- mechanically derived planning-state map;
- exact observed feed commit.

A shorter feed, changed prefix, replacement history, malformed cursor, or ambiguous source identity is a continuity failure. The consumer must not silently reset or rebase the cursor.

## Bootstrap rule

The bridge must not activate itself by replaying historical promotions. The initial snapshot therefore records current planning states including any already-active bridge work and is consumed only as synchronization state.

Only transition records appended **after** that baseline can produce awareness or engineering-intake events.

## Producer/consumer proof split

SSSF producer code proves offline that:

- records are canonical and closed-schema;
- event IDs/order and state transitions are legal;
- source commit and blob IDs are immutable Git-object-shaped identities;
- references and blob-map keys are complete, sorted, path-safe, and one-to-one;
- actionability and ACTIVE/increment bindings are mechanical;
- bootstrap is unique and non-actionable.

FirstMate independently proves online at observation time that:

- `source_commit` exists exactly in the configured repository;
- each authoritative path exists at that commit as a file;
- its observed Git blob ID equals the event's `authoritative_blobs` value;
- the feed prefix still matches its durable cursor.

Neither proof substitutes for the other.

## Authority

Browser Sol owns:

- the planning promotion;
- authoritative planning documents;
- the append of the corresponding transition record after the source commit exists.

SSSF producer code owns deterministic producer-contract validation.

FirstMate code owns polling, exact source re-observation, cursor/prefix continuity, dedupe, mechanical actionability classification, and stale/malformed refusal.

FirstMate does not promote SSSF planning states through this channel.
