"""Deterministic planning-foundation controls and watched-red coverage."""

from __future__ import annotations

import copy
import importlib.util
import re
from pathlib import Path

import pytest

_VALIDATOR_PATH = Path(__file__).parents[1] / "docs" / "validation" / "check_planning_foundation.py"
_SPEC = importlib.util.spec_from_file_location("planning_foundation_validator", _VALIDATOR_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_VALIDATOR)


def _symlink_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except (NotImplementedError, OSError) as error:
        if _VALIDATOR._is_windows_symlink_capability_error(error):
            pytest.skip(f"symlink creation unavailable: {error}")
        raise


def _temporary_project(tmp_path: Path) -> tuple[dict[str, object], Path]:
    project = _VALIDATOR.load_project()
    root = tmp_path / "project"
    project["root"] = root
    _VALIDATOR._materialize_fixture_references(project["state"], root)
    return project, root


def test_canonical_foundation_and_all_watched_red_controls_pass() -> None:
    control_cno: list[str] = []
    status, errors, red_failures = _VALIDATOR.validate_path(control_cno=control_cno)

    assert status in {"observed-good", "could-not-observe"}, errors
    assert red_failures == []
    if status == "could-not-observe":
        assert control_cno
        assert all("symlink-escape-" in item for item in control_cno)


def test_stale_complete_projection_prose_is_nonpass_and_names_surface() -> None:
    for key in ("lifecycle", "readme", "increment"):
        project = _VALIDATOR.load_project()
        original = project["surfaces"][key]
        mutated = original.replace("through FUT-016", "through FUT-013", 1)
        assert mutated != original
        project["surfaces"][key] = mutated

        status, errors = _VALIDATOR.validate_project(project, run_controls=False)

        assert status == "observed-bad"
        assert any(_VALIDATOR.SURFACE_PATHS[key].as_posix() in error for error in errors)


def test_closure_gate_requires_nonempty_exact_test_universe() -> None:
    failures = _VALIDATOR._watched_test_closure_controls()
    assert failures == []

    unrelated_nodeid = (
        "tests/test_planning_foundation.py::"
        "test_unrelated_notimplementederror_is_not_automatic_cno"
    )
    assert unrelated_nodeid in _VALIDATOR.CLOSURE_REQUIRED_TESTS
    omitted = tuple(
        nodeid
        for nodeid in _VALIDATOR.CLOSURE_REQUIRED_TESTS
        if nodeid != unrelated_nodeid
    )
    omitted_status, _ = _VALIDATOR.evaluate_test_closure(
        omitted,
        tuple((nodeid, "passed") for nodeid in omitted),
    )
    assert omitted
    assert omitted_status != "observed-good"

    renamed = tuple(
        nodeid if nodeid != unrelated_nodeid else nodeid + "_renamed"
        for nodeid in _VALIDATOR.CLOSURE_REQUIRED_TESTS
    )
    renamed_status, _ = _VALIDATOR.evaluate_test_closure(
        renamed,
        tuple((nodeid, "passed") for nodeid in renamed),
    )
    assert len(renamed) == len(_VALIDATOR.CLOSURE_REQUIRED_TESTS)
    assert renamed_status != "observed-good"

    required = ("tests/test_planning_foundation.py::required",)
    status, errors = _VALIDATOR.evaluate_test_closure(
        required,
        ((required[0], "passed"),),
        required_nodeids=required,
    )
    assert status == "observed-good", errors


def test_closure_gate_includes_unrelated_notimplementederror_regression() -> None:
    required = _VALIDATOR.CLOSURE_REQUIRED_TESTS
    unrelated_nodeid = (
        "tests/test_planning_foundation.py::"
        "test_unrelated_notimplementederror_is_not_automatic_cno"
    )
    reports = tuple((nodeid, "passed") for nodeid in required)

    status, errors = _VALIDATOR.evaluate_test_closure(
        required,
        reports,
        required_nodeids=required,
    )
    assert status == "observed-good", errors

    omitted = tuple(nodeid for nodeid in required if nodeid != unrelated_nodeid)
    omitted_status, _ = _VALIDATOR.evaluate_test_closure(
        omitted,
        tuple((nodeid, "passed") for nodeid in omitted),
        required_nodeids=required,
    )
    assert omitted_status != "observed-good"

    renamed = tuple(
        nodeid if nodeid != unrelated_nodeid else nodeid + "_renamed"
        for nodeid in required
    )
    renamed_status, _ = _VALIDATOR.evaluate_test_closure(
        renamed,
        tuple((nodeid, "passed") for nodeid in renamed),
        required_nodeids=required,
    )
    assert renamed_status != "observed-good"


