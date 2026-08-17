"""Validate the HD-13 field-level authority matrix and watch each control go red.

Three properties are asserted, never proxied:

1. every declared table and field has exactly one authority and one mutation
   owner, and observation, triage, archive/evidence copy, and run-state mutation
   are held by distinct owners;
2. read-only surfaces cannot mutate -- proven by hashing the whole fixture
   database and dumping every cell before and after every read surface runs,
   then attempting a real write through the real read-only helper;
3. only the archive route can change triage state -- proven by executing the
   archive statement extracted from the visualizer's own bytes and comparing
   every cell of every table.

Each of those has a negative control that must go red, so a green result cannot
come from having attempted nothing. `no error was raised` is never accepted as
evidence: a comparator that cannot detect a real mutation fails this validator.

Stdlib only, offline, no provider call. Nothing here imports the tracer package
(it needs pydantic); the real DDL is read out of the tracer's own source bytes.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import evidence_manifest, obs_query, sqlite_authority  # noqa: E402

# Every path comes from the matrix owner, so a renamed owner cannot leave the
# validator quietly checking a file the matrix no longer names.
TRACER_SOURCE = ROOT / sqlite_authority.TRACER
RUN_RECORD_SOURCE = ROOT / sqlite_authority.RUN_RECORD_OWNER
OBS_QUERY_SOURCE = ROOT / sqlite_authority.OBS_QUERY
VISUALIZER_DB_SOURCE = ROOT / sqlite_authority.VISUALIZER_DB
VISUALIZER_SERVER_SOURCE = ROOT / sqlite_authority.VISUALIZER_SERVER
AUTHORITY_DOC = ROOT / "docs/reference/SQLITE_AUTHORITY.md"

FIXTURE_ADW = "hd13-fixture-adw"

# The exact archive statement the visualizer is allowed to run. It is extracted
# from db.ts rather than retyped, so widening it there widens it here too.
EXPECTED_ARCHIVE_SQL = "UPDATE sessions SET archived = ? WHERE adw_id = ?"

WRITE_VERBS = ("INSERT", "UPDATE", "DELETE", "REPLACE", "DROP", "ALTER", "CREATE")

# The superseded sentences exactly as they stood before this increment. The
# documentation control is calibrated against the text that actually shipped,
# not against a fixture written to make it pass, so it stays red-capable after
# the real documents are corrected.
HISTORICAL_CLAIMS = (
    (
        "queryable-mirror",
        "**Files are the raw record** (`raw_output.jsonl` streams, `envelope.json`, "
        "`agent_map.json`); **SQLite (`sssf.db`) is the queryable mirror** the UI reads. "
        "`tracer.py` writes both. Losing the db loses nothing that can't be rebuilt from files.",
    ),
    (
        "loses-nothing",
        "**Files are the raw record; the db is the queryable mirror.** Losing `sssf.db` loses "
        "nothing that can't be rebuilt from `raw_output.jsonl`, `envelope.json`, and "
        "`agent_map.json`.",
    ),
    (
        "queryable-mirror",
        "`agent_sessions` in `sssf.db` is the queryable mirror of this file.",
    ),
    (
        "queryable-mirror",
        "agent_sessions (                   -- the queryable mirror of agent_map.json",
    ),
    (
        "rebuildable-from-files",
        "Losing the db loses nothing that can't be rebuilt from files.",
    ),
    (
        "rebuildable-from-files",
        "Losing `sssf.db` loses nothing that can't be rebuilt from `raw_output.jsonl`, "
        "`envelope.json`, and `agent_map.json`.",
    ),
    (
        "completed-sqlite-cli-proposal",
        "A later increment should either:\n\n1. install a supported SQLite CLI on Windows, or\n"
        "2. make the host `obs` recipes query SQLite through Python so no external CLI is "
        "required.",
    ),
)


# ── reading the real bytes ───────────────────────────────────────────────────


def module_constants(source: Path, names: tuple[str, ...]) -> dict[str, object]:
    """Literal module-level constants, read without importing (no dependencies)."""
    values: dict[str, object] = {}
    for node in ast.parse(source.read_text(encoding="utf-8")).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or target.id not in names:
            continue
        values[target.id] = ast.literal_eval(node.value)
    return values


def tracer_schema(path: Path) -> dict[str, list[str]]:
    """The tracer's real tables and columns, after its own additive migrations."""
    constants = module_constants(TRACER_SOURCE, ("SCHEMA", "MIGRATIONS"))
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.executescript(str(constants["SCHEMA"]))
    for table, column, decl in constants["MIGRATIONS"]:  # type: ignore[union-attr]
        columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in columns:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
    observed = {
        name: [row[1] for row in conn.execute(f"PRAGMA table_info({name})")]
        for (name,) in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    }
    conn.close()
    return observed


