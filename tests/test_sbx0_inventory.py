"""Durable SBX-0 handoff identity and watched-red coverage."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


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


@pytest.mark.parametrize("malformed_scope", [None, 7])
def test_malformed_owner_classification_scope_is_rejected(
    tmp_path: Path, malformed_scope: object
) -> None:
    document = json.loads(_VALIDATOR.DEFAULT_INVENTORY.read_text(encoding="utf-8"))
    document["owners"][0]["fact_classifications"] = malformed_scope
    mutated = tmp_path / "inventory.json"
    mutated.write_text(json.dumps(document), encoding="utf-8")

    status, errors, _ = _VALIDATOR.validate_path(
        mutated, verify_inventory_digest=False
    )

    assert status == "observed-bad"
    assert any(
        "fact_classifications is not a unique closed classification list" in error
        for error in errors
    )


@pytest.mark.parametrize(
    ("field", "malformed_value", "expected_error"),
    [
        ("fact_id", [], "has no bounded fact_id"),
        ("source_classification", [], "has unknown source classification"),
        ("classification", [], "has unknown classification"),
        ("owner_id", [], "has no singular registered owner"),
    ],
)
def test_malformed_fact_fields_are_rejected(
    tmp_path: Path, field: str, malformed_value: object, expected_error: str
) -> None:
    document = json.loads(_VALIDATOR.DEFAULT_INVENTORY.read_text(encoding="utf-8"))
    document["facts"][0][field] = malformed_value
    mutated = tmp_path / "inventory.json"
    mutated.write_text(json.dumps(document), encoding="utf-8")

    status, errors, _ = _VALIDATOR.validate_path(
        mutated, verify_inventory_digest=False
    )

    assert status == "observed-bad"
    assert any(expected_error in error for error in errors)


@pytest.mark.parametrize(
    ("section", "index", "expected_error"),
    [
        ("source_observations", 0, "source observation sbx0.observation.001 has no singular owner"),
        ("source_verifier_gap", None, "source verifier gap has no singular owner"),
        ("obligations", 0, "obligation sbx1.obligation.001 has no singular registered owner"),
        ("deferred_items", 0, "deferred item sbx0.deferred.ambiguity.01 has no owner"),
        ("recommendations", 0, "recommendation sbx0.recommendation.01 has no owner"),
    ],
)
def test_malformed_owner_references_are_rejected(
    tmp_path: Path, section: str, index: int | None, expected_error: str
) -> None:
    document = json.loads(_VALIDATOR.DEFAULT_INVENTORY.read_text(encoding="utf-8"))
    target = document[section] if index is None else document[section][index]
    target["owner_id"] = []
    mutated = tmp_path / "inventory.json"
    mutated.write_text(json.dumps(document), encoding="utf-8")

    status, errors, _ = _VALIDATOR.validate_path(
        mutated, verify_inventory_digest=False
    )

    assert status == "observed-bad"
    assert expected_error in errors


def test_unreadable_mutable_source_is_cno(tmp_path: Path) -> None:
    missing = tmp_path / "report.md"
    status, errors, _ = _VALIDATOR.validate_path(
        _VALIDATOR.DEFAULT_INVENTORY, source_report=missing
    )
    assert status == "could-not-observe"
    assert any("could not be observed" in error for error in errors)


def test_source_unreadability_preserves_property_local_three_valued_precedence(
    tmp_path: Path, monkeypatch
) -> None:
    readable = tmp_path / "report.md"
    readable.write_text("matching source report\n", encoding="utf-8")
    source_bytes = readable.read_bytes()
    monkeypatch.setattr(
        _VALIDATOR, "EXPECTED_REPORT_SHA", hashlib.sha256(source_bytes).hexdigest()
    )
    monkeypatch.setattr(_VALIDATOR, "EXPECTED_REPORT_BYTES", len(source_bytes))
    monkeypatch.setattr(
        _VALIDATOR, "EXPECTED_REPORT_LINES", len(source_bytes.decode().splitlines())
    )

    document = json.loads(_VALIDATOR.DEFAULT_INVENTORY.read_text(encoding="utf-8"))
    document["source_snapshot"].update(
        {
            "content_sha256": _VALIDATOR.EXPECTED_REPORT_SHA,
            "byte_length": _VALIDATOR.EXPECTED_REPORT_BYTES,
            "line_count": _VALIDATOR.EXPECTED_REPORT_LINES,
        }
    )
    valid = tmp_path / "valid-inventory.json"
    valid.write_text(json.dumps(document), encoding="utf-8")
    contradictory_document = json.loads(json.dumps(document))
    contradictory_document["facts"][0]["owner_id"] = "agent-backend"
    contradictory = tmp_path / "contradictory-inventory.json"
    contradictory.write_text(json.dumps(contradictory_document), encoding="utf-8")
    missing = tmp_path / "missing-report.md"

    contradiction_unreadable = _VALIDATOR.validate_path(
        contradictory, source_report=missing, verify_inventory_digest=False
    )
    valid_unreadable = _VALIDATOR.validate_path(
        valid, source_report=missing, verify_inventory_digest=False
    )
    contradiction_readable = _VALIDATOR.validate_path(
        contradictory, source_report=readable, verify_inventory_digest=False
    )
    valid_readable = _VALIDATOR.validate_path(
        valid, source_report=readable, verify_inventory_digest=False
    )

    # 1. A deterministic contradiction plus source CNO remains FAIL.
    assert contradiction_unreadable[0] == "observed-bad"
    assert any("does not govern classification" in e for e in contradiction_unreadable[1])
    assert any("could not be observed" in e for e in contradiction_unreadable[1])
    # 2. Source unreadability by itself remains CNO.
    assert valid_unreadable[0] == "could-not-observe"
    assert all("does not govern classification" not in e for e in valid_unreadable[1])
    # 3. A contradiction plus readable confirming source remains FAIL.
    assert contradiction_readable[0] == "observed-bad"
    assert any("does not govern classification" in e for e in contradiction_readable[1])
    assert all("source report" not in e for e in contradiction_readable[1])
    # 4. Fully readable, non-contradictory evidence retains PASS eligibility.
    assert valid_readable[0] == "observed-good"
    assert valid_readable[1] == []
    # 5. Adding source unreadability cannot erase or downgrade a known failure.
    assert contradiction_readable[0] == contradiction_unreadable[0]
    # 6. One property's failure does not fabricate failure for the CNO property.
    assert not any(
        "source report content digest mismatch" in e
        or "source report byte length mismatch" in e
        or "source report line count mismatch" in e
        for e in contradiction_unreadable[1]
    )


def test_source_content_mismatch_is_observed_bad(tmp_path: Path) -> None:
    changed = tmp_path / "report.md"
    changed.write_text("changed source generation\n", encoding="utf-8")
    status, errors, _ = _VALIDATOR.validate_path(
        _VALIDATOR.DEFAULT_INVENTORY, source_report=changed
    )
    assert status == "observed-bad"
    assert any("content digest mismatch" in error for error in errors)
