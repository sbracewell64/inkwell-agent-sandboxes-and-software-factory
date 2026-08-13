# Observability

## Trace store

SSSF writes runtime trace data to:

`adws/adw_data/sssf.db`

SQLite WAL mode allows readers without blocking writers.

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

## Baseline limitation

The Windows host invocation of `just obs sessions` failed because the host did not have a `sqlite3` CLI installed.

This does not invalidate the sandbox trace DB; it is a host tooling gap.

A later increment should either:

1. install a supported SQLite CLI on Windows, or
2. make the host `obs` recipes query SQLite through Python so no external CLI is required.

Option 2 better matches portability goals because Python/uv is already a required tool.