def archive_statements(text: str) -> list[str]:
    """Every SQL string literal in the visualizer reader that writes."""
    literals = re.findall(r'"((?:[^"\\]|\\.)*)"|`((?:[^`\\]|\\.)*)`', text, flags=re.DOTALL)
    found = []
    for double, backtick in literals:
        literal = double or backtick
        stripped = literal.strip()
        if any(stripped.upper().startswith(verb) for verb in WRITE_VERBS):
            found.append(" ".join(stripped.split()))
    return found


# ── fixtures ─────────────────────────────────────────────────────────────────


def populate(path: Path) -> None:
    """One realistic row per canonical table, written through the real DDL."""
    conn = sqlite3.connect(path, isolation_level=None)
    conn.execute(
        "INSERT INTO sessions (adw_id, adw_name, request, status, engineer, started_at,"
        " total_tokens, total_cost, archived) VALUES (?,?,?,?,?,?,?,?,0)",
        (FIXTURE_ADW, "adw_plan", "HD-13 fixture request", "running", "engineer",
         "2026-08-17T12:00:00Z", 123, 0.4567),
    )
    conn.execute(
        "INSERT INTO phases (phase_id, adw_id, seq, name, kind, owner, description, status,"
        " attempt, retries, started_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (f"{FIXTURE_ADW}_01_plan", FIXTURE_ADW, 1, "plan", "agent", "planner", "plan it",
         "success", 1, 2, "2026-08-17T12:00:01Z"),
    )
    conn.execute(
        "INSERT INTO events (event_id, adw_id, phase_id, parent_id, type, name, payload_json,"
        " tokens, started_at) VALUES (?,?,?,?,?,?,?,?,?)",
        ("evt_hd13", FIXTURE_ADW, f"{FIXTURE_ADW}_01_plan", "", "phase_start", "plan",
         '{"kind": "agent"}', 10, "2026-08-17T12:00:01Z"),
    )
    conn.execute(
        "INSERT INTO envelopes (envelope_id, adw_id, phase_id, agent, output_type,"
        " payload_json, valid, attempt, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        ("env_hd13", FIXTURE_ADW, f"{FIXTURE_ADW}_01_plan", "planner", "PlanReport",
         '{"raw": "not json"}', 0, 1, "2026-08-17T12:00:02Z"),
    )
    conn.execute(
        "INSERT INTO gate_results (adw_id, phase_id, attempt, gate, passed, outcome,"
        " nonempty_required, violations_json, checks_json, created_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (FIXTURE_ADW, f"{FIXTURE_ADW}_01_plan", 1, "artifacts", 1, "PASS", 1, "[]",
         '[{"item": "plan.md", "ok": true, "note": "exists"}]', "2026-08-17T12:00:03Z"),
    )
    conn.execute(
        "INSERT INTO processes (adw_id, kind, name, pid, command, started_at)"
        " VALUES (?,?,?,?,?,?)",
        (FIXTURE_ADW, "agent", "planner", 43210, "pi fixture", "2026-08-17T12:00:01Z"),
    )
    conn.execute(
        "INSERT INTO agent_sessions (adw_id, agent, coding_agent, model, color, session_id,"
        " context_tokens, context_window, created_at, last_used_at)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        (FIXTURE_ADW, "planner", "pi", "test/model", "cyan", "sssf-hd13-planner", 900, 100000,
         "2026-08-17T12:00:01Z", "2026-08-17T12:00:04Z"),
    )
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()


def build_fixture(path: Path) -> None:
    tracer_schema(path)
    populate(path)