def test_older_consistent_snapshot_cannot_replace_authoritative_generation() -> None:
    project = _VALIDATOR.load_project()
    stale = copy.deepcopy(project)
    stale["state"]["authoritative_planning_source"]["source_commit"] = "0" * 40
    stale["state"]["authoritative_planning_source"]["source_tree"] = "1" * 40
    stale["state"]["authoritative_planning_source"]["generation"] = "planning/future-sssf@" + "0" * 40 + ":" + "1" * 40
    stale["state"]["records"][-1]["state"] = "SEQUENCED"
    stale["state"]["records"][-1]["transition_history"].pop()
    stale["state"]["records"][-1].pop("planning_authority_binding", None)
    stale["surfaces"]["candidates"] = stale["surfaces"]["candidates"].replace(
        "| FUT-003 | FirstMate planning-transition awareness | ACTIVE |",
        "| FUT-003 | FirstMate planning-transition awareness | SEQUENCED |",
    )

    status, errors = _VALIDATOR.validate_project(stale, run_controls=False)

    assert status == "observed-bad"
    assert any("authoritative planning source identity/generation" in error for error in errors)


def test_current_planning_generation_is_observed_not_candidate_constant() -> None:
    project = _VALIDATOR.load_project()
    observation = project["authority_observation"]
    assert observation["source_commit"] == "eab880656b4ef00174ea514cca128f6336632fcf"
    assert observation["source_tree"] == "5328b8a437d894682f4ac1c5d7ae581694410c43"
    sbx2 = next(item for item in observation["lifecycle_identities"] if item["identity"] == "SBX-2")
    assert sbx2["state"] == "HELD"

    stale = copy.deepcopy(project)
    stale_commit = "5f83760a6d71bb798b9f652f21267fad4b743f16"
    stale_tree = "6e33db5ae5f7d43bf3a7f8c351d888c599d1997d"
    stale_generation = f"planning/future-sssf@{stale_commit}:{stale_tree}"
    stale["state"]["authoritative_planning_source"].update(
        source_commit=stale_commit,
        source_tree=stale_tree,
        generation=stale_generation,
    )
    stale["state"]["projection_scope"]["state_basis"].update(
        source_commit=stale_commit,
        source_tree=stale_tree,
        generation=stale_generation,
    )

    status, errors = _VALIDATOR.validate_project(stale, run_controls=False)

    assert status == "observed-bad"
    assert any("stale, missing, or mismatched" in error for error in errors)


def _authority_blob_fixture() -> dict[str, str]:
    lifecycle = (
        ("LAUNCH-1", "ACTIVE"),
        ("SBX-0", "ACTIVE"),
        ("SBX-1", "SEQUENCED"),
        ("SBX-2", None),
        ("SBX-3", None),
        ("SBX-4", None),
        ("SBX-5", None),
        ("SBX-6", None),
        ("SBX-7", None),
        ("SBX-8", None),
        ("WAYFINDER-0", "SEQUENCED"),
        ("WAYFINDER-1", "SEQUENCED"),
        ("DSH-0A", None),
        ("DSH-0B", None),
        ("DSH-1", None),
        ("DSH-2", None),
        ("DSH-3", None),
        ("DSH-4", None),
        ("DSH-5", None),
        ("DSH-6", None),
        ("DSH-7", None),
        ("DSH-8", None),
    )
    roadmap = "\n".join(
        (
            f"## {identity}\n"
            + (f"Planning state: `{state}`\n" if state else "roadmap substep\n")
            + ("landed bytes do not establish SBX-2 unlock.\n" if identity == "SBX-1" else "")
        )
        for identity, state in lifecycle
    ) + "\n## BOUND-1\ncomplete and qualify before `SBX-2` can leave `HELD`\n"
    future_states = (
        "SEQUENCED",
        "PRESERVE",
        "ACTIVE",
        "PRESERVE",
        "CANDIDATE",
        "CANDIDATE",
        "CANDIDATE",
        "CANDIDATE",
        "CANDIDATE",
        "CANDIDATE",
        "CANDIDATE",
        "CANDIDATE",
        "PRESERVE",
        "SEQUENCED",
        "SEQUENCED",
        "CANDIDATE",
    )
    future_rows = "\n".join(
        f"| FUT-{index:03d} | item | {state} |"
        for index, state in enumerate(future_states, 1)
    )
    future_details = "\n".join(
        f"## FUT-{index:03d} — item\n\n### Status\n\n`{state}`\n"
        for index, state in enumerate(future_states, 1)
    )
    return {
        "docs/development/FUTURE_CANDIDATES.md": future_rows + "\n" + future_details,
        "docs/development/ROADMAP.md": roadmap,
        "docs/development/INCREMENT_PROTOCOL.md": "\n".join(
            (
                "boundedness_delta:",
                "New or changed growth surfaces must use the boundedness registry/owner mechanism",
                "For an added or changed dynamic bound, prove the effective limit",
            )
        ),
        "docs/development/BOUNDEDNESS_LAW.md": "\n".join(
            ("Every list, queue, log, retry chain", "EXPLICIT_BOUND", "SAFE_UNBOUNDED")
        ),
        "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md": (
            "# BOUND-1 — Boundedness audit\n"
            "Planning state:** `SEQUENCED`\ncomplete and qualify before `SBX-2` activation"
        ),
    }


