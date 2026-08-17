# Field-Level Record Authority

## Scope

HD-13 assigns exactly one **authority** and exactly one **mutation owner** to every field of
every SSSF record surface, and supplies a deterministic validator for two assertions: read-only
surfaces cannot mutate, and only the archive route can change triage state.

This is a documentation and validation increment. It changes no write path. The tracer's local
contract comment is corrected, while runtime behavior and write paths were found correct and remain
unchanged. Other stale local comments are corrected to point back to this contract.

The sole executable owner of the matrix is `tools/sqlite_authority.py`. The table below is
generated from that module; do not hand-edit it.

## What was wrong

The observability reference and the root architecture document presented the trace database as a
derived copy of the run's files, and told the reader that destroying it cost them nothing. The code
says otherwise, and code outranks narrative documentation (`SOURCE_OF_TRUTH.md`). The exact
superseded sentences are retained in this increment's watched-red evidence capture,
`docs/evidence/hd13/documentation-claims-red.txt`, and in the validator's own controls, so the
correction can be audited against what actually shipped.

The tracer appends every **event** to both `events.jsonl` and SQLite. Nothing else is dual-written:

- `sessions` — status, engineer, start/end, `adw_name` and the archived flag exist only in SQLite;
- `phases` — `seq`, `attempt` and `retries` exist only in SQLite;
- `processes` — no file counterpart at all, so a hung run's pid is unrecoverable;
- `envelopes` — every attempt is stored, but `envelope.json` is written only for a **valid**
  envelope and is overwritten, so invalid attempts exist only in SQLite;
- `agent_sessions` — `agent_map.json` carries resume identity only; lane colour, context
  occupancy and timestamps exist only in SQLite;
- `sessions.total_tokens` / `total_cost` — accumulated in SQLite, only partially derivable.

The smallest counterfactual: delete the database after an invalid-envelope or gate attempt, and no
file necessarily reconstructs the phase, gate, process or session canonical row.

The root architecture document additionally proposed, as future work, the Python-only host
observability path that B3-004 had already shipped.

## What was already correct and is preserved

- `tools/obs_query.py` opens a `mode=ro` URI, sets `PRAGMA query_only=ON`, parameterises every
  ADW ID, and refuses to create a missing database.
- The visualizer opens its read connection `readonly: true` and isolates its single write —
  `POST /api/sessions/:adw_id/archive` — as a human triage action on one column.
- `events.jsonl` and the raw Pi files are valuable **raw sources**. They are simply not sufficient
  to reconstruct every canonical fact.

## The six authority classes

| Class | What it holds | Mutation |
|---|---|---|
| `raw-transport` | Append-only or overwrite-style files written as the run happens | The producing module only |
| `canonical-run-state` | The SQLite rows that define what the run did | `adws/adw_modules/tracer.py` only |
| `query-projection` | Values computed per read from canonical rows | **None.** Nothing is written back |
| `triage-state` | `sessions.archived` — "a human has looked at this run" | The archive route only |
| `archived-evidence-copy` | Frozen, hash-bound evidence copies (HD-08) | **None.** A correction is a new manifest |
| `lifecycle-run-record` | Sandbox lifecycle state across the six phase processes | `sandbox_mount/host/run_record.py` only |

The four duties the increment must keep apart are held by four different owners:

- **observation** — `tools/obs_query.py` and the visualizer read connection: no mutation owner;
- **triage** — the archive route: `sessions.archived` and nothing else;
- **archive / evidence copy** — `tools/evidence_manifest.py`: frozen bytes, never rewritten;
- **run-state mutation** — `adws/adw_modules/tracer.py`: every other SQLite column.

Archiving never changes terminal acceptance or evidence hashes. It sets one integer on one session
row. `phases.status`, `gate_results.outcome`, the run's exit code, and every manifest `sha256`
are outside its reach, and the validator proves it by comparing every cell of every table across
an archive write.

## Raw source

