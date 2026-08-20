#!/usr/bin/env python3
"""Validate the durable SBX-0 semantics handoff and watched-red controls.

The fleet-local report is evidence input, not a repository authority.  This
validator checks the durable inventory's pinned source generation/content
identity, complete fact/obligation coverage, singular owner binding, and
three-valued boundaries.  It can optionally replay the mutable report path;
absence or unreadability of that path is CNO, never PASS.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "docs" / "reference" / "SBX-0_SEMANTICS_INVENTORY.json"

OBSERVATIONS = ("observed-good", "observed-bad", "could-not-observe")
CLASSIFICATIONS = (
    "provider-neutral-semantic",
    "exe.dev/provider-mechanism",
    "limitation",
    "obsolete-artifact",
    "external-dependency",
    "could-not-observe",
)
SOURCE_CLASSIFICATION_MAP = {
    "REQUIRED_PROVIDER_NEUTRAL_SEMANTIC": "provider-neutral-semantic",
    "PROVIDER_SPECIFIC_MECHANISM": "exe.dev/provider-mechanism",
    "LIMITATION": "limitation",
    "COULD_NOT_OBSERVE": "could-not-observe",
    "OBSOLETE_ARTIFACT": "obsolete-artifact",
    "EXTERNAL_DEPENDENCY": "external-dependency",
}

EXPECTED_SCHEMA = "sssf.sbx-0-handoff.v1"
EXPECTED_INVENTORY_ID = "sssf-sbx-0-provider-semantics"
EXPECTED_BASE_SHA = "b902cdcecd65c8ba03031875297d31e990f12c11"
EXPECTED_REPORT_CODE_SHA = "bee9296a4c94b1dc3da6991acd1755a91fa681eb"
EXPECTED_PLANNING_SHA = "54ef67c3849b24b1eaa6e10d2ed0e49a09464a70"
EXPECTED_REPORT_SHA = "2d16bee3db4c46062b460dfbd6752339e85228a3b6f2c5002313a4f06dc663b3"
EXPECTED_REPORT_BYTES = 42031
EXPECTED_REPORT_LINES = 221
EXPECTED_INVENTORY_DIGEST = "e1c3d693b6e81b84405fb5402fc7ca071a49679c1fb8dc0b01b82069c381c974"
EXPECTED_RULING = "SOL-FM-SSSF-SBX1-POSTMERGE-20260820-1203"

EXPECTED_FACT_IDS = tuple(f"sbx0.fact.{number:03d}" for number in range(1, 58))
EXPECTED_OBLIGATION_IDS = (
    tuple(f"sbx1.obligation.{number:03d}" for number in range(1, 10))
    + (
        "sbx0.obligation.010",
        "sbx0.obligation.011",
        "sbx0.obligation.012",
        "sbx0.obligation.013",
        "sbx0.obligation.014",
        "sbx0.obligation.015",
    )
    + tuple(
        f"sbx1.obligation.fake.{name}"
        for name in (
            "create-ambiguity",
            "identity-mismatch",
            "exec-bounds",
            "provider-client-cleanup",
            "workload-leak",
            "artifact-missing",
            "artifact-tamper",
            "artifact-overflow",
            "git-ancestry",
            "partial-stop",
            "destroy-authorization",
            "destroy-residual",
            "inspect-unreachable",
            "already-absent",
            "duplicate-reconcile",
            "boundary-interruption",
            "secret-retirement",
            "aggregate-precedence",
        )
    )
)
EXPECTED_DEFERRED_IDS = tuple(
    f"sbx0.deferred.ambiguity.{number:02d}" for number in range(1, 17)
) + tuple(f"sbx0.deferred.qualification.{number:02d}" for number in range(1, 18))
EXPECTED_RECOMMENDATION_IDS = tuple(
    f"sbx0.recommendation.{number:02d}" for number in range(1, 9)
)
EXPECTED_SOURCE_OBSERVATION_IDS = tuple(
    f"sbx0.observation.{number:03d}" for number in range(1, 8)
)

OWNER_REQUIRED_PATHS = {
    "sandbox-contract": "adws/adw_modules/sandbox_provider.py",
    "process-supervisor": "adws/adw_modules/subprocess_supervisor.py",
    "evidence-manifest": "tools/evidence_manifest.py",
    "gate-outcome": "adws/adw_modules/data_types.py",
    "source-custody": "just/sandbox/lifecycle/fill.just",
    "legacy-exedev-lifecycle": "just/sandbox/lifecycle",
    "observability-trace": "adws/adw_modules/tracer.py",
    "security-boundary": "docs/architecture/SECURITY_AND_CREDENTIALS.md",
    "agent-backend": "adws/adw_modules/agents.py",
    "source-of-truth-policy": "docs/reference/SOURCE_OF_TRUTH.md",
    "planning-contract": "docs/development/ROADMAP.md",
    "verification-controls": "docs/validation/check_sbx0_inventory.py",
    "sbx0-handoff-record": "docs/reference/SBX-0_SEMANTICS_INVENTORY.json",
}


def _strict_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        document = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_strict_object_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        return None, [f"inventory could not be observed: {error}"]
    if not isinstance(document, dict):
        return None, ["inventory top level must be an object"]
    return document, []


def _expect_keys(
    value: dict[str, Any], expected: set[str], label: str, errors: list[str]
) -> None:
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{label} missing keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")


def _expect_observation(value: Any, label: str, errors: list[str]) -> None:
    if value not in OBSERVATIONS:
        errors.append(f"{label} is not a closed three-valued observation: {value!r}")


def _canonical_digest(document: dict[str, Any]) -> str:
    projection = copy.deepcopy(document)
    projection["inventory_content_sha256"] = None
    return hashlib.sha256(
        json.dumps(projection, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    ).hexdigest()


def _validate_source_snapshot(
    document: dict[str, Any], errors: list[str]
) -> None:
    source = document.get("source_snapshot")
    if not isinstance(source, dict):
        errors.append("source_snapshot is not an object")
        return
    _expect_keys(
        source,
        {
            "logical_path",
            "path_kind",
            "generation_id",
            "canonical_code_sha_examined",
            "planning_ref_examined",
            "planning_sha_examined",
            "content_sha256",
            "byte_length",
            "line_count",
            "content_observation",
            "content_observation_reason",
        },
        "source_snapshot",
        errors,
    )
    expected = {
        "logical_path": "data/sssf-sbx-0/report.md",
        "path_kind": "mutable-fleet-local-evidence-input",
        "generation_id": f"sbx-0-report/v1@code-{EXPECTED_REPORT_CODE_SHA}@planning-{EXPECTED_PLANNING_SHA}",
        "canonical_code_sha_examined": EXPECTED_REPORT_CODE_SHA,
        "planning_ref_examined": "origin/planning/future-sssf",
        "planning_sha_examined": EXPECTED_PLANNING_SHA,
        "content_sha256": EXPECTED_REPORT_SHA,
        "byte_length": EXPECTED_REPORT_BYTES,
        "line_count": EXPECTED_REPORT_LINES,
        "content_observation": "observed-good",
    }
    for key, expected_value in expected.items():
        if source.get(key) != expected_value:
            errors.append(
                f"source_snapshot {key} mismatch: expected {expected_value!r}, "
                f"got {source.get(key)!r}"
            )
    if not isinstance(source.get("content_observation_reason"), str) or not source.get(
        "content_observation_reason"
    ):
        errors.append("source_snapshot content observation has no reason")


def _validate_authority_boundary(
    document: dict[str, Any], errors: list[str]
) -> None:
    boundary = document.get("authority_boundary")
    if not isinstance(boundary, dict):
        errors.append("authority_boundary is not an object")
        return
    expected_keys = {
        "ruling_id",
        "starting_sssf_main_sha",
        "source_report_is_authority",
        "source_report_role",
        "source_report_copy_committed",
        "sbx0_exit_observation",
        "sbx1_activation_observation",
        "sbx1_acceptance_observation",
        "real_provider_custody_observation",
        "windows_host_observation",
        "independent_semantic_review_observation",
        "landing_authorization_observation",
        "sbx2_unlock_observation",
        "wayfinder_observation",
        "dsh_observation",
    }
    _expect_keys(boundary, expected_keys, "authority_boundary", errors)
    if boundary.get("ruling_id") != EXPECTED_RULING:
        errors.append("authority boundary ruling is stale or wrong")
    if boundary.get("starting_sssf_main_sha") != EXPECTED_BASE_SHA:
        errors.append("authority boundary starting SSSF generation is stale or wrong")
    if boundary.get("source_report_is_authority") is not False:
        errors.append("mutable source report was incorrectly made durable authority")
    if boundary.get("source_report_copy_committed") is not False:
        errors.append("mutable source report was incorrectly copied as authority")
    for key in expected_keys - {"ruling_id", "starting_sssf_main_sha", "source_report_is_authority", "source_report_role", "source_report_copy_committed"}:
        _expect_observation(boundary.get(key), f"authority_boundary.{key}", errors)
        if boundary.get(key) != "could-not-observe":
            errors.append(f"promotion boundary {key} was narrowed from CNO")
    if not isinstance(boundary.get("source_report_role"), str) or "mutable" not in boundary.get(
        "source_report_role", ""
    ).lower():
        errors.append("source report role does not preserve mutable evidence-only boundary")


def _validate_source_observations(
    document: dict[str, Any], owners: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    context = document.get("source_context")
    if not isinstance(context, dict):
        errors.append("source_context is not an object")
    else:
        _expect_keys(
            context,
            {"repository", "mode", "executive_conclusion", "constitutional_boundary", "evidence_precedence"},
            "source_context",
            errors,
        )
        for key in ("repository", "mode", "executive_conclusion", "constitutional_boundary", "evidence_precedence"):
            if not isinstance(context.get(key), str) or not context.get(key):
                errors.append(f"source_context.{key} is empty")
    observations = document.get("source_observations")
    if not isinstance(observations, list):
        errors.append("source_observations is not a list")
    else:
        _validate_coverage(document, errors, "required_source_observation_ids", EXPECTED_SOURCE_OBSERVATION_IDS, observations, "observation_id")
        expected_keys = {"observation_id", "source_line", "command", "observation", "statement", "owner_id"}
        for index, item in enumerate(observations):
            if not isinstance(item, dict):
                errors.append(f"source observation {index} is not an object")
                continue
            _expect_keys(item, expected_keys, f"source observation {index}", errors)
            if index >= len(EXPECTED_SOURCE_OBSERVATION_IDS) or item.get("observation_id") != EXPECTED_SOURCE_OBSERVATION_IDS[index]:
                errors.append(f"source observation order/identity drift at index {index}")
            _expect_observation(item.get("observation"), f"source observation {item.get('observation_id')}.observation", errors)
            if item.get("owner_id") not in owners:
                errors.append(f"source observation {item.get('observation_id')} has no singular owner")
            if not all(isinstance(item.get(key), str) and item.get(key) for key in ("command", "statement")):
                errors.append(f"source observation {item.get('observation_id')} is missing command/statement")
    gap = document.get("source_verifier_gap")
    if not isinstance(gap, dict):
        errors.append("source_verifier_gap is not an object")
    else:
        _expect_keys(gap, {"observation", "statement", "owner_id"}, "source_verifier_gap", errors)
        _expect_observation(gap.get("observation"), "source_verifier_gap.observation", errors)
        if gap.get("observation") != "could-not-observe":
            errors.append("source verifier gap was narrowed from CNO")
        if gap.get("owner_id") not in owners:
            errors.append("source verifier gap has no singular owner")


def _validate_owner_registry(
    document: dict[str, Any], errors: list[str]
) -> dict[str, dict[str, Any]]:
    owners = document.get("owners")
    if not isinstance(owners, list) or not owners:
        errors.append("owner registry is empty or not a list")
        return {}
    by_id: dict[str, dict[str, Any]] = {}
    for index, owner in enumerate(owners):
        if not isinstance(owner, dict):
            errors.append(f"owner {index} is not an object")
            continue
        _expect_keys(
            owner,
            {"owner_id", "kind", "path", "scope", "fact_classifications"},
            f"owner {index}",
            errors,
        )
        owner_id = owner.get("owner_id")
        if not isinstance(owner_id, str) or not owner_id:
            errors.append(f"owner {index} has no bounded owner_id")
            continue
        if owner_id in by_id:
            errors.append(f"duplicate authority owner_id: {owner_id}")
        path = owner.get("path")
        if not isinstance(path, str) or Path(path).is_absolute() or ".." in Path(path).parts:
            errors.append(f"owner {owner_id} path is not a safe repository path")
        elif not (ROOT / path).exists():
            errors.append(f"owner {owner_id} path could not be observed: {path}")
        if not isinstance(owner.get("scope"), str) or not owner.get("scope"):
            errors.append(f"owner {owner_id} has no scope")
        fact_classifications = owner.get("fact_classifications")
        if (
            not isinstance(fact_classifications, list)
            or any(
                not isinstance(value, str) or value not in CLASSIFICATIONS
                for value in fact_classifications
            )
            or len(fact_classifications) != len(set(fact_classifications))
        ):
            errors.append(
                f"owner {owner_id} fact_classifications is not a unique closed classification list"
            )
            fact_classifications = []
        by_id[owner_id] = {**owner, "fact_classifications": fact_classifications}
    for owner_id, path in OWNER_REQUIRED_PATHS.items():
        owner = by_id.get(owner_id)
        if owner is None:
            errors.append(f"required owner is missing: {owner_id}")
        elif owner.get("path") != path:
            errors.append(f"owner {owner_id} path changed from its authoritative owner")
    return by_id


def _validate_coverage(
    document: dict[str, Any],
    errors: list[str],
    field: str,
    expected: tuple[str, ...],
    actual_items: list[dict[str, Any]],
    item_key: str,
) -> None:
    coverage = document.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("coverage is not an object")
        return
    actual_coverage = coverage.get(field)
    if actual_coverage != list(expected):
        errors.append(
            f"coverage {field} dropped/reordered entries: expected {len(expected)}, "
            f"got {len(actual_coverage) if isinstance(actual_coverage, list) else actual_coverage!r}"
        )
    actual_ids = tuple(item.get(item_key) for item in actual_items if isinstance(item, dict))
    if actual_ids != expected:
        errors.append(
            f"{item_key} coverage is incomplete or reordered: expected {len(expected)}, got {len(actual_ids)}"
        )
    if len(set(actual_ids)) != len(actual_ids):
        errors.append(f"duplicate {item_key} authority entries")


def _validate_facts(
    document: dict[str, Any], owners: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    facts = document.get("facts")
    if not isinstance(facts, list) or not facts:
        errors.append("fact inventory is empty or not a list")
        return
    _validate_coverage(document, errors, "required_fact_ids", EXPECTED_FACT_IDS, facts, "fact_id")
    expected_keys = {
        "fact_id",
        "source_line",
        "section",
        "source_classification",
        "classification",
        "source_observation",
        "statement",
        "evidence",
        "owner_id",
        "current_contract_observation",
        "current_contract_reason",
        "provider_qualification_observation",
        "provider_qualification_reason",
        "handoff_disposition",
        "obligation_ids",
    }
    for index, fact in enumerate(facts):
        if not isinstance(fact, dict):
            errors.append(f"fact {index} is not an object")
            continue
        _expect_keys(fact, expected_keys, f"fact {index}", errors)
        if index >= len(EXPECTED_FACT_IDS) or fact.get("fact_id") != EXPECTED_FACT_IDS[index]:
            errors.append(f"fact order/identity drift at index {index}: {fact.get('fact_id')!r}")
        source_class = fact.get("source_classification")
        if source_class not in SOURCE_CLASSIFICATION_MAP:
            errors.append(f"fact {fact.get('fact_id')} has unknown source classification")
        elif fact.get("classification") != SOURCE_CLASSIFICATION_MAP[source_class]:
            errors.append(f"fact {fact.get('fact_id')} classification projection changed")
        elif fact.get("classification") not in CLASSIFICATIONS:
            errors.append(f"fact {fact.get('fact_id')} has unknown classification")
        _expect_observation(fact.get("source_observation"), f"fact {fact.get('fact_id')}.source_observation", errors)
        _expect_observation(fact.get("current_contract_observation"), f"fact {fact.get('fact_id')}.current_contract_observation", errors)
        _expect_observation(fact.get("provider_qualification_observation"), f"fact {fact.get('fact_id')}.provider_qualification_observation", errors)
        if source_class == "COULD_NOT_OBSERVE" and fact.get("source_observation") != "could-not-observe":
            errors.append(f"explicit CNO fact {fact.get('fact_id')} was narrowed to a positive observation")
        if fact.get("provider_qualification_observation") != "could-not-observe":
            errors.append(f"fact {fact.get('fact_id')} incorrectly claims provider qualification")
        owner_id = fact.get("owner_id")
        if owner_id not in owners:
            errors.append(f"fact {fact.get('fact_id')} has no singular registered owner")
        elif fact.get("classification") not in owners[owner_id].get(
            "fact_classifications", []
        ):
            errors.append(
                f"fact {fact.get('fact_id')} owner {owner_id} does not govern "
                f"classification {fact.get('classification')}"
            )
        for text_key in ("statement", "evidence", "current_contract_reason", "provider_qualification_reason", "handoff_disposition"):
            if not isinstance(fact.get(text_key), str) or not fact.get(text_key):
                errors.append(f"fact {fact.get('fact_id')} missing {text_key}")
        if not isinstance(fact.get("obligation_ids"), list) or not fact.get("obligation_ids"):
            errors.append(f"fact {fact.get('fact_id')} dropped its obligation trace")


def _validate_obligations(
    document: dict[str, Any], owners: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    obligations = document.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        errors.append("obligation inventory is empty or not a list")
        return
    _validate_coverage(document, errors, "required_obligation_ids", EXPECTED_OBLIGATION_IDS, obligations, "obligation_id")
    expected_keys = {"obligation_id", "slug", "statement", "owner_id", "binding_observation", "qualification_observation", "qualification_reason"}
    for index, obligation in enumerate(obligations):
        if not isinstance(obligation, dict):
            errors.append(f"obligation {index} is not an object")
            continue
        _expect_keys(obligation, expected_keys, f"obligation {index}", errors)
        if index >= len(EXPECTED_OBLIGATION_IDS) or obligation.get("obligation_id") != EXPECTED_OBLIGATION_IDS[index]:
            errors.append(f"obligation order/identity drift at index {index}")
        _expect_observation(obligation.get("binding_observation"), f"obligation {obligation.get('obligation_id')}.binding_observation", errors)
        _expect_observation(obligation.get("qualification_observation"), f"obligation {obligation.get('obligation_id')}.qualification_observation", errors)
        if obligation.get("qualification_observation") != "could-not-observe":
            errors.append(f"obligation {obligation.get('obligation_id')} narrowed qualification CNO")
        if obligation.get("owner_id") not in owners:
            errors.append(f"obligation {obligation.get('obligation_id')} has no singular registered owner")
        if not all(isinstance(obligation.get(key), str) and obligation.get(key) for key in ("slug", "statement", "qualification_reason")):
            errors.append(f"obligation {obligation.get('obligation_id')} has an empty identity/statement/reason")


def _validate_deferred_and_recommendations(
    document: dict[str, Any], owners: dict[str, dict[str, Any]], errors: list[str]
) -> None:
    deferred = document.get("deferred_items")
    if not isinstance(deferred, list):
        errors.append("deferred_items is not a list")
    else:
        _validate_coverage(document, errors, "required_deferred_item_ids", EXPECTED_DEFERRED_IDS, deferred, "item_id")
        for item in deferred:
            if not isinstance(item, dict):
                errors.append("deferred item is not an object")
                continue
            _expect_observation(item.get("observation"), f"deferred {item.get('item_id')}.observation", errors)
            if item.get("observation") != "could-not-observe":
                errors.append(f"deferred item {item.get('item_id')} narrowed CNO")
            if item.get("owner_id") not in owners:
                errors.append(f"deferred item {item.get('item_id')} has no owner")
    recommendations = document.get("recommendations")
    if not isinstance(recommendations, list):
        errors.append("recommendations is not a list")
    else:
        _validate_coverage(document, errors, "required_recommendation_ids", EXPECTED_RECOMMENDATION_IDS, recommendations, "recommendation_id")
        for recommendation in recommendations:
            if not isinstance(recommendation, dict):
                errors.append("recommendation is not an object")
                continue
            _expect_observation(recommendation.get("observation"), f"recommendation {recommendation.get('recommendation_id')}.observation", errors)
            if recommendation.get("observation") != "could-not-observe":
                errors.append(f"recommendation {recommendation.get('recommendation_id')} narrowed CNO")
            if recommendation.get("owner_id") not in owners:
                errors.append(f"recommendation {recommendation.get('recommendation_id')} has no owner")


def validate_document(
    document: dict[str, Any],
    *,
    source_report: Path | None = None,
    verify_inventory_digest: bool = True,
) -> tuple[str, list[str]]:
    """Return one of the three observations for the durable validation claim."""
    errors: list[str] = []
    _expect_keys(
        document,
        {
            "schema_version",
            "inventory_id",
            "inventory_revision",
            "publication_status",
            "authority_boundary",
            "source_context",
            "source_snapshot",
            "source_observations",
            "source_verifier_gap",
            "current_reconciliation",
            "classification_vocabulary",
            "observation_vocabulary",
            "owners",
            "facts",
            "obligations",
            "deferred_items",
            "recommendations",
            "coverage",
            "non_goals",
            "inventory_content_sha256",
        },
        "inventory",
        errors,
    )
    if document.get("schema_version") != EXPECTED_SCHEMA:
        errors.append("inventory schema generation is stale or unsupported")
    if document.get("inventory_id") != EXPECTED_INVENTORY_ID:
        errors.append("inventory identity is wrong")
    if document.get("inventory_revision") != 1:
        errors.append("inventory revision is unsupported")
    if document.get("publication_status") != "published-handoff-only-cno-for-promotions":
        errors.append("publication status implies an unauthorized promotion")
    if document.get("classification_vocabulary") != list(CLASSIFICATIONS):
        errors.append("classification vocabulary dropped or reordered a source classification")
    if document.get("observation_vocabulary") != list(OBSERVATIONS):
        errors.append("observation vocabulary is not the closed three-valued set")
    if verify_inventory_digest:
        if document.get("inventory_content_sha256") != EXPECTED_INVENTORY_DIGEST:
            errors.append("inventory content digest does not match the published generation")
        elif _canonical_digest(document) != EXPECTED_INVENTORY_DIGEST:
            errors.append("inventory content digest mismatch: fact/obligation content changed")
    _validate_authority_boundary(document, errors)
    _validate_source_snapshot(document, errors)
    owners = _validate_owner_registry(document, errors)
    _validate_source_observations(document, owners, errors)
    _validate_facts(document, owners, errors)
    _validate_obligations(document, owners, errors)
    _validate_deferred_and_recommendations(document, owners, errors)

    if source_report is not None:
        try:
            source_bytes = source_report.read_bytes()
        except (OSError, UnicodeError) as error:
            return (
                "observed-bad" if errors else "could-not-observe",
                errors + [f"source report could not be observed: {error}"],
            )
        if hashlib.sha256(source_bytes).hexdigest() != EXPECTED_REPORT_SHA:
            errors.append("source report content digest mismatch")
        if len(source_bytes) != EXPECTED_REPORT_BYTES:
            errors.append("source report byte length mismatch")
        try:
            source_lines = source_bytes.decode("utf-8").splitlines()
        except UnicodeDecodeError:
            errors.append("source report is not readable UTF-8")
        else:
            if len(source_lines) != EXPECTED_REPORT_LINES:
                errors.append("source report line count mismatch")

    return ("observed-bad" if errors else "observed-good"), errors


def _watched_red_controls(document: dict[str, Any]) -> list[str]:
    """Return control names that failed to go red; mutations stay in memory."""
    controls: list[tuple[str, Any, str]] = []
    stale = copy.deepcopy(document)
    stale["source_snapshot"]["generation_id"] = "sbx-0-report/v0"
    controls.append(("stale-source-generation", stale, "source_snapshot generation_id mismatch"))
    digest = copy.deepcopy(document)
    digest["source_snapshot"]["content_sha256"] = "0" * 64
    controls.append(("content-digest-mismatch", digest, "source_snapshot content_sha256 mismatch"))
    duplicate = copy.deepcopy(document)
    duplicate["owners"].append(copy.deepcopy(duplicate["owners"][0]))
    controls.append(("duplicate-authority", duplicate, "duplicate authority owner_id"))
    wrong_owner = copy.deepcopy(document)
    wrong_owner["facts"][0]["owner_id"] = "agent-backend"
    controls.append(
        (
            "registered-incompatible-owner",
            wrong_owner,
            "fact sbx0.fact.001 owner agent-backend does not govern classification provider-neutral-semantic",
        )
    )
    dropped_fact = copy.deepcopy(document)
    dropped_fact["facts"].pop()
    dropped_fact["coverage"]["required_fact_ids"].pop()
    controls.append(("dropped-fact", dropped_fact, "fact_id coverage is incomplete"))
    dropped_obligation = copy.deepcopy(document)
    dropped_obligation["obligations"].pop()
    dropped_obligation["coverage"]["required_obligation_ids"].pop()
    controls.append(("dropped-obligation", dropped_obligation, "obligation_id coverage is incomplete"))
    cno_to_absence = copy.deepcopy(document)
    cno_to_absence["authority_boundary"]["sbx0_exit_observation"] = "absent"
    controls.append(("cno-to-absence", cno_to_absence, "sbx0_exit_observation is not a closed three-valued observation"))
    cno_to_pass = copy.deepcopy(document)
    cno_to_pass["authority_boundary"]["sbx1_acceptance_observation"] = "PASS"
    controls.append(("cno-to-pass", cno_to_pass, "sbx1_acceptance_observation is not a closed three-valued observation"))

    failed_to_red: list[str] = []
    for name, mutated, expected_error in controls:
        status, errors = validate_document(mutated, verify_inventory_digest=False)
        if status != "observed-bad" or not any(expected_error in error for error in errors):
            failed_to_red.append(name)
    return failed_to_red


def validate_path(
    path: Path,
    *,
    source_report: Path | None = None,
    verify_inventory_digest: bool = True,
) -> tuple[str, list[str], list[str]]:
    document, errors = _read_json(path)
    if document is None:
        return "could-not-observe", errors, []
    status, validation_errors = validate_document(
        document,
        source_report=source_report,
        verify_inventory_digest=verify_inventory_digest,
    )
    red_failures = _watched_red_controls(document) if not validation_errors else []
    if red_failures:
        validation_errors = [*validation_errors, "watched-red controls did not go red: " + ", ".join(red_failures)]
        status = "observed-bad"
    return status, validation_errors, red_failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--source-report", type=Path, default=None)
    args = parser.parse_args()
    status, errors, red_failures = validate_path(args.inventory.resolve(), source_report=args.source_report)
    print(f"SBX-0 semantics handoff validation: {status}")
    print(f"inventory: {args.inventory}")
    print("source replay: could-not-observe (not requested; mutable source is not authority)" if args.source_report is None else f"source replay: {status}")
    print("watched-red: stale-generation, content-digest, duplicate-authority, registered-incompatible-owner, dropped-fact, dropped-obligation, CNO-to-absence, CNO-to-PASS")
    if errors:
        for error in errors:
            print(f"- {error}")
        return 1 if status == "observed-bad" else 2
    print("owner-per-fact: singular registered classification-compatible authorities")
    print("coverage: 57 facts, 33 obligations, 33 deferred items, 8 recommendations")
    print("promotion boundary: SBX-0/SBX-1/provider/Windows/review/landing/SBX-2 remain CNO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
