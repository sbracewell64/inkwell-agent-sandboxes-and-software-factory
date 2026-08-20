"""HD-04: the typed gate, console, and trace surfaces of the mutation fact.

The fact itself and its bidirectional comparison are proven offline and in CI by
`docs/validation/check_mutation_fact.py`, which runs without pydantic. What is
proven here is the layer that needs it: how a reconciliation becomes a
PASS/FAIL/COULD_NOT_OBSERVE gate outcome, that the boundary rides along with the
verdict, and that a phase's two consumers read ONE fact.
"""

from __future__ import annotations

import os
import sqlite3
import subprocess
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import pytest
from adw_modules import gates, mutation_fact, permissions
from adw_modules.console import Console
from adw_modules.data_types import (
    BuildOutput,
    GateCNOReason,
    GateCNOSource,
    GateReport,
    GateStatus,
    ObservationScope,
    Phase,
    PhaseParams,
)
from adw_modules.tracer import Tracer


class _Run:
    """The two attributes the claim gate and the permission check read."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.mutation = None


def _git(root: Path, *args: str) -> None:
    env = dict(os.environ)
    env.update({
        "GIT_CONFIG_GLOBAL": str(root / "absent-global"),
        "GIT_CONFIG_SYSTEM": str(root / "absent-system"),
        "GIT_AUTHOR_NAME": "hd04", "GIT_AUTHOR_EMAIL": "hd04@example.invalid",
        "GIT_COMMITTER_NAME": "hd04", "GIT_COMMITTER_EMAIL": "hd04@example.invalid",
    })
    subprocess.run(["git", *args], cwd=str(root), env=env, check=True,
                   capture_output=True)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = (tmp_path / "repo").resolve()
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "core.autocrlf", "false")
    # Distinct content on purpose: identical bytes would make the two files
    # interchangeable rename candidates, which is a different (and separately
    # proven) case from the rename this fixture's tests mean to exercise.
    (root / "kept.py").write_bytes(b"kept\n")
    (root / "edited.py").write_bytes(b"one\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "baseline")
    return root


def _observed(repo: Path, mutate) -> _Run:
    """Run `mutate` against the repo and publish the one fact of the phase."""
    run = _Run(repo)
    before = permissions.snapshot(run)
    mutate(repo)
    run.mutation = mutation_fact.MutationObservation.between(
        before, permissions.snapshot(run))
    return run


def test_exact_claim_set_is_pass_and_states_its_boundary(repo: Path) -> None:
    run = _observed(repo, lambda root: (root / "edited.py").write_bytes(b"two\n"))
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["edited.py"]), run)

    assert report.outcome.status == GateStatus.PASS
    assert [check.item for check in report.checks] == ["edited.py"]
    assert "modified" in report.checks[0].note
    # A green that cannot say what it did not look at reads as "nothing else
    # happened". This one says it.
    assert report.scope is not None
    assert report.scope.observed
    assert not report.scope.unobservable
    assert any("gitignored" in item for item in report.scope.out_of_scope)
    assert any("outside the repository" in item for item in report.scope.out_of_scope)


@pytest.mark.parametrize(
    ("mutate", "claims", "expected_violation"),
    [
        # a claimed path that did not actually change
        (lambda root: (root / "edited.py").write_bytes(b"two\n"),
         ["edited.py", "kept.py"], "kept.py"),
        # an actual changed path that was not claimed
        (lambda root: [(root / "edited.py").write_bytes(b"two\n"),
                       (root / "kept.py").write_bytes(b"two\n")],
         ["edited.py"], "kept.py"),
        # an extra actual path the envelope never mentioned
        (lambda root: [(root / "edited.py").write_bytes(b"two\n"),
                       (root / "scratch.tmp").write_bytes(b"left behind\n")],
         ["edited.py"], "scratch.tmp"),
        # nothing claimed at all, while the tree moved
        (lambda root: (root / "edited.py").write_bytes(b"two\n"), [], "edited.py"),
        # a truthfully deleted path left out of the claim set
        (lambda root: (root / "edited.py").unlink(), [], "edited.py"),
    ],
)
def test_each_direction_of_disagreement_is_fail(repo: Path, mutate, claims,
                                                expected_violation: str) -> None:
    run = _observed(repo, mutate)
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=claims), run)

    assert report.outcome.status == GateStatus.FAIL
    assert any(expected_violation in violation for violation in report.violations)
    assert report.scope is not None          # a red states its universe too


def test_truthful_deletion_and_rename_claims_pass(repo: Path) -> None:
    def mutate(root: Path) -> None:
        (root / "kept.py").rename(root / "moved.py")
        (root / "edited.py").unlink()

    run = _observed(repo, mutate)
    report = gates.diff_matches_claims(
        BuildOutput(status="success",
                    changed_files=["kept.py", "moved.py", "edited.py"]), run)

    assert report.outcome.status == GateStatus.PASS
    notes = {check.item: check.note for check in report.checks}
    assert "rename peer moved.py" in notes["kept.py"]
    assert "rename peer kept.py" in notes["moved.py"]
    assert "deleted" in notes["edited.py"]


def test_claiming_only_a_renames_destination_is_fail(repo: Path) -> None:
    run = _observed(repo, lambda root: (root / "kept.py").rename(root / "moved.py"))
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["moved.py"]), run)

    assert report.outcome.status == GateStatus.FAIL
    assert any("kept.py" in violation for violation in report.violations)


def test_incomplete_universe_is_cno_not_a_clean_pass(repo: Path) -> None:
    def mutate(root: Path) -> None:
        (root / "edited.py").write_bytes(b"two\n")
        (root / "kept.py").unlink()
        (root / "kept.py").mkdir()          # tracked path, no hashable content

    run = _observed(repo, mutate)
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["edited.py"]), run)

    assert report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert report.outcome.reason == GateCNOReason.INCOMPLETE_OBSERVED_UNIVERSE
    assert report.outcome.source == GateCNOSource.MUTATION_FACT
    assert report.scope is not None and report.scope.unobservable
    assert report.problems                  # CNO never advances a phase


def test_an_observed_defect_is_never_masked_by_an_observation_hole(repo: Path) -> None:
    def mutate(root: Path) -> None:
        (root / "edited.py").write_bytes(b"two\n")
        (root / "kept.py").unlink()
        (root / "kept.py").mkdir()

    run = _observed(repo, mutate)
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["edited.py", "never-touched.py"]), run)

    assert report.outcome.status == GateStatus.FAIL
    assert any("never-touched.py" in violation for violation in report.violations)


def test_gitignored_write_stays_outside_the_fact_and_the_verdict_says_so(repo: Path) -> None:
    (repo / ".gitignore").write_bytes(b"*.log\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "ignore logs")

    def mutate(root: Path) -> None:
        (root / "edited.py").write_bytes(b"two\n")
        (root / "out-of-fact.log").write_bytes(b"this really happened\n")

    run = _observed(repo, mutate)
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["edited.py"]), run)

    assert report.outcome.status == GateStatus.PASS
    assert (repo / "out-of-fact.log").exists()
    assert [check.item for check in report.checks] == ["edited.py"]
    assert any("gitignored" in item for item in report.scope.out_of_scope)


def test_nothing_claimed_and_nothing_moved_is_cno_not_agreement(repo: Path) -> None:
    """A builder that changed nothing has not agreed with anything."""
    run = _observed(repo, lambda root: None)
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=[]), run)

    assert report.checks == []
    assert report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert report.outcome.reason == GateCNOReason.NO_REQUIRED_OBSERVATIONS
    assert report.scope is not None and not report.scope.unobservable


def test_no_recorded_fact_is_cno_rather_than_path_existence(repo: Path) -> None:
    run = _Run(repo)                        # nothing published for this phase
    report = gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["kept.py"]), run)

    assert report.outcome.status == GateStatus.COULD_NOT_OBSERVE
    assert report.outcome.reason == GateCNOReason.INCOMPLETE_OBSERVED_UNIVERSE
    assert report.scope is not None and report.scope.unobservable


def test_permission_check_and_gate_consume_the_same_fact(
        repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Two snapshots would be two sources of truth. There must be only one."""
    run = _observed(repo, lambda root: (root / "edited.py").write_bytes(b"two\n"))
    before = mutation_fact.MutationObservation.between(
        run.mutation.before, run.mutation.before).after

    seen: dict[str, object] = {}
    real_reconcile = mutation_fact.reconcile

    def recording_reconcile(observation, claims):
        seen["gate"] = observation.after
        return real_reconcile(observation, claims)

    monkeypatch.setattr(mutation_fact, "reconcile", recording_reconcile)
    gates.diff_matches_claims(
        BuildOutput(status="success", changed_files=["edited.py"]), run)

    def refuse(_root):
        raise AssertionError("enforce took a second snapshot of its own")

    monkeypatch.setattr(mutation_fact, "observe", refuse)
    agent = type("Agent", (), {"name": "builder", "writes": None})()
    run.cfg = type("Cfg", (), {"defaults": type("D", (), {
        "protected_files": [], "data_dir": str(repo / "adw_data")})()})()
    touched = permissions.enforce(run, None, agent, before,
                                  after=run.mutation.after)

    assert seen["gate"] is run.mutation.after      # the same object, not an equal one
    assert touched == ["edited.py"]


