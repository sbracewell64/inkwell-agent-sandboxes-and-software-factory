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