def test_authority_projection_preserves_sbx2_state_and_rejects_missing_identity() -> None:
    blobs = _authority_blob_fixture()
    observation, error = _VALIDATOR._project_authoritative_planning_blobs("a" * 40, "b" * 40, blobs)
    assert error is None
    assert observation is not None
    sbx2 = next(item for item in observation["lifecycle_identities"] if item["identity"] == "SBX-2")
    assert sbx2["state"] == "HELD"

    promoted = copy.deepcopy(blobs)
    promoted["docs/development/ROADMAP.md"] = promoted["docs/development/ROADMAP.md"].replace(
        "## SBX-2\nroadmap substep", "## SBX-2\nPlanning state: `ACTIVE`"
    )
    promoted_observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, promoted
    )
    assert promoted_observation is None
    assert error is not None and "unexpected explicit state" in error

    omitted = copy.deepcopy(blobs)
    omitted["docs/development/ROADMAP.md"] = omitted["docs/development/ROADMAP.md"].replace(
        "## SBX-8\nroadmap substep\n", ""
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, omitted
    )
    assert observation is None
    assert error is not None and "omits lifecycle identity" in error


def test_authority_projection_derives_held_sbx2_from_unlock_boundary() -> None:
    blobs = _authority_blob_fixture()

    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, blobs
    )

    assert error is None
    assert observation is not None
    sbx2 = next(item for item in observation["lifecycle_identities"] if item["identity"] == "SBX-2")
    assert sbx2["state"] == "HELD"


def test_authority_projection_derives_bound1_predecessor_markers() -> None:
    blobs = _authority_blob_fixture()
    observation, error = _VALIDATOR._project_authoritative_planning_blobs("a" * 40, "b" * 40, blobs)

    assert error is None
    assert observation is not None
    assert observation["bound1_markers"] == {
        "predecessor": "BOUND-1",
        "state": "SEQUENCED",
        "before": "SBX-2",
        "required_phrase": "complete and qualify before `SBX-2` activation",
        "leave_held_phrase": "complete and qualify before `SBX-2` can leave `HELD`",
    }

    removed = copy.deepcopy(blobs)
    removed["docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"] = (
        "# BOUND-1 — Boundedness audit\n> **Planning state:** `SEQUENCED`.\n"
    )
    removed_observation, removed_error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, removed
    )
    assert removed_observation is None
    assert removed_error is not None and "predecessor relationship" in removed_error


def test_sbx2_state_is_observed_from_authority_not_candidate_expectation() -> None:
    blobs = _authority_blob_fixture()
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, blobs
    )
    assert error is None
    assert observation is not None
    sbx2 = next(item for item in observation["lifecycle_identities"] if item["identity"] == "SBX-2")
    assert sbx2["state"] == "HELD"

    promoted = copy.deepcopy(blobs)
    promoted["docs/development/ROADMAP.md"] = promoted["docs/development/ROADMAP.md"].replace(
        "do not establish", "establish", 1
    )
    promoted_observation, promoted_error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, promoted
    )
    assert promoted_observation is None
    assert promoted_error is not None and "unlock boundary" in promoted_error


