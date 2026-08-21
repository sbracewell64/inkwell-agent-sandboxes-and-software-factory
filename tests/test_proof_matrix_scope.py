"""Regression controls for the B4-002 historical production-boundary proof."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "validation"))

import check_ci_contract  # noqa: E402


def test_b4_002_production_integration_evidence_is_head_scoped() -> None:
    """Historical byte identity cannot qualify current or global production."""
    document = json.loads((ROOT / "ci" / "checks.json").read_text(encoding="utf-8"))
    subject = document["verification_contract"]["proof_subjects"][0]

    assert check_ci_contract.proof_scope_errors(document) == []
    assert check_ci_contract.b4_002_scope_authorization(
        subject, check_ci_contract.B4_002_HISTORICAL_CONSUMPTION
    ) == "PASS"

    # Watched red: a different evaluation head and a narrowed file set cannot
    # reuse the historical PASS.
    wrong_head = copy.deepcopy(subject)
    wrong_head["evaluation"]["head"] = "0" * 40
    assert check_ci_contract.b4_002_scope_authorization(
        wrong_head, check_ci_contract.B4_002_HISTORICAL_CONSUMPTION
    ) == "NON_PASS"

    wrong_files = copy.deepcopy(subject)
    wrong_files["evaluation"]["files"] = wrong_files["evaluation"]["files"][:-1]
    assert check_ci_contract.b4_002_scope_authorization(
        wrong_files, check_ci_contract.B4_002_HISTORICAL_CONSUMPTION
    ) == "NON_PASS"

    # Watched red: this proof has no standing-current or global authorization.
    assert check_ci_contract.b4_002_scope_authorization(
        subject, "current-production-qualification"
    ) == "NON_PASS"
    assert check_ci_contract.b4_002_scope_authorization(
        subject, "global-production-qualification"
    ) == "NON_PASS"
