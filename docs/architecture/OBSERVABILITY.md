# Observability

## Trace store

SSSF writes runtime trace data to:

`adws/adw_data/sssf.db`

SQLite WAL mode allows readers without blocking writers.

## Authority

`sssf.db` holds **canonical run state**. It is not a mirror of the run's files and it is not
rebuildable from them.

The tracer appends every **event** to both `events.jsonl` and SQLite. Session, phase, process, gate,
invalid-envelope, usage and agent-session rows are SQLite-only or only partially represented by
overwrite-style files. Delete the database after an invalid-envelope or gate attempt and no file
necessarily reconstructs the phase, gate, process or session canonical row.

`events.jsonl` and the raw Pi output remain valuable **raw sources**; they are simply not sufficient
to reconstruct every canonical fact.

Every table and field has exactly one authority and one mutation owner, recorded in
`../reference/SQLITE_AUTHORITY.md` and owned executably by `tools/sqlite_authority.py`. Read that
before deleting, rebuilding, relocating or archiving a trace database.

## What should be observable

At minimum:

- ADW session identity/status,
- phase sequence and status,
- agent ownership/model,
- complete agent events/tool calls where recorded,
- typed envelopes,
- token/cost accounting,
- deterministic command results,
- final acceptance.

## Read surfaces

- `just obs sessions`
- `just obs phases <adw_id>`
- `just obs tail <adw_id>`
- visualizer UI on port 4600 inside the mounted sandbox

Read surfaces do not mutate. `tools/obs_query.py` opens a `mode=ro` URI, sets `PRAGMA
query_only=ON`, parameterises every ADW ID, and refuses to create a missing database. The visualizer
opens its read connection `readonly: true`.

The one exception is review triage: `POST /api/sessions/:adw_id/archive` sets `sessions.archived`
and nothing else. Archiving is a human's "I have looked at this run". It never changes terminal
acceptance, run state, or evidence hashes, and no tracer reads or writes it.

## Observing a database

```text
python3 tools/sqlite_authority.py observe --db adws/adw_data/sssf.db
```

A missing, zero-byte, unreadable, schema-less or row-less database is **could-not-observe** — not an
empty result and not a pass. Observed-bad outranks could-not-observe, which outranks observed-good,
so an unreadable database never masks a violation it would otherwise have revealed.

## Host tooling

The host observability path requires no external `sqlite3` CLI: the `obs` recipes query the trace
database through Python's standard-library `sqlite3` (`tools/obs_query.py`). This closed the B3-001
Windows host gap and is proven by `docs/validation/check_obs_query.py`.