def test_missing_governed_identity_or_bound1_predecessor_is_nonpass() -> None:
    blobs = _authority_blob_fixture()
    omitted = copy.deepcopy(blobs)
    omitted["docs/development/ROADMAP.md"] = omitted["docs/development/ROADMAP.md"].replace(
        "## DSH-8\nroadmap substep\n", "", 1
    )
    omitted_observation, omitted_error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, omitted
    )
    assert omitted_observation is None
    assert omitted_error is not None and "omits lifecycle identity" in omitted_error

    removed_relation = copy.deepcopy(blobs)
    removed_relation["docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"] = (
        "# BOUND-1 — Boundedness audit\n> **Planning state:** `SEQUENCED`.\n"
    )
    relation_observation, relation_error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, removed_relation
    )
    assert relation_observation is None
    assert relation_error is not None and "predecessor relationship" in relation_error


def test_authority_projection_rejects_missing_duplicate_or_conflicting_governed_identities() -> None:
    blobs = _authority_blob_fixture()

    for identity in ("LAUNCH-1", "SBX-3", "DSH-1"):
        duplicated = copy.deepcopy(blobs)
        path = "docs/development/ROADMAP.md"
        block = _VALIDATOR._identity_heading_blocks(duplicated[path], identity)[0]
        duplicated[path] += "\n" + block
        observation, error = _VALIDATOR._project_authoritative_planning_blobs(
            "a" * 40, "b" * 40, duplicated
        )
    assert observation is None
    assert error is not None and "duplicate lifecycle identity" in error

    missing_substep_body = copy.deepcopy(blobs)
    path = "docs/development/ROADMAP.md"
    missing_substep_body[path] = missing_substep_body[path].replace(
        "## DSH-1\nroadmap substep\n", "## DSH-1\n", 1
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, missing_substep_body
    )
    assert observation is None
    assert error is not None and "substep declaration body is missing" in error

    malformed_substep_state = copy.deepcopy(blobs)
    malformed_substep_state[path] = malformed_substep_state[path].replace(
        "## SBX-3\nroadmap substep\n", "## SBX-3\nPlanning state ACTIVE\n", 1
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, malformed_substep_state
    )
    assert observation is None
    assert error is not None and "malformed state declaration" in error

    duplicate_state = copy.deepcopy(blobs)
    path = "docs/development/ROADMAP.md"
    block = _VALIDATOR._identity_heading_blocks(duplicate_state[path], "LAUNCH-1")[0]
    duplicate_state[path] = duplicate_state[path].replace(
        block, block + "\nPlanning state: `ACTIVE`", 1
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, duplicate_state
    )
    assert observation is None
    assert error is not None and "missing or duplicated" in error

    conflicting_bound = copy.deepcopy(blobs)
    conflicting_bound["docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"] += (
        "\n> **Planning state:** `ACTIVE`.\n"
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, conflicting_bound
    )
    assert observation is None
    assert error is not None and "duplicated" in error

    missing_future_heading = copy.deepcopy(blobs)
    path = "docs/development/FUTURE_CANDIDATES.md"
    missing_future_heading[path] = re.sub(
        r"(?ms)^## FUT-013\b.*?\Z", "", missing_future_heading[path]
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, missing_future_heading
    )
    assert observation is None
    assert error is not None and "missing or duplicate detail heading" in error

    conflicting_future_state = copy.deepcopy(blobs)
    conflicting_future_state[path] = conflicting_future_state[path].replace(
        "## FUT-004 — item\n\n### Status\n\n`PRESERVE`",
        "## FUT-004 — item\n\n### Status\n\n`ACTIVE`",
        1,
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, conflicting_future_state
    )
    assert observation is None
    assert error is not None and "conflicting state declarations" in error

    duplicate_future_status = copy.deepcopy(blobs)
    duplicate_future_status[path] = duplicate_future_status[path].replace(
        "## FUT-005 — item\n\n### Status\n\n`CANDIDATE`",
        "## FUT-005 — item\n\n### Status\n\n`CANDIDATE`\n\n### Status\n\n`CANDIDATE`",
        1,
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, duplicate_future_status
    )
    assert observation is None
    assert error is not None and "duplicate state declaration" in error

    successor_relation = copy.deepcopy(blobs)
    bound_path = "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"
    successor_relation[bound_path] = successor_relation[bound_path].replace(
        "before `SBX-2` activation", "before `SBX-7` activation", 1
    )
    observation, error = _VALIDATOR._project_authoritative_planning_blobs(
        "a" * 40, "b" * 40, successor_relation
    )
    assert error is None
    assert observation is not None
    assert observation["bound1_markers"]["before"] == "SBX-7"