`raw_source` answers one operational question per field: **if the trace database is destroyed, what
file still carries this fact?**

- `none` — nothing does. Deleting the database destroys it.
- `complete:<file>` — the file carries the field field-for-field.
- `partial:<file>` — the file carries it only under stated conditions, or lossily. This is a
  source, not a reconstruction.

`sssf.db` is therefore **canonical run state, not a rebuildable mirror**. Rebuilding it from files
recovers events and little else.

## Observing a database

```text
python3 tools/sqlite_authority.py observe --db adws/adw_data/sssf.db
```

Three-valued, using the vocabulary stabilised by the offline evidence manifest core (HD-08):

- `observed-good` — every table and column present is declared, and the database holds canonical
  session rows;
- `observed-bad` — a contradiction: a table or column that has no authority and no mutation owner;
- `could-not-observe` (CNO) — the database is missing, zero bytes, unreadable, schema-less, or
  holds no session rows.

**A missing or empty database is could-not-observe.** It is not an empty result and it is not a
pass. Exit codes are `0` observed-good, `1` observed-bad, `2` CNO; callers must read the printed
observation and must never collapse CNO into PASS or FAIL.

**Precedence is fixed:** observed-bad outranks CNO, which outranks observed-good. Every
contradiction reachable without opening the file is still reported when the file cannot be read, so
an unreadable database never masks a real violation it would otherwise have revealed.

## The visualizer read surface is executed, not inspected

The visualizer's reader is TypeScript, so the stdlib validator cannot run it. Asserting a
read-only property from source bytes would be reading the construction site instead of running the
thing, so the surface is genuinely executed:

`docs/validation/exercise_visualizer_read_surface.ts` runs under Bun against a fixture built from
the tracer's real DDL. It calls every public read method on the real `SssfDb`, then attempts a
mutation through the very connection those methods used, and requires two properties: the fixture's
whole-file digest is unchanged, and the mutation **fails**. An exercise that only showed the surface
running would prove nothing about read-only-ness, so the refused mutation is mandatory.

The exercise records the exact SHA-256 of the TypeScript it executed, into
`docs/evidence/hd13/visualizer-read-surface-exercise.json`.

**The stdlib check binds that record to the bytes present now.** It cannot execute TypeScript, but
it can establish whether the TypeScript has changed since it was last actually exercised — and
comparing digests needs no Bun. A single changed byte in `db.ts` or `index.ts` without a re-run
fails the check with both digests printed. This is what keeps a separately-run control from decaying
into a claim about source that has since moved.

So the CI result lets a reader establish, without Bun:

- **which** bytes were executed — both source digests are printed on success;
- **when**, and by what — the Bun version, script and timestamp are printed;
- **that the current bytes are those bytes** — otherwise the check is red.

The passing output states plainly that this check did **not** execute the read surface, so the
stdlib check alone cannot be mistaken for proof that it was exercised. The recorded exercise is that
proof; the check proves the proof still applies.

An absent or unreadable exercise record is **could-not-observe** — never a pass, and never confused
with a record showing the surface mutating, which is observed-bad.

## Commands

```text
python3 tools/sqlite_authority.py matrix
python3 tools/sqlite_authority.py render
python3 tools/sqlite_authority.py observe --db <path>
python3 docs/validation/check_sqlite_authority.py
python3 docs/validation/check_sqlite_authority.py --controls
python3 docs/validation/check_sqlite_authority.py --exercise-visualizer [--bun <path>]
```

Only `--exercise-visualizer` needs Bun, and it is not the CI entry point: the registered check stays
stdlib-only, because a check that cannot run is worth less than a weaker check that does. Re-run the
exercise whenever the visualizer server sources change; the check will tell you when that is.

Bun is not necessarily on `PATH`. When needed, install the CI-pinned version with
`npm install bun@1.3.14`, then pass `node_modules/.bin/bun` with `--bun`. Without Bun, a validation
run verifies the retained exercise's binding to the current sources rather than re-executing the
read surface; its output states which mode ran. Re-execution is required only when the bound
visualizer server sources change, which the check reports precisely.