def logical_dump(path: Path) -> str:
    """Every cell of every table, ordered, read through a read-only connection."""
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=5.0)
    conn.execute("PRAGMA query_only=ON;")
    chunks = []
    for (table,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        chunks.append(f"# {table}: {','.join(columns)}")
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        for row in sorted(repr(item) for item in rows):
            chunks.append(row)
    conn.close()
    return "\n".join(chunks)


def snapshot(path: Path) -> tuple[str, str]:
    """The property under test: whole-file digest plus full logical content."""
    return hashlib.sha256(path.read_bytes()).hexdigest(), logical_dump(path)


def cells(path: Path) -> dict[tuple[str, str, str], object]:
    """Every cell keyed by (table, primary-ish key, column), for exact diffing."""
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, timeout=5.0)
    conn.execute("PRAGMA query_only=ON;")
    grid: dict[tuple[str, str, str], object] = {}
    for (table,) in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ):
        columns = [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]
        for record in conn.execute(f"SELECT rowid, * FROM {table} ORDER BY rowid"):
            key = str(record[0])
            for index, column in enumerate(columns, start=1):
                grid[(table, key, column)] = record[index]
    conn.close()
    return grid


def changed_cells(before: dict, after: dict) -> set[tuple[str, str, str]]:
    return {key for key in set(before) | set(after) if before.get(key) != after.get(key)}


# ── property checks ──────────────────────────────────────────────────────────


def matrix_shape_errors() -> list[str]:
    errors: list[str] = []
    rows = sqlite_authority.matrix()
    if not rows:
        errors.append("the authority matrix is empty")
        return errors

    seen: set[tuple[str, str, str]] = set()
    classes_seen: set[str] = set()
    for row in rows:
        key = (row["store"], row["record"], row["field"])
        if key in seen:
            errors.append(f"duplicate authority row for {key}")
        seen.add(key)
        classes_seen.add(row["authority_class"])

        if row["store"] not in sqlite_authority.STORES:
            errors.append(f"{key}: unknown store {row['store']!r}")
        if row["authority_class"] not in sqlite_authority.AUTHORITY_CLASSES:
            errors.append(f"{key}: unknown authority class {row['authority_class']!r}")
        for name in ("authority_owner", "mutation_owner"):
            value = row[name]
            # The parenthetical is a qualifier ("append-only", "overwrite"), not a
            # second owner, so it is stripped before the one-owner check.
            named = re.sub(r"\s*\([^)]*\)", "", value).strip()
            if not isinstance(value, str) or not named:
                errors.append(f"{key}: {name} is not a single named owner")
            elif "," in named or " and " in named:
                errors.append(f"{key}: {name} names more than one owner: {value!r}")
        raw = row["raw_source"]
        if raw != sqlite_authority.RAW_SOURCE_NONE and not raw.startswith(
            sqlite_authority.RAW_SOURCE_PREFIXES
        ):
            errors.append(f"{key}: raw_source {raw!r} is outside the closed vocabulary")

    missing_classes = set(sqlite_authority.AUTHORITY_CLASSES) - classes_seen
    if missing_classes:
        errors.append(f"authority classes declared but never used: {sorted(missing_classes)}")
    return errors


def class_distinctness_errors() -> list[str]:
    """Observation, triage, archive/evidence copy, and run-state mutation stay distinct."""
    errors: list[str] = []
    rows = sqlite_authority.matrix()
    by_class: dict[str, set[str]] = {}
    for row in rows:
        by_class.setdefault(row["authority_class"], set()).add(row["mutation_owner"])

    for authority_class in ("query-projection", "archived-evidence-copy"):
        owners = by_class.get(authority_class, set())
        if not owners:
            errors.append(f"{authority_class} has no rows")
        for owner in owners:
            if not owner.startswith("none"):
                errors.append(f"{authority_class} must have no mutation owner, found {owner!r}")

    run_state = by_class.get("canonical-run-state", set())
    if run_state != {sqlite_authority.TRACER}:
        errors.append(f"canonical run state must be mutated only by the tracer, found {run_state}")

    triage = by_class.get("triage-state", set())
    if triage != {sqlite_authority.ARCHIVE_ROUTE}:
        errors.append(f"triage state must be mutated only by the archive route, found {triage}")

    lifecycle = by_class.get("lifecycle-run-record", set())
    if lifecycle != {sqlite_authority.RUN_RECORD_OWNER}:
        errors.append(f"lifecycle run record owner drifted: {lifecycle}")

    duties = [run_state, triage, lifecycle, by_class.get("raw-transport", set())]
    flat = [owner for duty in duties for owner in duty]
    if len(flat) != len(set(flat)):
        errors.append(f"a mutation owner holds more than one duty: {sorted(flat)}")

    # A field must not carry two classes on the same record.
    per_field: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        per_field.setdefault((row["record"], row["field"]), set()).add(row["authority_class"])
    for key, found in per_field.items():
        if len(found) != 1:
            errors.append(f"{key} carries more than one authority class: {sorted(found)}")
    return errors


