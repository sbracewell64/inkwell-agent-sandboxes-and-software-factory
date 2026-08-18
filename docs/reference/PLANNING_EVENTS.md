# SSSF Planning Event Contract

Schema: `sssf-planning-event/v1`

This contract defines the machine-readable notification surface used to tell FirstMate that Browser Sol has durably changed SSSF planning state.

The feed is **not** the planning source of truth. The authoritative meaning remains in the planning documents named by each record at the exact `source_commit`.

## Location

`docs/development/PLANNING_EVENTS.jsonl`

One compact JSON object per line. The file ends with exactly one LF and contains no blank records.

## Record kinds

### `snapshot`

The first record only.

Required fields:

- `schema`: exactly `sssf-planning-event/v1`;
- `event_id`: ordered unique ID `plan-YYYYMMDD-NNNN`;
- `kind`: `snapshot`;
- `source_commit`: full 40-hex Git commit containing the authoritative planning state;
- `states`: nonempty object mapping `FUT-NNN` IDs to closed planning states;
- `authoritative_refs`: nonempty list of safe `docs/...` file paths that exist at `source_commit`;
- `actionability`: exactly `baseline`.

A snapshot establishes the initial consumer cursor and current state map. It is mechanically non-actionable and cannot create engineering work.

There is exactly one snapshot and it must be the first record.

### `transition`

Required fields:

- `schema`;
- `event_id`;
- `kind`: `transition`;
- `item_id`: `FUT-NNN`;
- `from`;
- `to`;
- `source_commit`;
- `authoritative_refs`;
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

The validator owns the exact legal edge set. It also reconciles each transition's `from` value against the state established by the snapshot and earlier transitions.

## Actionability

The mapping is mechanical:

- `snapshot` -> `baseline`;
- transition to `ACTIVE` -> `engineering`;
- every other transition -> `awareness`.

`engineering` means **eligible for normal FirstMate intake**, not executable authority. FirstMate must still fetch the named increment and authoritative refs at `source_commit` and pass the work through ordinary admission/classification.

No planning event can waive tests, validators, independent review, maker/checker separation, expected-head checks, provenance, security constraints, cost constraints, or acceptance criteria.

## `ACTIVE` binding

A transition to `ACTIVE` must name one concrete `increment_id`.

The increment identifier is transport metadata that tells FirstMate what bounded work to fetch. It does not replace the increment record.

## Authoritative references

Every reference must:

- be a repository-relative path under `docs/`;
- contain no `.` or `..` traversal component;
- contain no empty path component;
- identify a regular tracked file at `source_commit`.

Consumers fetch those files at the exact bound source commit before using the event semantically.

## Continuity

The producer contract is append-only.

The FirstMate consumer maintains:

- byte offset;
- SHA-256 of the exact prefix through that offset;
- last handled event identity;
- exact observed repository/ref/commit.

A shorter feed, changed prefix, replacement history, malformed cursor, or ambiguous source identity is a continuity failure. The consumer must not silently reset or rebase the cursor.

## Bootstrap rule

The bridge must not activate itself by replaying historical promotions. The initial snapshot therefore records current planning states including any already-active bridge work and is consumed only as synchronization state.

Only transition records appended **after** that baseline can produce awareness or engineering-intake events.

## Producer/consumer authority

Browser Sol owns:

- the planning promotion;
- authoritative planning documents;
- the append of the corresponding transition record after the source commit exists.

SSSF producer code owns:

- schema validation;
- transition legality;
- provenance-shape/path checks;
- deterministic offline acceptance of feed bytes.

FirstMate code owns:

- polling;
- cursor/prefix continuity;
- dedupe;
- mechanical actionability classification;
- refusing stale or malformed activation.

FirstMate does not promote SSSF planning states through this channel.