def test_closure_gate_includes_authority_omission_and_predecessor_regressions() -> None:
    required = _VALIDATOR.CLOSURE_REQUIRED_TESTS
    authority_nodes = _VALIDATOR.AUTHORITY_CLOSURE_NODEIDS
    assert set(authority_nodes).issubset(required)
    for nodeid in authority_nodes:
        omitted = tuple(item for item in required if item != nodeid)
        omitted_status, _ = _VALIDATOR.evaluate_test_closure(
            omitted,
            tuple((item, "passed") for item in omitted),
            required_nodeids=required,
        )
        assert omitted_status != "observed-good"
        renamed = tuple(item if item != nodeid else item + "_renamed" for item in required)
        renamed_status, _ = _VALIDATOR.evaluate_test_closure(
            renamed,
            tuple((item, "passed") for item in renamed),
            required_nodeids=required,
        )
        assert renamed_status != "observed-good"


def test_bound1_omission_is_nonpass() -> None:
    project = _VALIDATOR.load_project()
    projection = project["state"]["projection_scope"]
    projection["lifecycle_identities"] = [
        item for item in projection["lifecycle_identities"] if item["identity"] != "BOUND-1"
    ]
    projection["mandatory_predecessors"] = []

    status, errors = _VALIDATOR.validate_project(project, run_controls=False)

    assert status == "observed-bad"
    assert any("BOUND-1 predecessor rule" in error for error in errors)


def test_projection_scope_prevents_out_of_scope_sbx2_readiness() -> None:
    project = _VALIDATOR.load_project()
    project["state"]["projection_scope"]["not_answerable_queries"] = []

    status, errors = _VALIDATOR.validate_project(project, run_controls=False)

    assert status == "observed-bad"
    assert any("out-of-scope readiness" in error for error in errors)


