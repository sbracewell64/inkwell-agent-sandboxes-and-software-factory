from __future__ import annotations

import sqlite3
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from adw_modules import agents, gates
from adw_modules.console import Console
from adw_modules.data_types import (
    AgentCall,
    BuildOutput,
    GateCNOReason,
    GateCNOSource,
    GateOutcome,
    GateReport,
    GateStatus,
    GenericOutput,
    Phase,
    PhaseParams,
)
from adw_modules.tracer import Tracer
from pydantic import ValidationError


def test_required_zero_checks_is_cno_and_not_truthy() -> None:
    report = GateReport(nonempty_required=True)

    assert report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert report.outcome.reason == GateCNOReason.NO_REQUIRED_OBSERVATIONS
    assert report.outcome.source == GateCNOSource.GATE_REPORT
    assert report.problems
    with pytest.raises(TypeError, match="three values"):
        bool(report.outcome)


def test_explicit_failed_check_is_fail() -> None:
    report = GateReport(nonempty_required=True).check("fixture", False, "observed defect")

    assert report.outcome.status == GateStatus.FAIL
    assert report.violations == ["fixture: observed defect"]

    partial = GateReport.could_not_observe(
        GateCNOReason.GATE_RAISED, GateCNOSource.GATE_EXECUTION, "other evidence unavailable"
    ).check("fixture", False, "observed defect")
    assert partial.outcome.status == GateStatus.FAIL


def test_gate_evidence_requirement_must_be_explicit_boolean() -> None:
    with pytest.raises(ValidationError):
        GateReport.model_validate({"nonempty_required": "false", "checks": []})


@pytest.mark.parametrize(
    "metadata",
    [
        {"cno_detail": "unavailable"},
        {"cno_reason": "GATE_RAISED"},
        {"cno_source": "GATE_EXECUTION"},
    ],
)
def test_incomplete_cno_metadata_is_cno(metadata: dict[str, str]) -> None:
    report = GateReport.model_validate({
        "nonempty_required": True,
        "checks": [{"item": "positive", "ok": True}],
        **metadata,
    })

    assert report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert report.outcome.reason == GateCNOReason.MALFORMED_TYPED_OUTCOME
    assert report.outcome.source == GateCNOSource.GATE_REPORT


def test_nonempty_exact_positive_artifact_is_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    artifact = Path("result.txt")
    artifact.write_text("qualifying evidence\n")
    envelope = BuildOutput(status="success", artifacts=[str(artifact)], changed_files=[str(artifact)])

    reports = [
        gates.artifacts_exist(envelope, None),
        gates.files_non_empty(envelope, None),
        gates.diff_matches_claims(envelope, None),
    ]

    assert all(report.checks for report in reports)
    assert [report.outcome.status for report in reports] == [GateStatus.PASS] * 3


@pytest.mark.parametrize(
    "raw",
    [
        '{}',
        '{"status":"UNKNOWN"}',
        '{"status":"PASS","status":"FAIL"}',
        '{"status":"COULD_NOT_OBSERVE"}',
        '{"status":"PASS","reason":"LEGACY_BOOLEAN_ONLY","source":"TRACE_READER"}',
    ],
)
def test_malformed_unknown_duplicate_outcome_is_refused(raw: str) -> None:
    with pytest.raises((ValidationError, ValueError)):
        GateOutcome.from_json(raw)


def test_zero_discovered_gates_and_legacy_return_are_cno() -> None:
    envelope = GenericOutput(status="success")
    empty_call = AgentCall(output_type=GenericOutput, prompt="fixture", gates=[])
    name, empty_report = agents._evaluate_gates(empty_call, envelope, None)[0]

    assert name == "gate_discovery"
    assert empty_report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert empty_report.outcome.reason == GateCNOReason.NO_GATES_DISCOVERED

    def legacy_gate(envelope, run):
        return []

    legacy_call = AgentCall(output_type=GenericOutput, prompt="fixture", gates=[legacy_gate])
    _, legacy_report = agents._evaluate_gates(legacy_call, envelope, None)[0]
    assert legacy_report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert legacy_report.outcome.reason == GateCNOReason.INVALID_GATE_RETURN


def test_raised_gate_is_cno_not_generic_fail() -> None:
    def unavailable(envelope, run):
        raise OSError("fixture evidence unreadable")

    call = AgentCall(output_type=GenericOutput, prompt="fixture", gates=[unavailable])
    _, report = agents._evaluate_gates(call, GenericOutput(status="success"), None)[0]

    assert report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert report.outcome.reason == GateCNOReason.GATE_RAISED
    assert report.outcome.source == GateCNOSource.GATE_EXECUTION
    assert "unreadable" in report.outcome.detail


class _EventSink:
    def __init__(self) -> None:
        self.records = []

    def event(self, record) -> None:
        self.records.append(record)


def test_console_cannot_render_cno_as_pass() -> None:
    sink = _EventSink()
    output = StringIO()
    with redirect_stdout(output):
        console = Console(sink, "fixture-adw")
        console.gate_result("empty_gate", GateReport(nonempty_required=True))

    rendered = output.getvalue()
    assert "COULD_NOT_OBSERVE" in rendered
    assert "PASS" not in rendered
    assert "✓" not in rendered
    assert sink.records[-1].payload["level"] == "warn"


def _phase() -> Phase:
    return Phase(
        phase_id="phase-fixture",
        adw_id="adw-fixture",
        seq=1,
        params=PhaseParams(
            name="gate_fixture",
            kind="code",
            owner="test",
            description="Exercise typed gate trace persistence",
        ),
    )