def test_console_pass_cannot_read_as_unqualified_clean() -> None:
    scope = ObservationScope(
        observed=["tracked path content identity against HEAD"],
        out_of_scope=list(mutation_fact.OUT_OF_SCOPE_CLASSES))
    report = GateReport(nonempty_required=True, scope=scope).check(
        "edited.py", True, "claimed and observed modified")

    output = StringIO()
    with redirect_stdout(output):
        Console(_EventSink(), "fixture-adw").gate_result("diff_matches_claims", report)

    rendered = output.getvalue()
    assert "PASS" in rendered
    assert "NOT observed" in rendered
    assert "gitignored files" in rendered


class _EventSink:
    def __init__(self) -> None:
        self.records = []

    def event(self, record) -> None:
        self.records.append(record)


def _phase() -> Phase:
    return Phase(phase_id="phase-fixture", adw_id="adw-fixture", seq=1,
                 params=PhaseParams(name="gate_fixture", kind="code", owner="test",
                                    description="Persist a bounded gate verdict"))


def test_trace_persists_the_verdict_universe(tmp_path: Path) -> None:
    tracer = Tracer(tmp_path / "scope.db", tmp_path / "events.jsonl")
    scope = ObservationScope(observed=["tracked content identity"],
                             out_of_scope=list(mutation_fact.OUT_OF_SCOPE_CLASSES),
                             unobservable=["swapped: could not be hashed"])
    tracer.gate_row(_phase(), "diff_matches_claims",
                    GateReport(nonempty_required=True, scope=scope,
                               cno_reason=GateCNOReason.INCOMPLETE_OBSERVED_UNIVERSE,
                               cno_source=GateCNOSource.MUTATION_FACT,
                               cno_detail="one candidate could not be read"), 1)
    row = tracer.conn.execute(
        "SELECT outcome, passed, cno_reason, cno_source, scope_json FROM gate_results"
    ).fetchone()
    tracer.conn.close()

    assert row[:4] == ("COULD_NOT_OBSERVE", None, "INCOMPLETE_OBSERVED_UNIVERSE",
                       "MUTATION_FACT")
    assert "gitignored files" in row[4]
    assert "swapped" in row[4]


