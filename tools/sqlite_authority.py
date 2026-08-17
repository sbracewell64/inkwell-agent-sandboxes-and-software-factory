"""Field-level authority matrix for SSSF record surfaces, plus three-valued observation.

This module is the sole executable owner of the answer to two questions:

1. for every record surface field, which single component is its AUTHORITY and
   which single component may MUTATE it;
2. whether a given trace database can be observed at all.

The matrix exists because the trace database is not a rebuildable mirror of the
run's files. Events are appended to both `events.jsonl` and SQLite, but session,
phase, process, gate, invalid-envelope, usage and agent-session facts are SQLite
canonical run state that no file necessarily reconstructs. An operator who
deletes or rebuilds `sssf.db` believing the files are canonical destroys those
rows. `raw_source` records that fact per field.

Terminology is consumed from the offline evidence manifest core (HD-08) rather
than reinvented: observations are `observed-good`, `observed-bad`, and
`could-not-observe` (CNO); CLI exit codes are 0, 1, and 2; canonical JSON bytes
are sorted-key UTF-8 with no insignificant whitespace and one final LF.

Observation precedence is fixed and never rounded: observed-bad outranks CNO,
which outranks observed-good. A missing or empty database is CNO, never an empty
PASS, and an unreadable database never masks a contradiction it would otherwise
have revealed -- every contradiction reachable without opening the file is still
reported.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any

# ── vocabulary ───────────────────────────────────────────────────────────────

STORES = ("sqlite", "file", "projection", "manifest", "run-record")

AUTHORITY_CLASSES = (
    "raw-transport",
    "canonical-run-state",
    "query-projection",
    "triage-state",
    "archived-evidence-copy",
    "lifecycle-run-record",
)

# A field's raw_source answers "if the trace database is destroyed, what file
# still carries this fact?". `none` is the honest answer for canonical run state
# that only SQLite holds. `partial:` means a file carries it only under stated
# conditions or lossily, so it is not a reconstruction.
RAW_SOURCE_NONE = "none"
RAW_SOURCE_PREFIXES = ("complete:", "partial:")

OBSERVATIONS = ("observed-good", "observed-bad", "could-not-observe")

CNO_REASONS = (
    "DATABASE_ABSENT",
    "DATABASE_EMPTY",
    "DATABASE_UNREADABLE",
    "SCHEMA_ABSENT",
    "NO_CANONICAL_ROWS",
    "FIELD_ABSENT",
)

CONTRADICTION_REASONS = (
    "UNDECLARED_TABLE",
    "UNDECLARED_FIELD",
)

# ── owners ───────────────────────────────────────────────────────────────────

TRACER = "adws/adw_modules/tracer.py"
RUNNER = "adws/adw_modules/runner.py"
AGENTS = "adws/adw_modules/agents.py"
AGENT_PI = "adws/adw_modules/agent_pi.py"
OBS_QUERY = "tools/obs_query.py"
VISUALIZER_DB = ".claude/skills/sssf/apps/visualizer/server/db.ts"
VISUALIZER_SERVER = ".claude/skills/sssf/apps/visualizer/server/index.ts"
ARCHIVE_ROUTE = "POST /api/sessions/:adw_id/archive -> db.ts setArchived"
MANIFEST_OWNER = "tools/evidence_manifest.py"
RUN_RECORD_OWNER = "sandbox_mount/host/run_record.py"

# Read surfaces have no mutation owner at all. This is the whole point of the
# class: a projection is computed from canonical rows on every read and is never
# written back, so there is nothing for a mutation owner to own.
NO_MUTATION = "none (read-only projection)"

# Archived evidence copies are frozen bytes bound to a SHA-256. Nothing may
# rewrite them in place; a correction is a new manifest, not an edit.
NO_MUTATION_FROZEN = "none (frozen, hash-bound copy)"

EVENTS_JSONL = "adws/adw_data/sessions/<adw_id>/events.jsonl"
RAW_OUTPUT_JSONL = "adws/adw_data/sessions/<adw_id>/<agent>/raw_output.jsonl"
ENVELOPE_JSON = "adws/adw_data/sessions/<adw_id>/<agent>/envelope.json"
AGENT_MAP_JSON = "adws/adw_data/sessions/<adw_id>/agent_map.json"
RUN_RECORD_JSON = ".sandbox/runs/<run_id>.json"

_EVENTS = f"complete:{EVENTS_JSONL}"
_EVENTS_PART = f"partial:{EVENTS_JSONL}"
_ENVELOPE_PART = f"partial:{ENVELOPE_JSON}"
_AGENT_MAP = f"complete:{AGENT_MAP_JSON}"
_AGENT_MAP_PART = f"partial:{AGENT_MAP_JSON}"

# ── the matrix ───────────────────────────────────────────────────────────────
#
# One record group per surface. Every field carries exactly one authority class,
# one authority owner, one mutation owner, and one raw_source. `overrides` exist
# so a single field can leave its group's class without splitting the group --
# `sessions.archived` is triage state living on a canonical run-state row.

RECORDS: tuple[dict[str, Any], ...] = (
    {
        "store": "sqlite",
        "record": "sessions",
        # One row per ADW run. Only `archived` is not run state.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "adw_id": _EVENTS_PART,
            "adw_name": RAW_SOURCE_NONE,
            "request": _EVENTS_PART,
            "status": RAW_SOURCE_NONE,
            "engineer": RAW_SOURCE_NONE,
            "started_at": RAW_SOURCE_NONE,
            "ended_at": RAW_SOURCE_NONE,
            "total_tokens": _EVENTS_PART,
            "total_cost": _EVENTS_PART,
            "archived": RAW_SOURCE_NONE,
        },
        "overrides": {
            "archived": {
                "authority_class": "triage-state",
                "authority_owner": VISUALIZER_DB,
                "mutation_owner": ARCHIVE_ROUTE,
            },
        },
    },
    {
        "store": "sqlite",
        "record": "phases",
        # Canonical phase sequence. `seq`, `attempt` and `retries` exist nowhere else.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "phase_id": _EVENTS_PART,
            "adw_id": _EVENTS_PART,
            "seq": RAW_SOURCE_NONE,
            "name": _EVENTS_PART,
            "kind": _EVENTS_PART,
            "owner": _EVENTS_PART,
            "description": _EVENTS_PART,
            "status": _EVENTS_PART,
            "attempt": RAW_SOURCE_NONE,
            "retries": RAW_SOURCE_NONE,
            "error": _EVENTS_PART,
            "started_at": _EVENTS_PART,
            "ended_at": _EVENTS_PART,
        },
    },
    {
        "store": "sqlite",
        "record": "events",
        # The one table the tracer dual-writes field-for-field to JSONL.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "event_id": _EVENTS,
            "adw_id": _EVENTS,
            "phase_id": _EVENTS,
            "parent_id": _EVENTS,
            "type": _EVENTS,
            "name": _EVENTS,
            "payload_json": _EVENTS,
            "tokens": _EVENTS,
            "started_at": _EVENTS,
            "ended_at": _EVENTS,
        },
    },
    {
        "store": "sqlite",
        "record": "envelopes",
        # Every attempt, valid or not. `envelope.json` holds only the last valid one.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "envelope_id": RAW_SOURCE_NONE,
            "adw_id": _ENVELOPE_PART,
            "phase_id": RAW_SOURCE_NONE,
            "agent": _ENVELOPE_PART,
            "output_type": _ENVELOPE_PART,
            "payload_json": _ENVELOPE_PART,
            "valid": RAW_SOURCE_NONE,
            "attempt": _ENVELOPE_PART,
            "created_at": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "sqlite",
        "record": "gate_results",
        # Typed gate verdicts. `passed` is a stored compatibility projection of `outcome`.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "id": RAW_SOURCE_NONE,
            "adw_id": _EVENTS,
            "phase_id": _EVENTS,
            "attempt": _EVENTS,
            "gate": _EVENTS,
            "passed": RAW_SOURCE_NONE,
            "outcome": _EVENTS,
            "cno_reason": _EVENTS,
            "cno_source": _EVENTS,
            "nonempty_required": _EVENTS,
            "violations_json": _EVENTS,
            "checks_json": _EVENTS,
            "created_at": _EVENTS_PART,
        },
    },
    {
        "store": "sqlite",
        "record": "processes",
        # No file counterpart at all. A hung run's pid exists only here.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "id": RAW_SOURCE_NONE,
            "adw_id": RAW_SOURCE_NONE,
            "kind": RAW_SOURCE_NONE,
            "name": RAW_SOURCE_NONE,
            "pid": RAW_SOURCE_NONE,
            "command": RAW_SOURCE_NONE,
            "started_at": RAW_SOURCE_NONE,
            "ended_at": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "sqlite",
        "record": "agent_sessions",
        # `agent_map.json` carries resume identity only; the rest is SQLite-only.
        "authority_class": "canonical-run-state",
        "authority_owner": TRACER,
        "mutation_owner": TRACER,
        "fields": {
            "adw_id": _AGENT_MAP_PART,
            "agent": _AGENT_MAP,
            "coding_agent": _AGENT_MAP,
            "model": _AGENT_MAP,
            "color": RAW_SOURCE_NONE,
            "session_id": _AGENT_MAP,
            "context_tokens": _EVENTS_PART,
            "context_window": _EVENTS_PART,
            "created_at": RAW_SOURCE_NONE,
            "last_used_at": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "file",
        "record": EVENTS_JSONL,
        # Append-only raw transport. Sufficient for events; for nothing else.
        "authority_class": "raw-transport",
        "authority_owner": TRACER,
        "mutation_owner": f"{TRACER} (append-only)",
        "fields": {
            "event_id": RAW_SOURCE_NONE,
            "ts": RAW_SOURCE_NONE,
            "adw_id": RAW_SOURCE_NONE,
            "phase_id": RAW_SOURCE_NONE,
            "parent_id": RAW_SOURCE_NONE,
            "type": RAW_SOURCE_NONE,
            "name": RAW_SOURCE_NONE,
            "payload": RAW_SOURCE_NONE,
            "tokens": RAW_SOURCE_NONE,
            "started_at": RAW_SOURCE_NONE,
            "ended_at": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "file",
        "record": RAW_OUTPUT_JSONL,
        # The coding agent's own stream. Never parsed into canonical rows.
        "authority_class": "raw-transport",
        "authority_owner": AGENT_PI,
        "mutation_owner": f"{AGENT_PI} (append-only)",
        "fields": {
            "line": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "file",
        "record": ENVELOPE_JSON,
        # Overwrite-style: only the last VALID envelope per agent survives.
        "authority_class": "raw-transport",
        "authority_owner": AGENTS,
        "mutation_owner": f"{AGENTS} (overwrite)",
        "fields": {
            "agent_name": RAW_SOURCE_NONE,
            "purpose": RAW_SOURCE_NONE,
            "output_type": RAW_SOURCE_NONE,
            "attempt": RAW_SOURCE_NONE,
            "envelope_body": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "file",
        "record": AGENT_MAP_JSON,
        # Overwrite-style resume key, one entry per agent.
        "authority_class": "raw-transport",
        "authority_owner": RUNNER,
        "mutation_owner": f"{RUNNER} (overwrite)",
        "fields": {
            "session_id": RAW_SOURCE_NONE,
            "model": RAW_SOURCE_NONE,
            "coding_agent": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "projection",
        "record": "obs_query:sessions",
        # Read-only. Opens mode=ro with query_only=ON and refuses to create a database.
        "authority_class": "query-projection",
        "authority_owner": OBS_QUERY,
        "mutation_owner": NO_MUTATION,
        "fields": {
            "adw_id": RAW_SOURCE_NONE,
            "status": RAW_SOURCE_NONE,
            "request": RAW_SOURCE_NONE,
            "total_tokens": RAW_SOURCE_NONE,
            "total_cost": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "projection",
        "record": "obs_query:phases",
        "authority_class": "query-projection",
        "authority_owner": OBS_QUERY,
        "mutation_owner": NO_MUTATION,
        "fields": {
            "seq": RAW_SOURCE_NONE,
            "name": RAW_SOURCE_NONE,
            "kind": RAW_SOURCE_NONE,
            "owner": RAW_SOURCE_NONE,
            "status": RAW_SOURCE_NONE,
            "attempt": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "projection",
        "record": "obs_query:tail",
        "authority_class": "query-projection",
        "authority_owner": OBS_QUERY,
        "mutation_owner": NO_MUTATION,
        "fields": {
            "rowid": RAW_SOURCE_NONE,
            "type": RAW_SOURCE_NONE,
            "name": RAW_SOURCE_NONE,
            "started_at": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "projection",
        "record": "obs_query:procs",
        "authority_class": "query-projection",
        "authority_owner": OBS_QUERY,
        "mutation_owner": NO_MUTATION,
        "fields": {
            "kind": RAW_SOURCE_NONE,
            "name": RAW_SOURCE_NONE,
            "pid": RAW_SOURCE_NONE,
            "command": RAW_SOURCE_NONE,
            "started_at": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "projection",
        "record": "obs_query:live-pids",
        "authority_class": "query-projection",
        "authority_owner": OBS_QUERY,
        "mutation_owner": NO_MUTATION,
        "fields": {
            "kind": RAW_SOURCE_NONE,
            "pid": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "projection",
        "record": "visualizer:derived",
        # Computed per request from canonical rows; never written back.
        "authority_class": "query-projection",
        "authority_owner": VISUALIZER_DB,
        "mutation_owner": NO_MUTATION,
        "fields": {
            "phase_count": RAW_SOURCE_NONE,
            "phases": RAW_SOURCE_NONE,
            "agents": RAW_SOURCE_NONE,
            "usage.read": RAW_SOURCE_NONE,
            "usage.written": RAW_SOURCE_NONE,
            "cursor": RAW_SOURCE_NONE,
            "has_more": RAW_SOURCE_NONE,
            "journal_mode": RAW_SOURCE_NONE,
            "session_count": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "manifest",
        "record": "sssf.evidence-manifest.v1",
        # HD-08 offline evidence manifest. Frozen bytes; no runtime acceptance authority.
        "authority_class": "archived-evidence-copy",
        "authority_owner": MANIFEST_OWNER,
        "mutation_owner": NO_MUTATION_FROZEN,
        "fields": {
            "schema_version": RAW_SOURCE_NONE,
            "repository": RAW_SOURCE_NONE,
            "run": RAW_SOURCE_NONE,
            "purpose": RAW_SOURCE_NONE,
            "required_phases": RAW_SOURCE_NONE,
            "required_dimensions": RAW_SOURCE_NONE,
            "inventory": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "manifest",
        "record": "sssf.evidence-manifest.v1:inventory_item",
        "authority_class": "archived-evidence-copy",
        "authority_owner": MANIFEST_OWNER,
        "mutation_owner": NO_MUTATION_FROZEN,
        "fields": {
            "sequence": RAW_SOURCE_NONE,
            "path": RAW_SOURCE_NONE,
            "artifact_type": RAW_SOURCE_NONE,
            "byte_length": RAW_SOURCE_NONE,
            "sha256": RAW_SOURCE_NONE,
            "producer": RAW_SOURCE_NONE,
            "run_id": RAW_SOURCE_NONE,
            "adw_id": RAW_SOURCE_NONE,
            "phase": RAW_SOURCE_NONE,
            "purpose": RAW_SOURCE_NONE,
            "terminal_outcome": RAW_SOURCE_NONE,
            "evidence_class": RAW_SOURCE_NONE,
            "claimed_dimensions": RAW_SOURCE_NONE,
        },
    },
    {
        "store": "run-record",
        "record": RUN_RECORD_JSON,
        # Sandbox lifecycle state shared across the six phase processes. Not run state.
        "authority_class": "lifecycle-run-record",
        "authority_owner": RUN_RECORD_OWNER,
        "mutation_owner": RUN_RECORD_OWNER,
        "fields": {
            "run_id": RAW_SOURCE_NONE,
            "vm_name": RAW_SOURCE_NONE,
            "https_url": RAW_SOURCE_NONE,
            "key_hash": RAW_SOURCE_NONE,
            "limit": RAW_SOURCE_NONE,
            "spend": RAW_SOURCE_NONE,
            "session_id": RAW_SOURCE_NONE,
            "source_repo": RAW_SOURCE_NONE,
            "source_sha": RAW_SOURCE_NONE,
            "commit_sha": RAW_SOURCE_NONE,
            "ports": RAW_SOURCE_NONE,
            "pid": RAW_SOURCE_NONE,
            "created_at": RAW_SOURCE_NONE,
            "closed_at": RAW_SOURCE_NONE,
        },
    },
)

# Refuted documentation claims. Each is observed-bad wherever a governed
# document states it, because the code says otherwise.
REFUTED_CLAIMS: tuple[dict[str, str], ...] = (
    {
        "id": "queryable-mirror",
        "pattern": r"queryable\s+mirror",
        "why": (
            "the database is not a mirror of the files: session, phase, process, gate, "
            "invalid-envelope, usage and agent-session rows have no file counterpart"
        ),
    },
    {
        "id": "loses-nothing",
        "pattern": r"los(?:e|es|ing)\s+nothing",
        "why": (
            "deleting the database destroys canonical run state that no file reconstructs"
        ),
    },
    {
        "id": "rebuildable-from-files",
        "pattern": r"rebuil\w*\s+from\s+(?:the\s+)?(?:files|`?raw_output\.jsonl`?)",
        "why": "the raw files are sources, not a reconstruction of canonical run state",
    },
    {
        "id": "completed-sqlite-cli-proposal",
        "pattern": (
            r"install\s+a\s+supported\s+SQLite\s+CLI"
            r"|query\s+SQLite\s+through\s+Python\s+so\s+no\s+external\s+CLI"
        ),
        "why": (
            "the Python-only host observability path already shipped in B3-004; "
            "a governed document must not propose a fix that is complete"
        ),
    },
    {
        "id": "wholly-read-only-visualizer",
        "pattern": (
            r"read-?only\s+(?:observability\s+)?(?:ui|app|application|server|visualizer|reader)\b"
            r"|(?:visualizer|observability\s+ui)\s+is\s+"
            r"(?:(?:wholly|entirely|completely)\s+)?read-?only\b"
        ),
        "why": (
            "the visualizer is read-only over run and evidence state, but its archive route "
            "owns the sessions.archived triage write"
        ),
    },
)

# Closed exclusions from the git-tracked, text-readable documentation-claim
# universe. Every omission is explicit and carries its source-of-truth reason.
DOCUMENTATION_SCAN_EXCLUSIONS = {
    "specs/": "generated run history under SOURCE_OF_TRUTH; retained, not rewritten",
    "app_docs/": "generated application history under SOURCE_OF_TRUTH; retained, not rewritten",
    "docs/evidence/": "watched-red captures intentionally quote refuted sentences verbatim",
    "tools/sqlite_authority.py": "owns the refuted patterns as executable data",
    "docs/validation/check_sqlite_authority.py": "contains patterns and negative controls as data",
}

# Retained history that is NOT governed: `specs/` is evidence produced by past
# runs, and source custody forbids rewriting it. The superseding statement is
# named in the governed reference instead, and the validator asserts it is there.
RETAINED_HISTORICAL_CLAIM = "specs/scaffold.md"

MATRIX_TABLE_BEGIN = "<!-- BEGIN GENERATED AUTHORITY MATRIX -->"
MATRIX_TABLE_END = "<!-- END GENERATED AUTHORITY MATRIX -->"


# ── projection ───────────────────────────────────────────────────────────────


def matrix() -> list[dict[str, str]]:
    """Flatten RECORDS into one sorted row per field."""
    rows: list[dict[str, str]] = []
    for group in RECORDS:
        overrides = group.get("overrides", {})
        for field, raw_source in group["fields"].items():
            override = overrides.get(field, {})
            rows.append(
                {
                    "store": group["store"],
                    "record": group["record"],
                    "field": field,
                    "authority_class": override.get(
                        "authority_class", group["authority_class"]
                    ),
                    "authority_owner": override.get(
                        "authority_owner", group["authority_owner"]
                    ),
                    "mutation_owner": override.get(
                        "mutation_owner", group["mutation_owner"]
                    ),
                    "raw_source": override.get("raw_source", raw_source),
                }
            )
    rows.sort(key=lambda row: (row["store"], row["record"], row["field"]))
    return rows


def sqlite_fields() -> dict[str, list[str]]:
    """Declared SQLite tables and their declared columns, in declaration order."""
    declared: dict[str, list[str]] = {}
    for group in RECORDS:
        if group["store"] == "sqlite":
            declared[group["record"]] = list(group["fields"])
    return declared


def canonical_json(document: Any) -> str:
    """Canonical UTF-8 JSON bytes as text: sorted keys, no padding, one final LF."""
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def render_table() -> str:
    """The generated Markdown block a governed document must embed verbatim."""
    lines = [
        MATRIX_TABLE_BEGIN,
        "",
        "| Store | Record | Field | Authority class | Authority owner | Mutation owner | Raw source |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in matrix():
        lines.append(
            "| {store} | `{record}` | `{field}` | {authority_class} | `{authority_owner}` "
            "| {mutation_owner} | {raw_source} |".format(
                store=row["store"],
                record=row["record"],
                field=row["field"],
                authority_class=row["authority_class"],
                authority_owner=row["authority_owner"],
                mutation_owner=(
                    row["mutation_owner"]
                    if row["mutation_owner"].startswith("none")
                    else f"`{row['mutation_owner']}`"
                ),
                raw_source=(
                    "none"
                    if row["raw_source"] == RAW_SOURCE_NONE
                    else f"`{row['raw_source']}`"
                ),
            )
        )
    lines.extend(["", MATRIX_TABLE_END])
    return "\n".join(lines) + "\n"


# ── three-valued observation ─────────────────────────────────────────────────


def _reason(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def observe(db_path: Path) -> dict[str, Any]:
    """Observe a trace database against the matrix, three-valued.

    Missing, empty, unreadable, schema-less, and row-less databases are all
    could-not-observe. A table or column the matrix does not declare is a
    contradiction, and a contradiction outranks any absence found alongside it.
    """
    result: dict[str, Any] = {
        "database": str(db_path),
        "observation": "could-not-observe",
        "contradictions": [],
        "absences": [],
        "tables_observed": 0,
        "fields_observed": 0,
        "canonical_rows": 0,
    }
    contradictions: list[dict[str, str]] = result["contradictions"]
    absences: list[dict[str, str]] = result["absences"]

    try:
        resolved = db_path.expanduser().resolve()
    except OSError as exc:
        absences.append(_reason("DATABASE_UNREADABLE", f"path could not be resolved: {exc}"))
        return _settle(result, contradictions, absences)

    if not resolved.is_file():
        absences.append(_reason("DATABASE_ABSENT", f"no regular file at {resolved}"))
        return _settle(result, contradictions, absences)

    if resolved.stat().st_size == 0:
        absences.append(_reason("DATABASE_EMPTY", f"{resolved} is zero bytes"))
        return _settle(result, contradictions, absences)

    try:
        conn = sqlite3.connect(f"{resolved.as_uri()}?mode=ro", uri=True, timeout=5.0)
    except sqlite3.Error as exc:
        absences.append(_reason("DATABASE_UNREADABLE", f"could not open read-only: {exc}"))
        return _settle(result, contradictions, absences)

    try:
        conn.execute("PRAGMA query_only=ON;")
        observed = _observe_open(conn, result, contradictions, absences)
    except sqlite3.Error as exc:
        absences.append(_reason("DATABASE_UNREADABLE", f"read failed: {exc}"))
        observed = False
    finally:
        conn.close()

    if not observed:
        return _settle(result, contradictions, absences)
    return _settle(result, contradictions, absences)


def _observe_open(
    conn: sqlite3.Connection,
    result: dict[str, Any],
    contradictions: list[dict[str, str]],
    absences: list[dict[str, str]],
) -> bool:
    tables = [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    if not tables:
        absences.append(_reason("SCHEMA_ABSENT", "the database declares no user tables"))
        return False

    declared = sqlite_fields()
    result["tables_observed"] = len(tables)
    fields_observed = 0

    for table in tables:
        if table not in declared:
            contradictions.append(
                _reason("UNDECLARED_TABLE", f"table `{table}` has no authority in the matrix")
            )
            continue
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        fields_observed += len(columns)
        for column in columns:
            if column not in declared[table]:
                contradictions.append(
                    _reason(
                        "UNDECLARED_FIELD",
                        f"`{table}.{column}` has no authority and no mutation owner",
                    )
                )
        for column in declared[table]:
            if column not in columns:
                absences.append(
                    _reason("FIELD_ABSENT", f"`{table}.{column}` is declared but not present")
                )

    for table in declared:
        if table not in tables:
            absences.append(_reason("FIELD_ABSENT", f"declared table `{table}` is not present"))

    result["fields_observed"] = fields_observed

    if "sessions" in tables:
        result["canonical_rows"] = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        if result["canonical_rows"] == 0:
            absences.append(
                _reason(
                    "NO_CANONICAL_ROWS",
                    "the database holds no session rows; an empty result is not a pass",
                )
            )
    return True


def _settle(
    result: dict[str, Any],
    contradictions: list[dict[str, str]],
    absences: list[dict[str, str]],
) -> dict[str, Any]:
    if contradictions:
        result["observation"] = "observed-bad"
    elif absences:
        result["observation"] = "could-not-observe"
    else:
        result["observation"] = "observed-good"
    return result


EXIT_CODES = {"observed-good": 0, "observed-bad": 1, "could-not-observe": 2}


# ── CLI ──────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Field-level authority matrix for SSSF record surfaces, and three-valued "
            "observation of a trace database against it."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("matrix", help="Print the canonical JSON matrix projection.")
    sub.add_parser("render", help="Print the generated Markdown matrix block.")
    observe_parser = sub.add_parser(
        "observe",
        help="Observe a trace database: exit 0 observed-good, 1 observed-bad, 2 CNO.",
    )
    observe_parser.add_argument("--db", required=True, help="Trace database path.")
    observe_parser.add_argument(
        "--json", action="store_true", help="Emit the full observation as JSON."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "matrix":
        sys.stdout.write(canonical_json(matrix()))
        return 0

    if args.command == "render":
        sys.stdout.write(render_table())
        return 0

    result = observe(Path(args.db))
    if args.json:
        sys.stdout.write(canonical_json(result))
    else:
        print(f"sqlite-authority: {result['observation']}")
        for reason in result["contradictions"]:
            print(f"- observed-bad {reason['code']}: {reason['detail']}")
        for reason in result["absences"]:
            print(f"- could-not-observe {reason['code']}: {reason['detail']}")
    return EXIT_CODES[result["observation"]]


if __name__ == "__main__":
    raise SystemExit(main())
