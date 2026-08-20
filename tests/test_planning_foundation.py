"""Deterministic planning-foundation controls and watched-red coverage."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path


_VALIDATOR_PATH = Path(__file__).parents[1] / "docs" / "validation" / "check_planning_foundation.py"
_SPEC = importlib.util.spec_from_file_location("planning_foundation_validator", _VALIDATOR_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_VALIDATOR)


def test_canonical_foundation_and_all_watched_red_controls_pass() -> None:
    status, errors, red_failures = _VALIDATOR.validate_path()

    assert status == "observed-good", errors
    assert red_failures == []


def test_valid_active_binding_is_checked_without_promoting_current_state() -> None:
    project = _VALIDATOR.load_project()

    assert _VALIDATOR._positive_active_fixture(project) == []
    current = {
        record["item_id"]: record["state"]
        for record in project["state"]["records"]
    }
    assert current["FUT-003"] == "SEQUENCED"


def test_active_binding_exactly_covers_planned_increments() -> None:
    project = _VALIDATOR.load_project()
    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["active_binding"]["increments"].pop()

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("exactly cover unique planned increments" in error for error in errors)


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

    assert any("PROVEN proof claim outside" in error for error in errors)


def test_active_authoritative_references_must_resolve() -> None:
    project = _VALIDATOR.load_project()
    state = _VALIDATOR._active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["active_binding"]["increments"][0]["authoritative_refs"] = [
        "docs/does-not-exist.md"
    ]

    errors = _VALIDATOR.validate_state_document(state, project)

    assert any("authoritative reference docs/does-not-exist.md" in error for error in errors)


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