def test_ci_workflow_remains_credential_free() -> None:
    workflow = (_VALIDATOR.ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "github-token: ''" in workflow
    assert "github-token: ${{ github.token }}" not in workflow
    assert (
        "eab880656b4ef00174ea514cca128f6336632fcf:"
        "refs/remotes/origin/planning/future-sssf"
    ) in workflow


def test_windows_symlink_privilege_cno_is_machine_readable_non_pass(monkeypatch) -> None:
    project = _VALIDATOR.load_project()
    original = Path.symlink_to

    def denied(self: Path, target: Path, target_is_directory: bool = False) -> None:
        error = OSError("A required privilege is not held by the client")
        error.winerror = 1314
        raise error

    monkeypatch.setattr(Path, "symlink_to", denied)
    control_cno: list[str] = []
    status, errors, red_failures = _VALIDATOR.validate_path(control_cno=control_cno)
    assert status == "could-not-observe"
    assert errors == []
    assert red_failures == []
    assert set(control_cno) == {
        "symlink-escape-active-authoritative-reference",
        "symlink-escape-proven-acceptance-evidence",
        "symlink-escape-proven-implementation-evidence",
        "symlink-escape-proven-proof-evidence",
        "symlink-escape-proven-documentation-evidence",
    }
    result = _VALIDATOR._machine_result(status, errors=errors, cno=control_cno)
    assert result["outcome"] == "CNO"
    assert result["status"] == "UNVERIFIED"
    assert _VALIDATOR._validator_exit_code(status) != 0
    assert _VALIDATOR._fold_property_outcome([], control_cno) == "could-not-observe"

    contradictory = copy.deepcopy(project)
    contradictory["surfaces"]["readme"] = contradictory["surfaces"]["readme"].replace(
        "`ACTIVE` is engineering authorization only. `ACTIVE` is intake eligibility",
        "`ACTIVE` is runtime authority.",
        1,
    )
    mixed_cno: list[str] = []
    mixed_status, mixed_errors = _VALIDATOR.validate_project(
        contradictory, control_cno=mixed_cno
    )
    assert mixed_status == "observed-bad"
    assert mixed_errors
    assert mixed_cno
    assert _VALIDATOR._fold_property_outcome(["contradiction"], mixed_cno) == "observed-bad"

    def unrelated(self: Path, target: Path, target_is_directory: bool = False) -> None:
        error = OSError("fixture filesystem I/O failure")
        error.winerror = 9999
        raise error

    monkeypatch.setattr(Path, "symlink_to", unrelated)
    unrelated_cno: list[str] = []
    unrelated_status, unrelated_errors, _ = _VALIDATOR.validate_path(
        control_cno=unrelated_cno
    )
    assert unrelated_status == "observed-bad"
    assert unrelated_errors
    assert unrelated_cno == []

    def unsupported(self: Path, target: Path, target_is_directory: bool = False) -> None:
        raise NotImplementedError("symlink operation is not implemented")

    monkeypatch.setattr(Path, "symlink_to", unsupported)
    unsupported_cno: list[str] = []
    unsupported_status, unsupported_errors, _ = _VALIDATOR.validate_path(
        control_cno=unsupported_cno
    )
    assert unsupported_status == "observed-bad"
    assert unsupported_errors
    assert unsupported_cno == []
    monkeypatch.setattr(Path, "symlink_to", original)


def test_unrelated_notimplementederror_is_not_automatic_cno(monkeypatch) -> None:
    project = _VALIDATOR.load_project()

    def unsupported(self: Path, target: Path, target_is_directory: bool = False) -> None:
        raise NotImplementedError("symlink operation is not implemented")

    monkeypatch.setattr(Path, "symlink_to", unsupported)
    control_cno: list[str] = []
    status, errors, red_failures = _VALIDATOR.validate_path(control_cno=control_cno)

    assert status == "observed-bad"
    assert errors
    assert red_failures
    assert control_cno == []
    assert _VALIDATOR._fold_property_outcome(["unrelated setup failure"], control_cno) == "observed-bad"


def test_valid_active_binding_is_checked_without_promoting_current_state() -> None:
    project = _VALIDATOR.load_project()

    assert _VALIDATOR._positive_active_fixture(project) == []
    current = {
        record["item_id"]: record["state"]
        for record in project["state"]["records"]
    }
    assert current["FUT-003"] == "ACTIVE"
    assert current["FUT-001"] == "SEQUENCED"
    assert project["state"]["authoritative_planning_source"]["generation"] == project["authority_observation"]["generation"]


def test_active_binding_exactly_covers_planned_increments() -> None:
    project = _VALIDATOR.load_project()
    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["active_binding"]["increments"].pop()

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("exactly cover unique planned increments" in error for error in errors)


def test_planning_authority_binding_exactly_matches_active_planned_increments() -> None:
    project = _VALIDATOR.load_project()

    for mutate in (
        lambda planned: planned.pop(),
        lambda planned: planned.append(copy.deepcopy(planned[0])),
        lambda planned: planned[0].update(increment_id="FP-002"),
        lambda planned: planned[0].update(status="proven"),
    ):
        state = copy.deepcopy(project["state"])
        record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
        mutate(record["planned_increments"])

        errors = _VALIDATOR.validate_state_document(state, project)

        assert any(
            "exactly match unique active-not-proven planned increments" in error
            for error in errors
        )

    for malformed in (None, {}, "FP-001"):
        state = copy.deepcopy(project["state"])
        record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
        record["planned_increments"] = malformed

        errors = _VALIDATOR.validate_state_document(state, project)

        assert any(
            "exactly match unique active-not-proven planned increments" in error
            for error in errors
        )

    state = copy.deepcopy(project["state"])
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record.pop("planned_increments")

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any(
        "exactly match unique active-not-proven planned increments" in error
        for error in errors
    )


def test_proven_requires_complete_accepted_proof_contract() -> None:
    project = _VALIDATOR.load_project()

    assert _VALIDATOR._positive_proven_fixture(project) == []
    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["state"] = "PROVEN"
    record["transition_history"].append(
        {"from": "ACTIVE", "to": "PROVEN", "evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"]}
    )

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("complete proof contract" in error for error in errors)


def test_proven_evidence_must_be_retained_inside_repository() -> None:
    project = _VALIDATOR.load_project()
    state = _VALIDATOR._proven_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["proven_proof"]["proof_evidence_refs"] = [
        "https://example.invalid/proof.json"
    ]

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("lacks retained proof_evidence_refs" in error for error in errors)