`--controls` prints what each negative control observed, so the record shows the controls are
red-capable rather than merely asserting it.

## Known limit: retained historical claim

`specs/scaffold.md` is generated history produced by a factory run. Under
`docs/reference/SOURCE_OF_TRUTH.md` it is evidence, not current runtime authority, and source
custody forbids rewriting it. Its "Two stores, one truth" section still states the superseded
mirror claim. **That section is superseded by this document.** It is deliberately left in place and
is deliberately outside the validator's governed set; the fact is recorded here rather than hidden.

The validator derives its documentation universe from `git ls-files`: every tracked file that is
UTF-8 text-readable is scanned, minus the closed exclusions declared with reasons in
`tools/sqlite_authority.py`. Those exclusions are generated history (`specs/`, `app_docs/`),
watched-red quotations (`docs/evidence/`), and the two source files that necessarily carry the
patterns and controls as data. Re-run the universe enumeration with:

```bash
python3 - <<'PY'
import pathlib, subprocess
excluded = ("specs/", "app_docs/", "docs/evidence/", "tools/sqlite_authority.py",
            "docs/validation/check_sqlite_authority.py")
for raw in subprocess.check_output(["git", "ls-files", "-z"]).split(b"\0"):
    if not raw:
        continue
    relative = raw.decode()
    if any(relative == item or relative.startswith(item) for item in excluded):
        continue
    try:
        pathlib.Path(relative).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        continue
    print(relative)
PY
```

## The matrix

Generated by `python3 tools/sqlite_authority.py render`. The validator requires this block to
appear verbatim.

<!-- BEGIN GENERATED AUTHORITY MATRIX -->

