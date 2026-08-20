"""Durable SBX-0 handoff identity and watched-red coverage."""

from __future__ import annotations

import importlib.util
import json
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


def test_provider_neutral_lifecycle_facts_use_compatible_authority() -> None:
    document = json.loads(_VALIDATOR.DEFAULT_INVENTORY.read_text(encoding="utf-8"))
    expected = {
        "sbx0.fact.001",
        "sbx0.fact.003",
        "sbx0.fact.012",
        "sbx0.fact.037",
        "sbx0.fact.044",
        "sbx0.fact.047",
        "sbx0.fact.049",
    }
    actual = {
        fact["fact_id"]
        for fact in document["facts"]
        if fact["owner_id"] == "sandbox-contract" and fact["fact_id"] in expected
    }

    status, errors, _ = _VALIDATOR.validate_path(_VALIDATOR.DEFAULT_INVENTORY)

    assert actual == expected
    assert status == "observed-good", errors


def test_registered_but_incompatible_fact_owner_is_rejected(tmp_path: Path) -> None:
    document = json.loads(_VALIDATOR.DEFAULT_INVENTORY.read_text(encoding="utf-8"))
    document["facts"][0]["owner_id"] = "agent-backend"
    mutated = tmp_path / "inventory.json"
    mutated.write_text(json.dumps(document), encoding="utf-8")

    status, errors, _ = _VALIDATOR.validate_path(
        mutated, verify_inventory_digest=False
    )

    expected = (
        "fact sbx0.fact.001 owner agent-backend does not govern "
        "classification provider-neutral-semantic"
    )
    assert status == "observed-bad"
    assert expected in errors
    assert not any("inventory content digest" in error for error in errors)


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