def test_remote_reference_syntax_cannot_alias_a_local_repository_path(
    tmp_path: Path,
) -> None:
    project, root = _temporary_project(tmp_path)
    host = "local-alias.invalid"
    alias = root / "https:" / host
    alias.mkdir(parents=True)
    (alias / "authority.md").write_text("local alias", encoding="utf-8")
    (alias / "proof.json").write_text("local alias", encoding="utf-8")

    active = _VALIDATOR._active_state_fixture(project)
    active_record = next(item for item in active["records"] if item["item_id"] == "FUT-003")
    active_record["active_binding"]["increments"][0]["authoritative_refs"] = [
        f"https://{host}/authority.md"
    ]
    active_errors = _VALIDATOR.validate_state_document(active, project)

    proven = _VALIDATOR._proven_state_fixture(project)
    proven_record = next(item for item in proven["records"] if item["item_id"] == "FUT-003")
    proven_record["proven_proof"]["proof_evidence_refs"] = [
        f"https://{host}/proof.json"
    ]
    proven_errors = _VALIDATOR.validate_state_document(proven, project)

    assert any("authoritative reference https://" in error for error in active_errors)
    assert any("lacks retained proof_evidence_refs" in error for error in proven_errors)
    assert _VALIDATOR._repository_path_exists(
        project, "docs/development/FUTURE_CANDIDATES.md"
    )
    for reference in (
        "http://example.invalid/file",
        "ssh://example.invalid/file",
        "mailto:agent@example.invalid",
        "urn:sssf:planning",
        "git@example.invalid:owner/repository.git",
        "//example.invalid/file",
    ):
        assert not _VALIDATOR._repository_path_exists(project, reference)


def test_active_authoritative_symlink_to_outside_root_is_rejected(tmp_path: Path) -> None:
    project, root = _temporary_project(tmp_path)
    outside = tmp_path / "outside-active.md"
    outside.write_text("outside", encoding="utf-8")
    link = root / "docs" / "development" / "active-outside.md"
    _symlink_or_skip(link, outside)

    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    reference = link.relative_to(root).as_posix()
    record["active_binding"]["increments"][0]["authoritative_refs"] = [reference]

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any(f"authoritative reference {reference}" in error for error in errors)


def test_every_retained_proven_evidence_symlink_to_outside_root_is_rejected(
    tmp_path: Path,
) -> None:
    project, root = _temporary_project(tmp_path)
    state = _VALIDATOR._proven_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    fields = (
        "acceptance_evidence_refs",
        "implementation_evidence_refs",
        "proof_evidence_refs",
        "documentation_evidence_refs",
    )
    for field in fields:
        outside = tmp_path / f"{field}-outside.json"
        outside.write_text("outside", encoding="utf-8")
        link = root / "docs" / "development" / f"{field}-outside.json"
        _symlink_or_skip(link, outside)
        record["proven_proof"][field] = [link.relative_to(root).as_posix()]

    errors = _VALIDATOR.validate_state_document(state, project)

    for field in fields:
        assert any(f"lacks retained {field}" in error for error in errors)


def test_watched_red_controls_detect_symlink_only_containment_regression(
    monkeypatch,
) -> None:
    project = _VALIDATOR.load_project()

    def symlink_vulnerable(project: dict[str, object], reference: object) -> bool:
        if not isinstance(reference, str) or not reference:
            return False
        path_text = reference.split("#", 1)[0]
        path = Path(path_text)
        if (
            _VALIDATOR._is_remote_reference(path_text)
            or path.is_absolute()
            or ".." in path.parts
        ):
            return False
        return (project["root"] / path).is_file()

    monkeypatch.setattr(_VALIDATOR, "_repository_path_exists", symlink_vulnerable)

    control_cno: list[str] = []
    failures = _VALIDATOR._watched_red_controls(project, control_cno)
    if control_cno:
        assert failures == []
        assert set(control_cno) == {
            "symlink-escape-active-authoritative-reference",
            "symlink-escape-proven-acceptance-evidence",
            "symlink-escape-proven-implementation-evidence",
            "symlink-escape-proven-proof-evidence",
            "symlink-escape-proven-documentation-evidence",
        }
        return

    assert "symlink-escape-active-authoritative-reference" in failures
    assert "symlink-escape-proven-acceptance-evidence" in failures
    assert "symlink-escape-proven-implementation-evidence" in failures
    assert "symlink-escape-proven-proof-evidence" in failures
    assert "symlink-escape-proven-documentation-evidence" in failures


def test_active_branch_and_pr_identities_are_canonical() -> None:
    assert _VALIDATOR._valid_branch("fm/fp-001")
    assert _VALIDATOR._valid_pr_url("https://github.com/example/sssf/pull/101")
    for branch in (" bad ", "bad branch", "-bad", "bad..branch", "bad@{branch"):
        assert not _VALIDATOR._valid_branch(branch)
    for pr_url in (
        "not-a-pr",
        "http://github.com/example/sssf/pull/1",
        "https://github.com/example/sssf/pull/0",
        "https://github.com/example/sssf/pull/1?x=1",
        "https://github.com/example/sssf/pull/1#x",
    ):
        assert not _VALIDATOR._valid_pr_url(pr_url)