| Store | Record | Field | Authority class | Authority owner | Mutation owner | Raw source |
|---|---|---|---|---|---|---|
| file | `adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` | `agent_name` | raw-transport | `adws/adw_modules/agents.py` | `adws/adw_modules/agents.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` | `attempt` | raw-transport | `adws/adw_modules/agents.py` | `adws/adw_modules/agents.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` | `envelope_body` | raw-transport | `adws/adw_modules/agents.py` | `adws/adw_modules/agents.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` | `output_type` | raw-transport | `adws/adw_modules/agents.py` | `adws/adw_modules/agents.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` | `purpose` | raw-transport | `adws/adw_modules/agents.py` | `adws/adw_modules/agents.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/<agent>/raw_output.jsonl` | `line` | raw-transport | `adws/adw_modules/agent_pi.py` | `adws/adw_modules/agent_pi.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/agent_map.json` | `coding_agent` | raw-transport | `adws/adw_modules/runner.py` | `adws/adw_modules/runner.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/agent_map.json` | `model` | raw-transport | `adws/adw_modules/runner.py` | `adws/adw_modules/runner.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/agent_map.json` | `session_id` | raw-transport | `adws/adw_modules/runner.py` | `adws/adw_modules/runner.py (overwrite)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `adw_id` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `ended_at` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `event_id` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `name` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `parent_id` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `payload` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `phase_id` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `started_at` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `tokens` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `ts` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| file | `adws/adw_data/sessions/<adw_id>/events.jsonl` | `type` | raw-transport | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py (append-only)` | none |
| manifest | `sssf.evidence-manifest.v1` | `inventory` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1` | `purpose` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1` | `repository` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1` | `required_dimensions` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1` | `required_phases` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1` | `run` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1` | `schema_version` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `adw_id` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `artifact_type` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `byte_length` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `claimed_dimensions` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `evidence_class` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `path` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `phase` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `producer` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `purpose` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `run_id` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `sequence` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `sha256` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| manifest | `sssf.evidence-manifest.v1:inventory_item` | `terminal_outcome` | archived-evidence-copy | `tools/evidence_manifest.py` | none (frozen, hash-bound copy) | none |
| projection | `obs_query:live-pids` | `kind` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:live-pids` | `pid` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:phases` | `attempt` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:phases` | `kind` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:phases` | `name` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:phases` | `owner` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:phases` | `seq` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:phases` | `status` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:procs` | `command` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:procs` | `kind` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:procs` | `name` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:procs` | `pid` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:procs` | `started_at` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:sessions` | `adw_id` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:sessions` | `request` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:sessions` | `status` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:sessions` | `total_cost` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:sessions` | `total_tokens` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:tail` | `name` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:tail` | `rowid` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:tail` | `started_at` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `obs_query:tail` | `type` | query-projection | `tools/obs_query.py` | none (read-only projection) | none |
| projection | `visualizer:derived` | `agents` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `cursor` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `has_more` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `journal_mode` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `phase_count` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `phases` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `session_count` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `usage.read` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| projection | `visualizer:derived` | `usage.written` | query-projection | `.claude/skills/sssf/apps/visualizer/server/db.ts` | none (read-only projection) | none |
| run-record | `.sandbox/runs/<run_id>.json` | `closed_at` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `commit_sha` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `created_at` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `https_url` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `key_hash` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `limit` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `pid` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `ports` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `run_id` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `session_id` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `source_repo` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `source_sha` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `spend` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| run-record | `.sandbox/runs/<run_id>.json` | `vm_name` | lifecycle-run-record | `sandbox_mount/host/run_record.py` | `sandbox_mount/host/run_record.py` | none |
| sqlite | `agent_sessions` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/agent_map.json` |
| sqlite | `agent_sessions` | `agent` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/agent_map.json` |
| sqlite | `agent_sessions` | `coding_agent` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/agent_map.json` |
| sqlite | `agent_sessions` | `color` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `agent_sessions` | `context_tokens` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `agent_sessions` | `context_window` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `agent_sessions` | `created_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `agent_sessions` | `last_used_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `agent_sessions` | `model` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/agent_map.json` |
| sqlite | `agent_sessions` | `session_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/agent_map.json` |
| sqlite | `envelopes` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` |
| sqlite | `envelopes` | `agent` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` |
| sqlite | `envelopes` | `attempt` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` |
| sqlite | `envelopes` | `created_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `envelopes` | `envelope_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `envelopes` | `output_type` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` |
| sqlite | `envelopes` | `payload_json` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/<agent>/envelope.json` |
| sqlite | `envelopes` | `phase_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `envelopes` | `valid` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `events` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `ended_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `event_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `name` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `parent_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `payload_json` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `phase_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `started_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `tokens` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `events` | `type` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `attempt` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `checks_json` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `cno_reason` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `cno_source` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `created_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `gate` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `gate_results` | `nonempty_required` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `outcome` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `passed` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `gate_results` | `phase_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `gate_results` | `violations_json` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `complete:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `attempt` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `phases` | `description` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `ended_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `error` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `kind` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `name` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `owner` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `phase_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `retries` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `phases` | `seq` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `phases` | `started_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `phases` | `status` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `processes` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `command` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `ended_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `kind` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `name` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `pid` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `processes` | `started_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `sessions` | `adw_id` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `sessions` | `adw_name` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `sessions` | `archived` | triage-state | `.claude/skills/sssf/apps/visualizer/server/db.ts` | `POST /api/sessions/:adw_id/archive -> db.ts setArchived` | none |
| sqlite | `sessions` | `ended_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `sessions` | `engineer` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `sessions` | `request` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `sessions` | `started_at` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `sessions` | `status` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | none |
| sqlite | `sessions` | `total_cost` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |
| sqlite | `sessions` | `total_tokens` | canonical-run-state | `adws/adw_modules/tracer.py` | `adws/adw_modules/tracer.py` | `partial:adws/adw_data/sessions/<adw_id>/events.jsonl` |

<!-- END GENERATED AUTHORITY MATRIX -->
