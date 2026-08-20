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


def _temporary_project(tmp_path: Path) -> tuple[dict[str, object], Path]:
    project = _VALIDATOR.load_project()
    root = tmp_path / "project"
    project["root"] = root
    _VALIDATOR._materialize_fixture_references(project["state"], root)
    return project, root


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
    link.symlink_to(outside)

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
        link.symlink_to(outside)
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

    failures = _VALIDATOR._watched_red_controls(project)

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