def completeness_errors(fixture: Path) -> list[str]:
    """The matrix must agree, field for field, with the real owners' own bytes."""
    errors: list[str] = []

    declared = sqlite_authority.sqlite_fields()
    observed = tracer_schema(fixture)
    if set(declared) != set(observed):
        errors.append(
            f"declared SQLite tables {sorted(declared)} differ from the tracer's {sorted(observed)}"
        )
    for table in sorted(set(declared) & set(observed)):
        if declared[table] != observed[table]:
            errors.append(
                f"`{table}` fields differ: matrix {declared[table]} vs tracer {observed[table]}"
            )

    run_record_fields = module_constants(RUN_RECORD_SOURCE, ("FIELDS",)).get("FIELDS")
    declared_run_record = [
        row["field"]
        for row in sqlite_authority.matrix()
        if row["store"] == "run-record"
    ]
    if run_record_fields is None:
        errors.append("run_record.py no longer declares a FIELDS constant")
    elif sorted(run_record_fields) != sorted(declared_run_record):
        errors.append(
            f"run record fields differ: matrix {sorted(declared_run_record)} "
            f"vs owner {sorted(run_record_fields)}"
        )

    schema = evidence_manifest.EVIDENCE_MANIFEST_SCHEMA
    manifest_declared = {
        row["record"]: set()
        for row in sqlite_authority.matrix()
        if row["store"] == "manifest"
    }
    for row in sqlite_authority.matrix():
        if row["store"] == "manifest":
            manifest_declared[row["record"]].add(row["field"])
    expected_manifest = {
        evidence_manifest.SCHEMA_VERSION: set(schema["properties"]),
        f"{evidence_manifest.SCHEMA_VERSION}:inventory_item": set(
            schema["$defs"]["inventory_item"]["properties"]
        ),
    }
    if manifest_declared != expected_manifest:
        errors.append(
            f"evidence manifest fields differ: matrix {manifest_declared} "
            f"vs owner {expected_manifest}"
        )

    projections = {
        row["record"]: []
        for row in sqlite_authority.matrix()
        if row["store"] == "projection"
    }
    for row in sqlite_authority.matrix():
        if row["store"] == "projection":
            projections[row["record"]].append(row["field"])

    conn = obs_query.connect_read_only(fixture)
    try:
        for command, (sql, _separator) in obs_query.QUERIES.items():
            record = f"obs_query:{command}"
            if record not in projections:
                errors.append(f"{record} has no authority rows")
                continue
            parameters = () if command == "sessions" else (FIXTURE_ADW,)
            cursor = conn.execute(sql, parameters)
            names = [description[0] for description in cursor.description]
            declared_fields = projections[record]
            if len(names) != len(declared_fields):
                errors.append(
                    f"{record}: matrix declares {len(declared_fields)} fields, "
                    f"the query projects {len(names)}"
                )
                continue
            # Order-independent: each declared field must claim exactly one
            # projected column, and every projected column must be claimed once.
            unclaimed = list(names)
            for declared_field in sorted(declared_fields):
                matches = [name for name in unclaimed if declared_field in name]
                if len(matches) != 1:
                    errors.append(
                        f"{record}: matrix field `{declared_field}` matches {matches} "
                        f"among the projected columns {names}"
                    )
                    continue
                unclaimed.remove(matches[0])
            if unclaimed:
                errors.append(f"{record}: projected columns with no authority row: {unclaimed}")
    finally:
        conn.close()
    return errors


def read_only_surface_errors() -> list[str]:
    """No read surface holds a mutation statement, and the reader opens read-only."""
    errors: list[str] = []

    helper = OBS_QUERY_SOURCE.read_text(encoding="utf-8")
    for sql, _separator in obs_query.QUERIES.values():
        if not sql.strip().upper().startswith("SELECT"):
            errors.append(f"obs_query declares a non-SELECT query: {sql.strip()[:60]!r}")
    for fragment in ('"?mode=ro"', "PRAGMA query_only=ON;", "raise FileNotFoundError"):
        if fragment not in helper:
            errors.append(f"tools/obs_query.py no longer contains {fragment!r}")

    reader = VISUALIZER_DB_SOURCE.read_text(encoding="utf-8")
    if "new Database(path, { readonly: true })" not in reader:
        errors.append("the visualizer read connection is no longer opened readonly")
    writes = archive_statements(reader)
    if writes != [EXPECTED_ARCHIVE_SQL]:
        errors.append(f"visualizer write statements are not exactly the archive update: {writes}")

    server = VISUALIZER_SERVER_SOURCE.read_text(encoding="utf-8")
    methods = re.findall(r"\b(POST|PUT|PATCH|DELETE)\s*:", server)
    if methods != ["POST"]:
        errors.append(f"the visualizer server declares mutating methods {methods}, expected one POST")
    if "/api/sessions/:adw_id/archive" not in server:
        errors.append("the archive route is missing from the visualizer server")
    return errors