def test_trace_persists_three_values_and_cno_reason_source(tmp_path: Path) -> None:
    tracer = Tracer(tmp_path / "typed.db", tmp_path / "events.jsonl")
    reports = [
        GateReport(nonempty_required=True).check("positive", True, "exact fixture"),
        GateReport(nonempty_required=True).check("negative", False, "observed defect"),
        GateReport(nonempty_required=True),
    ]
    for index, report in enumerate(reports, start=1):
        tracer.gate_row(_phase(), f"gate-{index}", report, 1)

    rows = tracer.conn.execute(
        "SELECT outcome, passed, cno_reason, cno_source, nonempty_required "
        "FROM gate_results ORDER BY id"
    ).fetchall()
    with pytest.raises(sqlite3.IntegrityError):
        tracer.conn.execute(
            "INSERT INTO gate_results (outcome, cno_reason, cno_source, nonempty_required) "
            "VALUES ('PASS','LEGACY_BOOLEAN_ONLY','TRACE_READER',1)"
        )
    tracer.conn.close()

    assert rows[0] == ("PASS", 1, None, None, 1)
    assert rows[1] == ("FAIL", 0, None, None, 1)
    assert rows[2] == (
        "COULD_NOT_OBSERVE",
        None,
        "NO_REQUIRED_OBSERVATIONS",
        "GATE_REPORT",
        1,
    )


def test_legacy_boolean_migration_never_promotes_old_green(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE gate_results ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, adw_id TEXT, phase_id TEXT, attempt INTEGER, "
        "gate TEXT, passed INTEGER, violations_json TEXT, checks_json TEXT, created_at TEXT)"
    )
    conn.execute(
        "INSERT INTO gate_results (gate, passed, violations_json, checks_json) VALUES (?,?,?,?)",
        ("legacy-green", 1, "[]", "[]"),
    )
    conn.execute(
        "INSERT INTO gate_results (gate, passed, violations_json, checks_json) VALUES (?,?,?,?)",
        ("legacy-red", 0, '["observed defect"]', "[]"),
    )
    conn.commit()
    conn.close()

    tracer = Tracer(db_path, tmp_path / "legacy-events.jsonl")
    rows = tracer.conn.execute(
        "SELECT gate, outcome, passed, cno_reason, cno_source FROM gate_results ORDER BY id"
    ).fetchall()
    tracer.conn.close()

    assert rows[0] == (
        "legacy-green",
        "COULD_NOT_OBSERVE",
        None,
        "LEGACY_BOOLEAN_ONLY",
        "SCHEMA_MIGRATION",
    )
    assert rows[1] == ("legacy-red", "FAIL", 0, None, None)


def test_partial_typed_migration_normalizes_unknown_and_vacuous_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "partial-typed.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE gate_results ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, adw_id TEXT, phase_id TEXT, "
        "attempt INTEGER, gate TEXT, passed INTEGER, outcome TEXT, cno_reason TEXT, "
        "cno_source TEXT, nonempty_required INTEGER, violations_json TEXT, "
        "checks_json TEXT, created_at TEXT)"
    )
    insert = (
        "INSERT INTO gate_results (gate, passed, outcome, cno_reason, cno_source, "
        "nonempty_required, violations_json, checks_json) VALUES (?,?,?,?,?,?,?,?)"
    )
    conn.execute(insert, ("unknown", 1, "SURPRISE", "ALIEN", "ALIEN", 1, "[]", "[]"))
    conn.execute(insert, ("vacuous", 1, "PASS", None, None, 1, "[]", "[]"))
    conn.commit()
    conn.close()

    tracer = Tracer(db_path, tmp_path / "partial-events.jsonl")
    rows = tracer.conn.execute(
        "SELECT gate, outcome, passed, cno_reason, cno_source "
        "FROM gate_results ORDER BY id"
    ).fetchall()
    tracer.conn.close()

    expected = (
        "COULD_NOT_OBSERVE",
        None,
        "MALFORMED_TYPED_OUTCOME",
        "SCHEMA_MIGRATION",
    )
    assert rows[0] == ("unknown", *expected)
    assert rows[1] == ("vacuous", *expected)


def test_malformed_migrated_typed_outcome_is_cno(tmp_path: Path) -> None:
    db_path = tmp_path / "malformed-typed.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE gate_results ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, passed INTEGER, outcome TEXT, "
        "cno_reason TEXT, cno_source TEXT, nonempty_required INTEGER, checks_json TEXT)"
    )
    insert = (
        "INSERT INTO gate_results "
        "(passed, outcome, cno_reason, cno_source, nonempty_required, checks_json) "
        "VALUES (?,?,?,?,?,?)"
    )
    conn.execute(insert, (1, "PASS", "GATE_RAISED", None, 0, "[]"))
    conn.execute(insert, (0, "FAIL", None, None, 0, "[]"))
    conn.execute(insert, (1, "PASS", None, None, 0, "[]"))
    conn.commit()
    conn.close()

    tracer = Tracer(db_path, tmp_path / "malformed-typed-events.jsonl")
    rows = tracer.conn.execute(
        "SELECT outcome, passed, cno_reason, cno_source FROM gate_results ORDER BY id"
    ).fetchall()
    tracer.conn.close()

    assert rows[0] == (
        "COULD_NOT_OBSERVE",
        None,
        "MALFORMED_TYPED_OUTCOME",
        "SCHEMA_MIGRATION",
    )
    assert rows[1] == ("FAIL", 0, None, None)
    assert rows[2] == ("PASS", 1, None, None)