@pytest.mark.parametrize("vintage", ["pre-typed", "typed-with-narrow-check"])
def test_older_databases_readmit_the_current_closed_values(tmp_path: Path,
                                                           vintage: str) -> None:
    """A db written before a closed set grew must not refuse the new member."""
    db_path = tmp_path / f"{vintage}.db"
    conn = sqlite3.connect(db_path)
    if vintage == "pre-typed":
        conn.execute(
            "CREATE TABLE gate_results ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, adw_id TEXT, phase_id TEXT, "
            "attempt INTEGER, gate TEXT, passed INTEGER, violations_json TEXT, "
            "checks_json TEXT, created_at TEXT)")
        conn.execute("INSERT INTO gate_results (gate, passed, checks_json) "
                     "VALUES ('legacy-red', 0, '[]')")
    else:
        conn.execute(
            "CREATE TABLE gate_results ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, adw_id TEXT, phase_id TEXT, "
            "attempt INTEGER, gate TEXT, passed INTEGER, "
            "outcome TEXT NOT NULL CHECK(outcome IN ('PASS','FAIL','COULD_NOT_OBSERVE')), "
            "cno_reason TEXT, cno_source TEXT, nonempty_required INTEGER, "
            "violations_json TEXT, checks_json TEXT, created_at TEXT, "
            "CHECK((outcome='COULD_NOT_OBSERVE' AND cno_reason IN ("
            "'NO_REQUIRED_OBSERVATIONS','NO_GATES_DISCOVERED','GATE_RAISED',"
            "'INVALID_GATE_RETURN','LEGACY_BOOLEAN_ONLY','MALFORMED_TYPED_OUTCOME') "
            "AND cno_source IN ('GATE_REPORT','AGENT_CALL','GATE_EXECUTION',"
            "'GATE_ADAPTER','SCHEMA_MIGRATION','TRACE_READER')) "
            "OR (outcome IN ('PASS','FAIL') AND cno_reason IS NULL AND cno_source IS NULL))"
            ")")
        conn.execute("INSERT INTO gate_results (gate, passed, outcome, "
                     "nonempty_required, checks_json) "
                     "VALUES ('older-red', 0, 'FAIL', 1, '[]')")
    conn.commit()
    conn.close()

    tracer = Tracer(db_path, tmp_path / f"{vintage}-events.jsonl")
    tracer.gate_row(_phase(), "diff_matches_claims",
                    GateReport(nonempty_required=True,
                               cno_reason=GateCNOReason.INCOMPLETE_OBSERVED_UNIVERSE,
                               cno_source=GateCNOSource.MUTATION_FACT,
                               cno_detail="a candidate could not be read"), 1)
    rows = tracer.conn.execute(
        "SELECT gate, outcome, cno_reason, cno_source FROM gate_results ORDER BY id"
    ).fetchall()
    with pytest.raises(sqlite3.IntegrityError):
        tracer.conn.execute(
            "INSERT INTO gate_results (outcome, cno_reason, cno_source, "
            "nonempty_required) VALUES ('COULD_NOT_OBSERVE','ALIEN','MUTATION_FACT',1)")
    tracer.conn.close()

    assert rows[0][1] in {"FAIL", "COULD_NOT_OBSERVE"}       # the old row survived
    assert rows[-1] == ("diff_matches_claims", "COULD_NOT_OBSERVE",
                        "INCOMPLETE_OBSERVED_UNIVERSE", "MUTATION_FACT")