def read_only_behaviour_errors(fixture: Path) -> list[str]:
    """Reads leave the database byte-identical; a write through the reader fails."""
    errors: list[str] = []

    before = snapshot(fixture)
    for command, extra in (
        ("sessions", []),
        ("phases", [FIXTURE_ADW]),
        ("tail", [FIXTURE_ADW]),
        ("procs", [FIXTURE_ADW]),
        ("live-pids", [FIXTURE_ADW]),
    ):
        completed = subprocess.run(
            [sys.executable, str(OBS_QUERY_SOURCE), "--db", str(fixture), command, *extra],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if completed.returncode != 0:
            errors.append(f"read surface `{command}` failed: {completed.stdout.strip()}")
    after = snapshot(fixture)
    if after != before:
        errors.append("a read-only surface changed the database")

    conn = obs_query.connect_read_only(fixture)
    refused = False
    try:
        conn.execute("UPDATE sessions SET status = 'tampered'")
    except sqlite3.Error:
        refused = True
    finally:
        conn.close()
    if not refused:
        errors.append("a write through the read-only helper was accepted")
    if snapshot(fixture) != before:
        errors.append("the refused write still changed the database")
    return errors


def defective_helper_errors(temp: Path, fixture: Path) -> list[str]:
    """Watched red against the real failure shape: a read helper that lost its guards.

    A copy of the shipped helper with `mode=ro` and `query_only` removed must be
    seen to mutate the database. If this control cannot go red, the green result
    above means only that nothing was attempted.
    """
    errors: list[str] = []
    source = OBS_QUERY_SOURCE.read_text(encoding="utf-8")
    defective_source = source.replace('+ "?mode=ro"', '+ ""').replace(
        '"PRAGMA query_only=ON;"', '"PRAGMA query_only=OFF;"'
    )
    if defective_source == source:
        errors.append("could not build the defective-helper control: the guards moved")
        return errors

    defective_path = temp / "defective_obs_query.py"
    defective_path.write_text(defective_source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("hd13_defective_obs_query", defective_path)
    if spec is None or spec.loader is None:
        errors.append("could not load the defective-helper control")
        return errors
    defective = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(defective)

    target = temp / "defective-target.db"
    target.write_bytes(fixture.read_bytes())
    before = snapshot(target)
    conn = defective.connect_read_only(target)
    try:
        conn.execute("UPDATE sessions SET status = 'tampered'")
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    except sqlite3.Error as exc:
        errors.append(f"the defective-helper control did not mutate: {exc}")
    finally:
        conn.close()
    after = snapshot(target)
    if after == before:
        errors.append(
            "the defective-helper control left the database unchanged; the read-only "
            "assertion above cannot distinguish a guarded helper from an unguarded one"
        )
    return errors


def comparator_capability_errors(fixture: Path) -> list[str]:
    """Negative control: the comparator must detect a real mutation, or it proves nothing."""
    errors: list[str] = []
    before = snapshot(fixture)
    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute("UPDATE sessions SET status = 'tampered' WHERE adw_id = ?", (FIXTURE_ADW,))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    after = snapshot(fixture)
    if after[0] == before[0]:
        errors.append("negative control: the file digest did not change on a real mutation")
    if after[1] == before[1]:
        errors.append("negative control: the logical dump did not change on a real mutation")

    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute("UPDATE sessions SET status = 'running' WHERE adw_id = ?", (FIXTURE_ADW,))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    if snapshot(fixture)[1] != before[1]:
        errors.append("negative control: the fixture was not restored")
    return errors


def apply_statement(fixture: Path, sql: str, archived: int) -> set[tuple[str, str, str]]:
    before = cells(fixture)
    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute(sql, (archived, FIXTURE_ADW))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    return changed_cells(before, cells(fixture))


def triage_errors(fixture: Path) -> list[str]:
    """Only `sessions.archived` may move, proven by the visualizer's own statement."""
    errors: list[str] = []
    statements = archive_statements(VISUALIZER_DB_SOURCE.read_text(encoding="utf-8"))
    if statements != [EXPECTED_ARCHIVE_SQL]:
        errors.append("cannot run the triage control: the archive statement is not extractable")
        return errors

    moved = apply_statement(fixture, statements[0], 1)
    unexpected = {key for key in moved if key[0] != "sessions" or key[2] != "archived"}
    if unexpected:
        errors.append(f"the archive route changed columns it does not own: {sorted(unexpected)}")
    if not moved:
        errors.append("the archive route changed nothing; the control proved nothing")

    restored = apply_statement(fixture, statements[0], 0)
    if restored != moved:
        errors.append("un-archiving did not move exactly the same cells back")

    # Negative control: a widened archive statement must be caught by the same
    # comparator. Without this, "no other column changed" could mean "nothing was
    # compared".
    widened = "UPDATE sessions SET archived = ?, status = 'triaged' WHERE adw_id = ?"
    widened_moved = apply_statement(fixture, widened, 1)
    caught = {key for key in widened_moved if key[0] != "sessions" or key[2] != "archived"}
    if not caught:
        errors.append("negative control: a widened archive statement was not detected")

    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute(
        "UPDATE sessions SET archived = 0, status = 'running' WHERE adw_id = ?", (FIXTURE_ADW,)
    )
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()

    # Negative control: a second write statement in the reader must go red.
    tampered = VISUALIZER_DB_SOURCE.read_text(encoding="utf-8").replace(
        f'"{EXPECTED_ARCHIVE_SQL}"',
        f'"{EXPECTED_ARCHIVE_SQL}"; this.writer.query("DELETE FROM events WHERE adw_id = ?")',
        1,
    )
    if len(archive_statements(tampered)) < 2:
        errors.append("negative control: a second visualizer write statement was not detected")
    return errors


def observation_errors(temp: Path, fixture: Path) -> list[str]:
    """Missing, empty and row-less databases are could-not-observe, never a pass."""
    errors: list[str] = []

    good = sqlite_authority.observe(fixture)
    if good["observation"] != "observed-good":
        errors.append(f"the populated fixture was not observed-good: {good}")

    def closed_vocabulary(label: str, result: dict) -> None:
        if result["observation"] not in sqlite_authority.OBSERVATIONS:
            errors.append(f"{label}: {result['observation']!r} is not a declared observation")
        for reason in result["contradictions"]:
            if reason["code"] not in sqlite_authority.CONTRADICTION_REASONS:
                errors.append(f"{label}: {reason['code']} is outside the contradiction vocabulary")
        for reason in result["absences"]:
            if reason["code"] not in sqlite_authority.CNO_REASONS:
                errors.append(f"{label}: {reason['code']} is outside the CNO vocabulary")

    missing = temp / "missing.db"
    absent = sqlite_authority.observe(missing)
    if absent["observation"] != "could-not-observe":
        errors.append(f"a missing database was not could-not-observe: {absent['observation']}")
    if missing.exists():
        errors.append("observing a missing database created it")

    zero = temp / "zero.db"
    zero.write_bytes(b"")
    if sqlite_authority.observe(zero)["observation"] != "could-not-observe":
        errors.append("a zero-byte database was not could-not-observe")

    schema_only = temp / "schema-only.db"
    tracer_schema(schema_only)
    result = sqlite_authority.observe(schema_only)
    if result["observation"] != "could-not-observe":
        errors.append(f"a schema-only database was not could-not-observe: {result['observation']}")
    if "NO_CANONICAL_ROWS" not in {reason["code"] for reason in result["absences"]}:
        errors.append("an empty database lost its NO_CANONICAL_ROWS reason")

    unreadable = temp / "unreadable.db"
    unreadable.write_bytes(b"this is not a sqlite database at all, not even close\n" * 8)
    if sqlite_authority.observe(unreadable)["observation"] != "could-not-observe":
        errors.append("an unreadable database was not could-not-observe")

    # Precedence: a contradiction found alongside an absence must win, so an
    # unreadable or empty database never masks a real violation.
    masked = temp / "masked.db"
    tracer_schema(masked)
    conn = sqlite3.connect(masked, isolation_level=None)
    conn.execute("ALTER TABLE sessions ADD COLUMN unowned_column TEXT")
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    masked_result = sqlite_authority.observe(masked)
    if masked_result["observation"] != "observed-bad":
        errors.append(
            "an unowned column alongside zero rows was narrowed to "
            f"{masked_result['observation']}; a failure must outrank could-not-observe"
        )
    if not masked_result["absences"]:
        errors.append("precedence control lost the absence it outranked")

    undeclared = temp / "undeclared.db"
    tracer_schema(undeclared)
    populate(undeclared)
    conn = sqlite3.connect(undeclared, isolation_level=None)
    conn.execute("CREATE TABLE unowned_table (id INTEGER)")
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    if sqlite_authority.observe(undeclared)["observation"] != "observed-bad":
        errors.append("a table with no authority owner was not observed-bad")

    for label, path in (
        ("populated", fixture),
        ("missing", missing),
        ("zero-byte", zero),
        ("schema-only", schema_only),
        ("unreadable", unreadable),
        ("masked", masked),
        ("undeclared-table", undeclared),
    ):
        closed_vocabulary(label, sqlite_authority.observe(path))

    for label, path, expected in (
        ("populated", fixture, 0),
        ("missing", missing, 2),
        ("zero-byte", zero, 2),
        ("schema-only", schema_only, 2),
        ("undeclared-table", undeclared, 1),
    ):
        completed = subprocess.run(
            [sys.executable, str(ROOT / "tools/sqlite_authority.py"), "observe", "--db", str(path)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if completed.returncode != expected:
            errors.append(
                f"`observe` on the {label} database exited {completed.returncode}, "
                f"expected {expected}"
            )
    return errors


def documentation_errors() -> list[str]:
    """Governed documents may not restate a claim the code refutes."""
    errors: list[str] = []
    for relative in sqlite_authority.GOVERNED_DOCUMENTS:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"governed document is missing: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for claim in sqlite_authority.REFUTED_CLAIMS:
            for match in re.finditer(claim["pattern"], text, flags=re.IGNORECASE):
                line = text[: match.start()].count("\n") + 1
                errors.append(
                    f"{relative}:{line} restates the refuted claim `{claim['id']}` "
                    f"({match.group(0)!r}): {claim['why']}"
                )

    if not AUTHORITY_DOC.is_file():
        errors.append("docs/reference/SQLITE_AUTHORITY.md is missing")
        return errors

    doc = AUTHORITY_DOC.read_text(encoding="utf-8")
    rendered = sqlite_authority.render_table()
    if rendered not in doc:
        errors.append(
            "docs/reference/SQLITE_AUTHORITY.md does not embed the generated matrix verbatim; "
            "regenerate it with `python3 tools/sqlite_authority.py render`"
        )
    if sqlite_authority.RETAINED_HISTORICAL_CLAIM not in doc:
        errors.append(
            "the reference does not record where the superseded claim is retained as history "
            f"({sqlite_authority.RETAINED_HISTORICAL_CLAIM})"
        )
    return errors


def documentation_control_errors() -> list[str]:
    """Every refuted pattern must fire on the sentence that actually shipped."""
    errors: list[str] = []
    patterns = {claim["id"]: claim["pattern"] for claim in sqlite_authority.REFUTED_CLAIMS}
    unfired = set(patterns)
    for claim_id, sentence in HISTORICAL_CLAIMS:
        if claim_id not in patterns:
            errors.append(f"historical claim references unknown refutation `{claim_id}`")
            continue
        if not re.search(patterns[claim_id], sentence, flags=re.IGNORECASE):
            errors.append(
                f"negative control: the shipped sentence for `{claim_id}` is no longer rejected: "
                f"{sentence[:70]!r}"
            )
        else:
            unfired.discard(claim_id)
    if unfired:
        errors.append(
            f"refuted claims with no shipped-sentence control: {sorted(unfired)}"
        )
    return errors


# ── entry point ──────────────────────────────────────────────────────────────


def report_controls(temp: Path, fixture: Path) -> None:
    """Print what each negative control actually observed, so the red is on the record."""
    print("## negative controls (each of these MUST be detectable)")
    print()

    before = snapshot(fixture)
    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute("UPDATE sessions SET status = 'tampered' WHERE adw_id = ?", (FIXTURE_ADW,))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    after = snapshot(fixture)
    print(f"real mutation, digest before: {before[0]}")
    print(f"real mutation, digest after:  {after[0]}")
    print(f"digest detected the mutation: {before[0] != after[0]}")
    print(f"logical dump detected it:     {before[1] != after[1]}")
    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute("UPDATE sessions SET status = 'running' WHERE adw_id = ?", (FIXTURE_ADW,))
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    print()

    widened = "UPDATE sessions SET archived = ?, status = 'triaged' WHERE adw_id = ?"
    moved = apply_statement(fixture, widened, 1)
    outside = sorted(key for key in moved if key[0] != "sessions" or key[2] != "archived")
    print(f"widened archive statement: {widened}")
    print(f"cells moved outside sessions.archived: {outside}")
    conn = sqlite3.connect(fixture, isolation_level=None)
    conn.execute(
        "UPDATE sessions SET archived = 0, status = 'running' WHERE adw_id = ?", (FIXTURE_ADW,)
    )
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    conn.close()
    print()

    tampered = VISUALIZER_DB_SOURCE.read_text(encoding="utf-8").replace(
        f'"{EXPECTED_ARCHIVE_SQL}"',
        f'"{EXPECTED_ARCHIVE_SQL}"; this.writer.query("DELETE FROM events WHERE adw_id = ?")',
        1,
    )
    print(f"write statements in the shipped reader: {archive_statements(VISUALIZER_DB_SOURCE.read_text(encoding='utf-8'))}")
    print(f"write statements in a tampered reader:  {archive_statements(tampered)}")
    print()

    for label, path in (
        ("populated fixture", fixture),
        ("missing", temp / "control-missing.db"),
        ("zero-byte", temp / "control-zero.db"),
        ("schema-only", temp / "control-schema-only.db"),
        ("unreadable", temp / "control-unreadable.db"),
        ("unowned column + zero rows", temp / "control-masked.db"),
    ):
        if label == "zero-byte":
            path.write_bytes(b"")
        elif label == "schema-only":
            tracer_schema(path)
        elif label == "unreadable":
            path.write_bytes(b"not a sqlite database\n" * 8)
        elif label.startswith("unowned"):
            tracer_schema(path)
            conn = sqlite3.connect(path, isolation_level=None)
            conn.execute("ALTER TABLE sessions ADD COLUMN unowned_column TEXT")
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.close()
        result = sqlite_authority.observe(path)
        codes = [reason["code"] for reason in result["contradictions"] + result["absences"]]
        print(f"observe {label:>28}: {result['observation']:<18} {sorted(set(codes))}")
    print()

    source = OBS_QUERY_SOURCE.read_text(encoding="utf-8")
    defective_errors = defective_helper_errors(temp, fixture)
    print("defective read helper (mode=ro and query_only removed):")
    print(f"  guards present in the shipped helper: {'?mode=ro' in source}")
    print(f"  control observed a mutation: {not defective_errors}")
    for error in defective_errors:
        print(f"  {error}")
    print()

    print("shipped-sentence documentation controls:")
    patterns = {claim["id"]: claim["pattern"] for claim in sqlite_authority.REFUTED_CLAIMS}
    for claim_id, sentence in HISTORICAL_CLAIMS:
        match = re.search(patterns[claim_id], sentence, flags=re.IGNORECASE)
        head = " ".join(sentence.split())[:64]
        print(f"  rejected={bool(match)} {claim_id:<30} {head!r}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the HD-13 field-level authority matrix."
    )
    parser.add_argument(
        "--controls",
        action="store_true",
        help="Also print what every negative control observed.",
    )
    args = parser.parse_args()

    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sssf-hd13-") as raw_temp:
        temp = Path(raw_temp)
        fixture = temp / "fixture.db"
        build_fixture(fixture)

        errors.extend(matrix_shape_errors())
        errors.extend(class_distinctness_errors())
        errors.extend(completeness_errors(temp / "derived.db"))
        errors.extend(read_only_surface_errors())
        errors.extend(read_only_behaviour_errors(fixture))
        errors.extend(comparator_capability_errors(fixture))
        errors.extend(defective_helper_errors(temp, fixture))
        errors.extend(triage_errors(fixture))
        errors.extend(observation_errors(temp, fixture))
        errors.extend(documentation_errors())
        errors.extend(documentation_control_errors())

        if args.controls:
            report_controls(temp, fixture)
            print()

    if errors:
        print("HD-13 SQLite field authority: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("HD-13 SQLite field authority: PASS")
    print(f"{len(sqlite_authority.matrix())} fields carry exactly one authority and mutation owner")
    print("read-only surfaces left the fixture byte-identical and refused a write")
    print("the archive statement moved sessions.archived and nothing else")
    print("missing, zero-byte, unreadable and row-less databases are could-not-observe")
    print("a contradiction alongside an absence stays observed-bad")
    print("governed documents restate no claim the code refutes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