def test_proven_proof_is_rejected_outside_durable_proven_state() -> None:
    project = _VALIDATOR.load_project()
    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    evidence = ["docs/development/FUTURE_CANDIDATES.md"]
    record["proven_proof"] = {
        "accepted_implementation": True,
        "acceptance_evidence_refs": evidence,
        "implementation_evidence_refs": evidence,
        "proof_evidence_refs": evidence,
        "documentation_evidence_refs": evidence,
        "source_commit": "e" * 40,
        "source_tree": "f" * 40,
    }

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("PROVEN proof claim without legal PROVEN history" in error for error in errors)


def test_superseded_item_retains_valid_historical_proof() -> None:
    project = _VALIDATOR.load_project()

    assert _VALIDATOR._positive_superseded_proof_fixture(project) == []


def test_active_authoritative_references_must_resolve() -> None:
    project = _VALIDATOR.load_project()
    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["active_binding"]["increments"][0]["authoritative_refs"] = [
        "docs/does-not-exist.md"
    ]

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("authoritative reference docs/does-not-exist.md" in error for error in errors)


def test_active_authoritative_references_cannot_escape_repository(
    tmp_path: Path, monkeypatch
) -> None:
    project = _VALIDATOR.load_project()
    outside = tmp_path / "outside.md"
    outside.write_text("outside", encoding="utf-8")
    link = _VALIDATOR.ROOT / "active-reference-test-link"
    original_resolve = Path.resolve

    def resolve_with_escape(path: Path, strict: bool = False) -> Path:
        if path == link:
            return outside
        return original_resolve(path, strict=strict)

    monkeypatch.setattr(Path, "resolve", resolve_with_escape)
    for reference in (
        "https://example.invalid/authority.md",
        str(outside),
        "../authority.md",
        link.name,
    ):
        assert not _VALIDATOR._repository_path_exists(project, reference)


def test_deferred_exit_matches_return_state_recorded_on_entry() -> None:
    project = _VALIDATOR.load_project()

    assert _VALIDATOR._positive_deferred_fixture(project) == []
    state = copy.deepcopy(project["state"])
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    evidence = ["docs/development/FUTURE_CANDIDATES.md"]
    record["state"] = "DECIDED"
    record["transition_history"].extend(
        [
            {"from": "SEQUENCED", "to": "DEFERRED", "return_to": "SEQUENCED", "evidence_refs": evidence},
            {"from": "DEFERRED", "to": "DECIDED", "return_to": "DECIDED", "evidence_refs": evidence},
        ]
    )

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("deferred re-entry" in error for error in errors)


def test_unknown_and_skipped_transitions_are_rejected() -> None:
    project = _VALIDATOR.load_project()
    unknown = copy.deepcopy(project)
    record = next(item for item in unknown["state"]["records"] if item["item_id"] == "FUT-003")
    record["transition_history"][1]["to"] = "UNKNOWN"

    status, errors = _VALIDATOR.validate_project(unknown, run_controls=False)

    assert status == "observed-bad"
    assert any("illegal/unknown/skipped transition" in error for error in errors)


def test_duplicate_adr_identity_is_rejected_without_renumbering_historical_0003() -> None:
    project = _VALIDATOR.load_project()
    project["adr_documents"]["ADR-0007-DUPLICATE.md"] = "# ADR-0007 — duplicate\n"

    status, errors = _VALIDATOR.validate_project(project, run_controls=False)

    assert status == "observed-bad"
    assert any("duplicate or missing ADR-0007 identity" in error for error in errors)
    assert not any("ADR-0003" in error for error in errors)


def test_validator_does_not_write_project_files(tmp_path: Path) -> None:
    project = _VALIDATOR.load_project()
    before = {
        path: path.read_bytes()
        for path in (
            _VALIDATOR.ROOT / _VALIDATOR.SURFACE_PATHS["state"],
            _VALIDATOR.ROOT / _VALIDATOR.SURFACE_PATHS["roadmap"],
        )
    }

    status, errors = _VALIDATOR.validate_project(project)

    assert status == "observed-good", errors
    assert all(path.read_bytes() == content for path, content in before.items())
    assert not list(tmp_path.iterdir())
