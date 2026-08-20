"""Durable SBX-0 handoff identity and watched-red coverage."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_VALIDATOR_PATH = Path(__file__).parents[1] / "docs" / "validation" / "check_sbx0_inventory.py"
_SPEC = importlib.util.spec_from_file_location("sbx0_inventory_validator", _VALIDATOR_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_VALIDATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_VALIDATOR)


def test_inventory_is_exact_and_watched_red_controls_fire() -> None:
    status, errors, red_failures = _VALIDATOR.validate_path(_VALIDATOR.DEFAULT_INVENTORY)
    assert status == "observed-good", errors
    assert red_failures == []


def test_unreadable_mutable_source_is_cno(tmp_path: Path) -> None:
    missing = tmp_path / "report.md"
    status, errors, _ = _VALIDATOR.validate_path(
        _VALIDATOR.DEFAULT_INVENTORY, source_report=missing
    )
    assert status == "could-not-observe"
    assert any("could not be observed" in error for error in errors)


def test_source_content_mismatch_is_observed_bad(tmp_path: Path) -> None:
    changed = tmp_path / "report.md"
    changed.write_text("changed source generation\n", encoding="utf-8")
    status, errors, _ = _VALIDATOR.validate_path(
        _VALIDATOR.DEFAULT_INVENTORY, source_report=changed
    )
    assert status == "observed-bad"
    assert any("content digest mismatch" in error for error in errors)
