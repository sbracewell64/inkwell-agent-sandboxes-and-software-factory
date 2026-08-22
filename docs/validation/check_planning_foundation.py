#!/usr/bin/env python3
"""Validate the SSSF planning foundation without changing repository state.

This is the single deterministic validation owner for the planning/lifecycle
foundation. It reads the canonical lifecycle contract, the durable planning
state record, linked planning surfaces, and a pre-fetched Git tracking ref for
current planning authority. It performs no fetch, network, feed, watcher,
FirstMate, provider, or runtime action. Watched-red controls mutate only
in-memory copies; Git observation is read-only.
"""

from __future__ import annotations

import copy
import json
import posixpath
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SURFACE_PATHS = {
    "lifecycle": Path("docs/development/PLANNING_LIFECYCLE.md"),
    "state": Path("docs/development/PLANNING_STATE.json"),
    "increment_protocol": Path("docs/development/INCREMENT_PROTOCOL.md"),
    "candidates": Path("docs/development/FUTURE_CANDIDATES.md"),
    "roadmap": Path("docs/development/ROADMAP.md"),
    "adr_planning": Path(
        "docs/decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md"
    ),
    "adr_dsh": Path(
        "docs/decisions/ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md"
    ),
    "readme": Path("docs/README.md"),
    "manifest": Path("docs/manifest.yaml"),
    "increment": Path("docs/increments/FUT-003_PLANNING_FOUNDATION_REPAIR.md"),
    "bound1": Path("docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"),
    "boundedness_law": Path("docs/development/BOUNDEDNESS_LAW.md"),
    "file_map": Path("docs/reference/FILE_MAP.md"),
    "ci_manifest": Path("ci/checks.json"),
}

LIFECYCLE_OWNER = "docs/development/PLANNING_LIFECYCLE.md"
VALIDATION_OWNER = "docs/validation/check_planning_foundation.py"
LIFECYCLE_MARKER = "canonical transition contract owner: v1"
STATES = (
    "EXPLORE",
    "PRESERVE",
    "CANDIDATE",
    "DECIDED",
    "SEQUENCED",
    "ACTIVE",
    "PROVEN",
    "DEFERRED",
    "REJECTED",
    "SUPERSEDED",
)
TERMINAL_STATES = {"PROVEN", "REJECTED", "SUPERSEDED"}
RESUMABLE_STATES = {
    "EXPLORE",
    "PRESERVE",
    "CANDIDATE",
    "DECIDED",
    "SEQUENCED",
}
LEGAL_EDGES = {
    "EXPLORE": {"PRESERVE", "CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "PRESERVE": {"EXPLORE", "CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "CANDIDATE": {"PRESERVE", "DECIDED", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "DECIDED": {"CANDIDATE", "SEQUENCED", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "SEQUENCED": {"DECIDED", "ACTIVE", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "ACTIVE": {"SEQUENCED", "PROVEN", "REJECTED", "SUPERSEDED"},
    "PROVEN": {"SUPERSEDED"},
    "DEFERRED": set(RESUMABLE_STATES),
    "REJECTED": set(),
    "SUPERSEDED": set(),
}

EXPECTED_CURRENT_MAIN_ADRS = [
    "ADR-0001-PROVEN-INCREMENTS.md",
    "ADR-0002-SANDBOX-PROVIDER-ABSTRACTION.md",
    "ADR-0003-OFFLINE-EVIDENCE-MANIFEST.md",
    "ADR-0003-OWNED-SUBPROCESS-SUPERVISION.md",
    "ADR-0003-THREE_VALUED_GATE_OUTCOMES.md",
    "ADR-0004-SSSF-FIRSTMATE-WINDOWS-FRONT-DOOR.md",
    "ADR-0006-SANDBOX-PROVIDER-CONTRACT.md",
]
AUTHORITATIVE_PLANNING_REF = "planning/future-sssf"
AUTHORITATIVE_PLANNING_TRACKING_REF = "refs/remotes/origin/planning/future-sssf"
AUTHORITATIVE_PLANNING_PATHS = (
    "docs/development/FUTURE_CANDIDATES.md",
    "docs/development/ROADMAP.md",
    "docs/development/INCREMENT_PROTOCOL.md",
    "docs/development/BOUNDEDNESS_LAW.md",
    "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md",
)
PROJECTION_SCHEMA = "sssf.planning-authority-projection.v1"
EXPECTED_ITEM_STATES = {"FUT-001": "SEQUENCED", "FUT-002": "PRESERVE", "FUT-003": "ACTIVE"}
GOVERNED_FUTURE_IDS = tuple(f"FUT-{index:03d}" for index in range(1, 14))
GOVERNED_LIFECYCLE_IDENTITIES = (
    "LAUNCH-1",
    "SBX-0",
    "SBX-1",
    "SBX-2",
    "SBX-3",
    "SBX-4",
    "SBX-5",
    "SBX-6",
    "SBX-7",
    "SBX-8",
    "WAYFINDER-1",
    "DSH-0A",
    "DSH-0B",
    "DSH-1",
    "DSH-2",
    "DSH-3",
    "DSH-4",
    "DSH-5",
    "DSH-6",
    "DSH-7",
    "DSH-8",
)
EXPECTED_EXPLICIT_LIFECYCLE_STATES = {
    "LAUNCH-1": "ACTIVE",
    "SBX-0": "ACTIVE",
    "SBX-1": "SEQUENCED",
    "WAYFINDER-1": "SEQUENCED",
}
DOCKER_FIRST_ORDER = """Docker SBX-2..8
-> Docker-backed ordinary PR
-> immutable post-Docker/pre-DSH baseline
-> existing Wayfinder
-> DSH-0A
-> DSH-0B
-> DSH-1..."""
CLOSURE_REQUIRED_TESTS = (
    "tests/test_planning_foundation.py::test_closure_gate_requires_nonempty_exact_test_universe",
    "tests/test_planning_foundation.py::test_closure_gate_includes_unrelated_notimplementederror_regression",
    "tests/test_planning_foundation.py::test_older_consistent_snapshot_cannot_replace_authoritative_generation",
    "tests/test_planning_foundation.py::test_authority_projection_preserves_sbx2_state_and_rejects_missing_identity",
    "tests/test_planning_foundation.py::test_authority_projection_derives_bound1_predecessor_markers",
    "tests/test_planning_foundation.py::test_sbx2_state_is_observed_from_authority_not_candidate_expectation",
    "tests/test_planning_foundation.py::test_missing_governed_identity_or_bound1_predecessor_is_nonpass",
    "tests/test_planning_foundation.py::test_authority_projection_rejects_missing_duplicate_or_conflicting_governed_identities",
    "tests/test_planning_foundation.py::test_closure_gate_includes_authority_omission_and_predecessor_regressions",
    "tests/test_planning_foundation.py::test_windows_symlink_privilege_cno_is_machine_readable_non_pass",
    "tests/test_planning_foundation.py::test_unrelated_notimplementederror_is_not_automatic_cno",
)
CLOSURE_EXPECTED_OUTCOMES = {nodeid: "passed" for nodeid in CLOSURE_REQUIRED_TESTS}
AUTHORITY_CLOSURE_NODEIDS = (
    "tests/test_planning_foundation.py::test_sbx2_state_is_observed_from_authority_not_candidate_expectation",
    "tests/test_planning_foundation.py::test_missing_governed_identity_or_bound1_predecessor_is_nonpass",
    "tests/test_planning_foundation.py::test_authority_projection_rejects_missing_duplicate_or_conflicting_governed_identities",
    "tests/test_planning_foundation.py::test_closure_gate_includes_authority_omission_and_predecessor_regressions",
)
PLANNING_SURFACE_KEYS = (
    "candidates",
    "roadmap",
    "adr_planning",
    "adr_dsh",
    "readme",
    "increment",
)

FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BRANCH_FORBIDDEN = re.compile(r"[\x00-\x20\x7f~^:?*\[\\]")
GITHUB_PR_URL = re.compile(
    r"https://github\.com/"
    r"(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?)/"
    r"(?P<repository>[A-Za-z0-9._-]{1,100})/pull/[1-9][0-9]*"
)
URI_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
SCP_REMOTE_REFERENCE = re.compile(r"^(?:[^/\s:@]+@)?[^/\s:@]+:[^\s].*$")


class _DuplicateKey(ValueError):
    pass


def _git_output(root: Path, *arguments: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, UnicodeError, subprocess.CalledProcessError):
        return None
    value = result.stdout.strip()
    return value or None


def _authority_generation(commit: str, tree: str) -> str:
    return f"{AUTHORITATIVE_PLANNING_REF}@{commit}:{tree}"


def _authority_identity_line(observation: dict[str, Any]) -> str:
    return (
        f"authoritative planning source: {observation['ref']}; "
        f"commit: {observation['source_commit']}; "
        f"tree: {observation['source_tree']}; "
        f"generation: {observation['generation']}"
    )


def _observe_authoritative_planning_source(root: Path) -> tuple[dict[str, Any] | None, str | None]:
    """Observe the fetched authority ref rather than trusting candidate constants."""
    commit = _git_output(
        root,
        "rev-parse",
        "--verify",
        f"{AUTHORITATIVE_PLANNING_TRACKING_REF}^{{commit}}",
    )
    if commit is None:
        return None, f"authority tracking ref unavailable: {AUTHORITATIVE_PLANNING_TRACKING_REF}"
    tree = _git_output(root, "rev-parse", "--verify", f"{commit}^{{tree}}")
    if tree is None:
        return None, f"authority tree unavailable for observed commit: {commit}"
    blobs: dict[str, str] = {}
    for relative in AUTHORITATIVE_PLANNING_PATHS:
        blob = _git_output(root, "show", f"{commit}:{relative}")
        if blob is None:
            return None, f"authority source path unavailable at {commit}: {relative}"
        blobs[relative] = blob
    return _project_authoritative_planning_blobs(commit, tree, blobs)


def _project_authoritative_planning_blobs(
    commit: str, tree: str, blobs: dict[str, str]
) -> tuple[dict[str, Any] | None, str | None]:
    future_items, future_error = _parse_future_register(
        blobs[AUTHORITATIVE_PLANNING_PATHS[0]]
    )
    if future_error:
        return None, f"authority future-item register is invalid at {commit}: {future_error}"
    assert future_items is not None

    roadmap = blobs["docs/development/ROADMAP.md"]
    observed_heading_ids = _extract_lifecycle_heading_ids(roadmap)
    unexpected = sorted(set(observed_heading_ids) - set(GOVERNED_LIFECYCLE_IDENTITIES))
    if unexpected:
        return None, (
            f"authority roadmap contains unexpected lifecycle identities at {commit}: "
            + ", ".join(unexpected)
        )

    lifecycle_items: list[dict[str, str]] = []
    for identity in GOVERNED_LIFECYCLE_IDENTITIES:
        blocks = _identity_heading_blocks(roadmap, identity)
        if not blocks:
            return None, f"authority roadmap omits lifecycle identity at {commit}: {identity}"
        if len(blocks) != 1:
            return None, (
                f"authority roadmap has duplicate lifecycle identity at {commit}: "
                f"{identity} ({len(blocks)} headings)"
            )
        block = blocks[0]
        state_matches = _planning_state_declarations(block)
        if identity in EXPECTED_EXPLICIT_LIFECYCLE_STATES:
            expected_state = EXPECTED_EXPLICIT_LIFECYCLE_STATES[identity]
            if len(state_matches) != 1:
                return None, (
                    f"authority lifecycle state declaration is missing or duplicated at "
                    f"{commit}: {identity}"
                )
            state = state_matches[0].upper()
            if state != expected_state:
                return None, (
                    f"authority lifecycle state is unexpected at {commit}: "
                    f"{identity}={state}"
                )
        elif identity == "SBX-2":
            if state_matches:
                return None, (
                    f"authority SBX-2 has an unexpected explicit state declaration at {commit}"
                )
            sbx1_blocks = _identity_heading_blocks(roadmap, "SBX-1")
            if len(sbx1_blocks) != 1:
                return None, f"authority SBX-1 unlock boundary is unavailable at {commit}"
            unlock_matches = _sbx2_unlock_boundary_matches(sbx1_blocks[0])
            if len(unlock_matches) != 1:
                return None, f"authority SBX-2 unlock boundary is missing or duplicated at {commit}"
            state = "HELD"
        else:
            if state_matches:
                return None, (
                    f"authority roadmap has an unexpected state declaration at {commit}: "
                    f"{identity}"
                )
            state = "ROADMAP_SUBSTEP"
        lifecycle_items.append(
            {
                "identity": identity,
                "state": state,
                "source_path": "docs/development/ROADMAP.md",
            }
        )

    protocol_markers = (
        "boundedness_delta:",
        "New or changed growth surfaces must use the boundedness registry/owner mechanism",
        "For an added or changed dynamic bound, prove the effective limit",
    )
    if any(marker not in blobs["docs/development/INCREMENT_PROTOCOL.md"] for marker in protocol_markers):
        return None, f"authority increment protocol lacks boundedness marker at {commit}"
    law_markers = (
        "Every list, queue, log, retry chain",
        "EXPLICIT_BOUND",
        "SAFE_UNBOUNDED",
    )
    if any(marker not in blobs["docs/development/BOUNDEDNESS_LAW.md"] for marker in law_markers):
        return None, f"authority boundedness law lacks governing marker at {commit}"

    bound1_markers, bound1_error = _parse_bound1_authority_blob(
        blobs["docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"],
        roadmap,
    )
    if bound1_error:
        return None, f"authority BOUND-1 contract is invalid at {commit}: {bound1_error}"
    assert bound1_markers is not None
    if bound1_markers["state"] != "SEQUENCED":
        return None, (
            f"authority BOUND-1 state is unexpected at {commit}: "
            f"{bound1_markers['state']}"
        )
    lifecycle_items.append(
        {
            "identity": bound1_markers["predecessor"],
            "state": bound1_markers["state"],
            "source_path": "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md",
        }
    )
    return {
        "ref": AUTHORITATIVE_PLANNING_REF,
        "tracking_ref": AUTHORITATIVE_PLANNING_TRACKING_REF,
        "source_commit": commit,
        "source_tree": tree,
        "generation": _authority_generation(commit, tree),
        "future_items": future_items,
        "lifecycle_identities": lifecycle_items,
        "protocol_markers": list(protocol_markers),
        "law_markers": list(law_markers),
        "bound1_markers": bound1_markers,
        "source_blobs": dict(blobs),
    }, None


def _is_windows_symlink_capability_error(error: BaseException) -> bool:
    """Return true only for the ruled Windows missing-link privilege case."""
    return isinstance(error, OSError) and getattr(error, "winerror", None) == 1314


def _fold_property_outcome(failures: list[str], cno: list[str]) -> str:
    """Apply the property-local FAIL > CNO > PASS precedence."""
    if failures:
        return "observed-bad"
    if cno:
        return "could-not-observe"
    return "observed-good"


def _machine_result(
    status: str,
    *,
    errors: list[str] | tuple[str, ...] = (),
    cno: list[str] | tuple[str, ...] = (),
) -> dict[str, Any]:
    if status == "observed-good":
        outcome, result_status = "PASS", "OBSERVED_GOOD"
    elif status == "observed-bad":
        outcome, result_status = "FAIL", "OBSERVED_BAD"
    else:
        outcome, result_status = "CNO", "UNVERIFIED"
    return {
        "schema": "sssf.planning-foundation-result/v1",
        "outcome": outcome,
        "status": result_status,
        "errors": list(errors),
        "unverified_controls": list(cno),
    }


def _validator_exit_code(status: str) -> int:
    return {"observed-good": 0, "observed-bad": 1, "could-not-observe": 2}[status]


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(text, object_pairs_hook=_strict_pairs)
    except (json.JSONDecodeError, ValueError) as error:
        return None, str(error)
    if not isinstance(value, dict):
        return None, "top-level JSON value is not an object"
    return value, None


def evaluate_test_closure(
    collected_nodeids: list[str] | tuple[str, ...],
    executed_reports: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    *,
    required_nodeids: tuple[str, ...] = CLOSURE_REQUIRED_TESTS,
    collection_errors: list[str] | tuple[str, ...] = (),
    exit_status: int = 0,
) -> tuple[str, list[str]]:
    """Evaluate pytest collection/report events without trusting terminal prose."""
    errors: list[str] = []
    cno: list[str] = []
    collected = list(collected_nodeids)
    required = set(required_nodeids)
    if not required:
        cno.append("closure required test universe is empty")
    if not collected:
        cno.append("closure selected zero tests")
    if len(collected) != len(set(collected)):
        cno.append("closure collection contains duplicate test identities")
    if set(collected) != required:
        missing = sorted(required - set(collected))
        extra = sorted(set(collected) - required)
        if missing:
            cno.append("closure required test identity missing or renamed: " + ", ".join(missing))
        if extra:
            cno.append("closure selected test universe contains unexpected identities: " + ", ".join(extra))
    if collection_errors:
        cno.append("closure collection failed: " + "; ".join(collection_errors))
    reports: dict[str, list[str]] = {}
    for nodeid, outcome in executed_reports:
        reports.setdefault(nodeid, []).append(outcome)
    if set(reports) != set(collected):
        missing_reports = sorted(set(collected) - set(reports))
        if missing_reports:
            cno.append("closure required test did not complete: " + ", ".join(missing_reports))
        extra_reports = sorted(set(reports) - set(collected))
        if extra_reports:
            cno.append("closure reported an uncollected test identity: " + ", ".join(extra_reports))
    for nodeid in sorted(required):
        outcomes = reports.get(nodeid, [])
        expected = CLOSURE_EXPECTED_OUTCOMES.get(nodeid, "passed")
        if len(outcomes) != 1:
            if not outcomes:
                cno.append(f"closure required identity has no executed call result: {nodeid}")
            else:
                cno.append(f"closure required identity executed {len(outcomes)} times: {nodeid}")
            continue
        actual = outcomes[0]
        if actual != expected:
            if actual in {"failed", "error"}:
                errors.append(f"closure required test failed: {nodeid} ({actual})")
            else:
                cno.append(f"closure required test was not completed as {expected}: {nodeid} ({actual})")
    if exit_status not in (0,):
        cno.append(f"closure runner ended with nonzero status: {exit_status}")
    if errors:
        return "observed-bad", errors + cno
    if cno:
        return "could-not-observe", cno
    return "observed-good", []


class _PytestClosureRecorder:
    """Capture collection and call reports from pytest's executed event stream."""

    def __init__(self) -> None:
        self.collected_nodeids: list[str] = []
        self.executed_reports: list[tuple[str, str]] = []
        self.collection_errors: list[str] = []
        self.exit_status = 0

    def pytest_collection_finish(self, session: Any) -> None:
        self.collected_nodeids = [item.nodeid for item in session.items]

    def pytest_collectreport(self, report: Any) -> None:
        if getattr(report, "failed", False):
            self.collection_errors.append(str(getattr(report, "longrepr", report)))

    def pytest_runtest_logreport(self, report: Any) -> None:
        if getattr(report, "when", None) == "call":
            self.executed_reports.append((report.nodeid, report.outcome))

    def pytest_sessionfinish(self, session: Any, exitstatus: Any) -> None:
        self.exit_status = int(exitstatus)


def run_test_closure(
    required_nodeids: tuple[str, ...] = CLOSURE_REQUIRED_TESTS,
) -> tuple[str, list[str]]:
    """Run and evaluate the exact closure universe through pytest events."""
    try:
        import pytest
    except Exception as error:  # pragma: no cover - environment-specific
        return "could-not-observe", [f"pytest closure runner unavailable: {error}"]
    recorder = _PytestClosureRecorder()
    previous_bytecode_setting = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        pytest.main(["-q", "-p", "no:cacheprovider", *required_nodeids], plugins=[recorder])
    except BaseException as error:  # pragma: no cover - runner-specific
        return "could-not-observe", [f"pytest closure runner raised: {error}"]
    finally:
        sys.dont_write_bytecode = previous_bytecode_setting
    return evaluate_test_closure(
        recorder.collected_nodeids,
        recorder.executed_reports,
        required_nodeids=required_nodeids,
        collection_errors=recorder.collection_errors,
        exit_status=recorder.exit_status,
    )


def _watched_test_closure_controls() -> list[str]:
    """Keep every vacuity escape causally red while retaining positive controls."""
    required = ("tests/test_planning_foundation.py::required",)
    cases = (
        ("closure-zero-selection", (), (), (), 0, "could-not-observe"),
        ("closure-selector-typo", (), (), (), 0, "could-not-observe"),
        (
            "closure-nonexistent-identity",
            ("tests/test_planning_foundation.py::other",),
            (("tests/test_planning_foundation.py::other", "passed"),),
            (),
            0,
            "could-not-observe",
        ),
        (
            "closure-required-identity-removed",
            ("tests/test_planning_foundation.py::renamed",),
            (("tests/test_planning_foundation.py::renamed", "passed"),),
            (),
            0,
            "could-not-observe",
        ),
        (
            "closure-collection-failure",
            required,
            ((required[0], "passed"),),
            ("fixture import failed",),
            0,
            "could-not-observe",
        ),
        (
            "closure-required-pass",
            required,
            ((required[0], "passed"),),
            (),
            0,
            "observed-good",
        ),
        (
            "closure-required-fail",
            required,
            ((required[0], "failed"),),
            (),
            0,
            "observed-bad",
        ),
        (
            "closure-fail-over-collection-cno",
            required,
            ((required[0], "failed"),),
            ("fixture import failed",),
            0,
            "observed-bad",
        ),
    )
    failures: list[str] = []
    for name, collected, reports, collection_errors, exit_status, expected in cases:
        status, _ = evaluate_test_closure(
            collected,
            reports,
            required_nodeids=required,
            collection_errors=collection_errors,
            exit_status=exit_status,
        )
        if status != expected:
            failures.append(name)
    unrelated_nodeid = (
        "tests/test_planning_foundation.py::"
        "test_unrelated_notimplementederror_is_not_automatic_cno"
    )
    if unrelated_nodeid not in CLOSURE_REQUIRED_TESTS:
        failures.append("closure-unrelated-notimplemented-required")
    else:
        omitted = tuple(
            nodeid for nodeid in CLOSURE_REQUIRED_TESTS if nodeid != unrelated_nodeid
        )
        omitted_reports = tuple((nodeid, "passed") for nodeid in omitted)
        omitted_status, _ = evaluate_test_closure(omitted, omitted_reports)
        renamed = tuple(
            nodeid
            if nodeid != unrelated_nodeid
            else nodeid + "_renamed"
            for nodeid in CLOSURE_REQUIRED_TESTS
        )
        renamed_reports = tuple((nodeid, "passed") for nodeid in renamed)
        renamed_status, _ = evaluate_test_closure(renamed, renamed_reports)
        if omitted_status == "observed-good":
            failures.append("closure-unrelated-notimplemented-omitted")
        if renamed_status == "observed-good":
            failures.append("closure-unrelated-notimplemented-renamed")

    for authority_nodeid in AUTHORITY_CLOSURE_NODEIDS:
        if authority_nodeid not in CLOSURE_REQUIRED_TESTS:
            failures.append("closure-authority-regression-not-required:" + authority_nodeid)
            continue
        omitted = tuple(
            nodeid for nodeid in CLOSURE_REQUIRED_TESTS if nodeid != authority_nodeid
        )
        omitted_status, _ = evaluate_test_closure(
            omitted,
            tuple((nodeid, "passed") for nodeid in omitted),
        )
        renamed = tuple(
            nodeid
            if nodeid != authority_nodeid
            else nodeid + "_renamed"
            for nodeid in CLOSURE_REQUIRED_TESTS
        )
        renamed_status, _ = evaluate_test_closure(
            renamed,
            tuple((nodeid, "passed") for nodeid in renamed),
        )
        if omitted_status == "observed-good":
            failures.append("closure-authority-regression-omitted:" + authority_nodeid)
        if renamed_status == "observed-good":
            failures.append("closure-authority-regression-renamed:" + authority_nodeid)
    return failures


def _normal(text: str) -> str:
    # Markdown emphasis/code markers are presentation, not contract text.
    plain = text.lower().replace("`", "").replace("**", "")
    return " ".join(plain.split())


def _safe_sha(value: Any) -> bool:
    return isinstance(value, str) and bool(FULL_SHA.fullmatch(value))


def _valid_branch(value: Any) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    if (
        value.startswith(("-", "/"))
        or value.endswith(("/", "."))
        or "//" in value
        or ".." in value
        or "@{" in value
        or value == "@"
        or BRANCH_FORBIDDEN.search(value)
    ):
        return False
    return all(
        component
        and not component.startswith(".")
        and not component.endswith(".lock")
        for component in value.split("/")
    )


def _valid_pr_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    match = GITHUB_PR_URL.fullmatch(value)
    return bool(
        match
        and "--" not in match.group("owner")
        and match.group("repository") not in {".", ".."}
    )


def load_project(root: Path = ROOT) -> dict[str, Any]:
    """Read the project once; callers may copy this object for controls."""
    surfaces: dict[str, str] = {}
    unreadable: list[str] = []
    for key, relative in SURFACE_PATHS.items():
        try:
            surfaces[key] = (root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            surfaces[key] = ""
            unreadable.append(str(relative))

    adr_documents: dict[str, str] = {}
    decisions = root / "docs" / "decisions"
    try:
        paths = sorted(decisions.glob("ADR-*.md"))
    except OSError:
        paths = []
        unreadable.append("docs/decisions/")
    for path in paths:
        try:
            adr_documents[path.name] = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            unreadable.append(str(path.relative_to(root)))

    state: dict[str, Any] | None = None
    state_error: str | None = None
    if surfaces["state"]:
        state, state_error = _read_json(surfaces["state"])
    else:
        state_error = "planning state record is empty or unreadable"

    ci_manifest: dict[str, Any] | None = None
    ci_error: str | None = None
    if surfaces["ci_manifest"]:
        ci_manifest, ci_error = _read_json(surfaces["ci_manifest"])
    else:
        ci_error = "CI manifest is empty or unreadable"

    authority_observation, authority_observation_error = _observe_authoritative_planning_source(root)
    return {
        "root": root,
        "surfaces": surfaces,
        "adr_documents": adr_documents,
        "state": state,
        "state_error": state_error,
        "ci_manifest": ci_manifest,
        "ci_error": ci_error,
        "authority_observation": authority_observation,
        "authority_observation_error": authority_observation_error,
        "unreadable": unreadable,
    }


def _surface_paths(project: dict[str, Any]) -> set[str]:
    paths = {str(path) for path in SURFACE_PATHS.values()}
    paths.update(f"docs/decisions/{name}" for name in project.get("adr_documents", {}))
    return paths


def _path_exists(project: dict[str, Any], reference: Any) -> bool:
    if not isinstance(reference, str) or not reference:
        return False
    path = reference.split("#", 1)[0]
    if not path or path.startswith(("http://", "https://", "mailto:")):
        return True
    return path in _surface_paths(project) or (project["root"] / path).is_file()


def _is_remote_reference(value: str) -> bool:
    """Classify URL/URI and remote-reference syntax before Path sees it."""
    return bool(
        URI_SCHEME.match(value)
        or value.startswith(("//", "\\\\"))
        or SCP_REMOTE_REFERENCE.fullmatch(value)
    )


def _repository_path_exists(project: dict[str, Any], reference: Any) -> bool:
    if not isinstance(reference, str) or not reference or reference != reference.strip():
        return False
    # Do this before splitting fragments or constructing a filesystem path.  A
    # local directory named ``https:`` must not turn a remote identity into
    # repository evidence by accident.
    if _is_remote_reference(reference):
        return False
    path_text = reference.split("#", 1)[0]
    if not path_text or _is_remote_reference(path_text):
        return False
    path = Path(path_text)
    if (
        path.is_absolute()
        or PureWindowsPath(path_text).is_absolute()
        or ".." in path.parts
    ):
        return False
    try:
        root = project["root"].resolve(strict=True)
        candidate = (root / path).resolve(strict=True)
        if not _resolved_path_within_root(root, candidate):
            return False
    except (OSError, RuntimeError, ValueError):
        return False
    return candidate.is_file()


def _resolved_path_within_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _check_required_files(project: dict[str, Any], errors: list[str], cno: list[str]) -> None:
    for key, relative in SURFACE_PATHS.items():
        if not project["surfaces"].get(key):
            cno.append(f"required planning surface could-not-observe: {relative}")
    for path in project.get("unreadable", []):
        cno.append(f"ADR identity surface could-not-observe: {path}")
    if project.get("state_error"):
        cno.append(f"planning state could-not-observe: {project['state_error']}")
    if project.get("ci_error"):
        cno.append(f"CI manifest could-not-observe: {project['ci_error']}")
    if project.get("authority_observation_error"):
        cno.append(
            "current planning authority could-not-observe: "
            + str(project["authority_observation_error"])
        )


def _validate_projection(
    project: dict[str, Any], observation: dict[str, Any], errors: list[str]
) -> None:
    state = project.get("state")
    projection = state.get("projection_scope") if isinstance(state, dict) else None
    expected_basis = {
        "ref": observation["ref"],
        "tracking_ref": observation["tracking_ref"],
        "source_commit": observation["source_commit"],
        "source_tree": observation["source_tree"],
        "generation": observation["generation"],
    }
    if not isinstance(projection, dict) or projection.get("schema") != PROJECTION_SCHEMA:
        errors.append("planning authority projection schema is missing or unsupported")
        return
    if projection.get("state_basis") != expected_basis:
        errors.append("planning authority projection is stale or not bound to observed authority")
    if projection.get("future_items") != observation["future_items"]:
        errors.append("planning authority projection omits, adds, or demotes a current FUT item")
    expected_lifecycle = observation["lifecycle_identities"]
    if projection.get("lifecycle_identities") != expected_lifecycle:
        errors.append(
            "planning authority projection omits or demotes a LAUNCH/SBX/Wayfinder/DSH identity"
        )
    observed_lifecycle = {
        item.get("identity"): item
        for item in observation.get("lifecycle_identities", [])
        if isinstance(item, dict)
    }
    observed_sbx2 = observed_lifecycle.get("SBX-2")
    bound1 = observation.get("bound1_markers")
    if (
        not isinstance(observed_sbx2, dict)
        or not isinstance(bound1, dict)
        or bound1.get("predecessor") != "BOUND-1"
        or bound1.get("before") != "SBX-2"
        or not isinstance(bound1.get("required_phrase"), str)
        or not bound1["required_phrase"]
    ):
        errors.append("current authority BOUND-1 predecessor observation is incomplete")
    else:
        source_phrase = str(bound1["required_phrase"]).replace("`", "")
        expected_rule = (
            f"{bound1['predecessor']} must {source_phrase}; "
            f"{bound1['before']} can leave {observed_sbx2.get('state')} only after that qualification."
        )
        expected_predecessors = [
            {
                "predecessor": bound1["predecessor"],
                "predecessor_state": bound1.get("state"),
                "successor": bound1["before"],
                "successor_state": observed_sbx2.get("state"),
                "rule": expected_rule,
                "authority_rule": bound1["required_phrase"],
            }
        ]
        if projection.get("mandatory_predecessors") != expected_predecessors:
            errors.append("BOUND-1 predecessor rule is missing or demoted")
    protocol = project["surfaces"].get("increment_protocol", "")
    law = project["surfaces"].get("boundedness_law", "")
    if any(marker not in protocol for marker in observation.get("protocol_markers", [])):
        errors.append("increment protocol omits current boundedness-delta requirements")
    if any(marker not in law for marker in observation.get("law_markers", [])):
        errors.append("boundedness law projection is missing current governing contract")
    answerable = projection.get("answerable_queries")
    if answerable != ["future-item-state", "named-lifecycle-state", "boundedness-predecessor-order"]:
        errors.append("planning authority projection answerable scope drifted")
    not_answerable = projection.get("not_answerable_queries")
    required_not_answerable = {
        "SBX-2 readiness",
        "SBX-2 activation or promotion",
        "implementation, landing, acceptance, certification, or live enablement",
    }
    if not isinstance(not_answerable, list) or not required_not_answerable.issubset(not_answerable):
        errors.append("planning authority projection can answer an out-of-scope readiness query")
    if projection.get("scope_rule") != (
        "Only answerable_queries may be answered; every other query is CNO/non-PASS. "
        "This projection never answers SBX-2 readiness."
    ):
        errors.append("planning authority projection scope rule is missing or unsafe")


def _validate_authoritative_planning_source(
    project: dict[str, Any], errors: list[str]
) -> None:
    state = project.get("state")
    observation = project.get("authority_observation")
    if not isinstance(observation, dict):
        errors.append("current planning authority observation is missing")
        return
    expected_source = {
        "ref": observation["ref"],
        "tracking_ref": observation["tracking_ref"],
        "source_commit": observation["source_commit"],
        "source_tree": observation["source_tree"],
        "generation": observation["generation"],
        "identity_rule": (
            "The ref, tracking ref, observed source commit, observed source tree, "
            "and generation must match the current authority before planning state is accepted."
        ),
    }
    if not isinstance(state, dict) or state.get("authoritative_planning_source") != expected_source:
        errors.append(
            "authoritative planning source identity/generation is stale, missing, or mismatched"
        )
    observed_sbx2 = next(
        (
            item
            for item in observation.get("lifecycle_identities", [])
            if isinstance(item, dict) and item.get("identity") == "SBX-2"
        ),
        None,
    )
    observed_sandbox_states = (
        {"SBX-2": observed_sbx2.get("state")}
        if isinstance(observed_sbx2, dict)
        else None
    )
    if not isinstance(state, dict) or state.get("current_sandbox_states") != observed_sandbox_states:
        errors.append("candidate SBX-2 state is not bound to the observed authority state")
    for key in ("lifecycle",) + PLANNING_SURFACE_KEYS:
        text = project["surfaces"].get(key, "")
        if _authority_identity_line(observation) not in text:
            errors.append(
                f"{SURFACE_PATHS[key]} is not bound to observed authoritative planning generation"
            )
    manifest = project["surfaces"].get("manifest", "")
    for fragment in (
        f"authoritative_ref: {observation['ref']}",
        f"authoritative_tracking_ref: {observation['tracking_ref']}",
        f"authoritative_commit: {observation['source_commit']}",
        f"authoritative_tree: {observation['source_tree']}",
        f"authoritative_generation: {observation['generation']}",
    ):
        if fragment not in manifest:
            errors.append(f"planning manifest is missing authority identity: {fragment}")
    candidates = project["surfaces"].get("candidates", "")
    if _extract_register_state(candidates, "FUT-001") != "SEQUENCED":
        errors.append("authoritative FUT-001/DSH state drifted from SEQUENCED")
    if _extract_register_state(candidates, "FUT-003") != "ACTIVE":
        errors.append("authoritative FUT-003 state drifted from ACTIVE")
    candidate_items, candidate_register_error = _parse_future_register(candidates)
    if candidate_register_error:
        errors.append(
            "candidate register is malformed or incomplete: " + candidate_register_error
        )
    elif candidate_items != observation["future_items"]:
        errors.append("candidate register is not a complete current-authority FUT projection")
    if "**Planning state: `ACTIVE`, not `PROVEN`.**" not in project["surfaces"].get("roadmap", ""):
        errors.append("roadmap does not preserve FUT-003 ACTIVE-but-not-PROVEN authority")
    if "SBX-2 is held." not in project["surfaces"].get("roadmap", ""):
        errors.append("roadmap does not preserve SBX-2 HELD authority")
    if "BOUND-1" not in project["surfaces"].get("roadmap", ""):
        errors.append("roadmap omits mandatory BOUND-1 predecessor")
    if _normal(DOCKER_FIRST_ORDER) not in _normal(project["surfaces"].get("roadmap", "")):
        errors.append("roadmap Docker-first commissioning order drifted")
    _validate_projection(project, observation, errors)


def _validate_planning_authority_binding(
    record: dict[str, Any], project: dict[str, Any], errors: list[str]
) -> None:
    binding = record.get("planning_authority_binding")
    expected_increment_ids = ["FP-001", "FM-FP-001"]
    observation = project.get("authority_observation")
    expected = {
        "ref": observation.get("ref") if isinstance(observation, dict) else None,
        "source_commit": observation.get("source_commit") if isinstance(observation, dict) else None,
        "source_tree": observation.get("source_tree") if isinstance(observation, dict) else None,
        "generation": observation.get("generation") if isinstance(observation, dict) else None,
        "increment_ids": expected_increment_ids,
    }
    if not isinstance(binding, dict):
        errors.append(f"{record.get('item_id')} ACTIVE state lacks authoritative planning binding")
        return
    for field, value in expected.items():
        if binding.get(field) != value:
            errors.append(
                f"{record.get('item_id')} ACTIVE planning binding has stale {field}"
            )
    planned = record.get("planned_increments")
    expected_planned = [
        {"increment_id": increment_id, "status": "active-not-proven"}
        for increment_id in expected_increment_ids
    ]
    planned_matches = isinstance(planned, list) and planned == expected_planned
    binding_matches_planned = planned_matches and binding.get("increment_ids") == [
        item["increment_id"] for item in planned
    ]
    if not binding_matches_planned:
        errors.append(
            f"{record.get('item_id')} ACTIVE planning binding must exactly match "
            "unique active-not-proven planned increments"
        )
    refs = binding.get("authoritative_refs")
    if not isinstance(refs, list) or not refs or any(
        not _repository_path_exists(project, reference) for reference in refs
    ):
        errors.append(f"{record.get('item_id')} ACTIVE planning binding lacks retained authoritative refs")


def _validate_lifecycle(project: dict[str, Any], errors: list[str]) -> None:
    text = project["surfaces"]["lifecycle"]
    normalized = _normal(text)
    if LIFECYCLE_MARKER not in normalized:
        errors.append("lifecycle contract owner marker is missing")
    required = (
        "every state is one of",
        "legal transition",
        "side exit",
        "terminal state",
        "re-entry",
        "proven means",
        "active is intake eligibility only",
        "active is never task creation",
        "active is never execution authority",
        "active is never landing authority",
        "active is never pre_certification exit",
        "active is never acceptance",
        "active is never certification",
        "active is never live enablement",
        "active is never proven",
    )
    for fragment in required:
        if fragment not in normalized:
            errors.append(f"lifecycle contract is missing rule: {fragment}")
    for state in STATES:
        if f"`{state.lower()}`" not in normalized and state.lower() not in normalized:
            errors.append(f"lifecycle contract is missing state: {state}")
    for source, targets in LEGAL_EDGES.items():
        for target in sorted(targets):
            edge = f"{source} -> {target}"
            if edge.lower() not in normalized:
                errors.append(f"lifecycle contract is missing legal edge: {edge}")


def _validate_single_transition(
    transition: Any,
    *,
    previous: str,
    record: dict[str, Any],
    project: dict[str, Any],
    index: int,
    errors: list[str],
    deferred_return: str | None,
) -> tuple[str, str | None]:
    if not isinstance(transition, dict):
        errors.append(f"{record.get('item_id')} transition {index} is not an object")
        return previous, deferred_return
    source = transition.get("from")
    target = transition.get("to")
    if source not in STATES or target not in STATES:
        errors.append(
            f"illegal/unknown/skipped transition for {record.get('item_id')}: "
            f"{source!r} -> {target!r}"
        )
        return (target if target in STATES else previous), deferred_return
    if source != previous:
        errors.append(
            f"illegal/unknown/skipped transition for {record.get('item_id')}: "
            f"history expected from {previous}, recorded {source}"
        )
    elif target not in LEGAL_EDGES[source]:
        errors.append(
            f"illegal/unknown/skipped transition for {record.get('item_id')}: "
            f"{source} -> {target}"
        )
    if not isinstance(transition.get("evidence_refs"), list) or not transition["evidence_refs"]:
        errors.append(f"{record.get('item_id')} transition {index} has no durable evidence refs")
    else:
        for reference in transition["evidence_refs"]:
            if not _repository_path_exists(project, reference):
                errors.append(
                    f"broken planning cross-reference in {record.get('item_id')} transition: {reference}"
                )
    source_commit = transition.get("source_commit")
    if source_commit is not None and not _safe_sha(source_commit):
        errors.append(f"{record.get('item_id')} transition {index} has an invalid source commit identity")
    if target == "DEFERRED":
        return_to = transition.get("return_to")
        if source not in RESUMABLE_STATES or return_to != source:
            errors.append(
                f"{record.get('item_id')} deferred entry does not retain its return state"
            )
        else:
            deferred_return = return_to
    if source == "DEFERRED":
        if target not in RESUMABLE_STATES or deferred_return != target:
            errors.append(
                f"{record.get('item_id')} deferred re-entry does not return to its recorded state"
            )
        deferred_return = None
    if target == "ACTIVE":
        if (
            record.get("active_binding") is None
            and record.get("planning_authority_binding") is not None
        ):
            _validate_planning_authority_binding(record, project, errors)
        else:
            _validate_active_binding(record, project, errors)
    if target == "PROVEN":
        _validate_proven_proof(record, project, errors)
    return target, deferred_return


def _validate_proven_proof(
    record: dict[str, Any], project: dict[str, Any], errors: list[str]
) -> None:
    proof = record.get("proven_proof")
    item_id = record.get("item_id")
    if not isinstance(proof, dict):
        errors.append(f"{item_id} PROVEN transition lacks the complete proof contract")
        return
    if proof.get("accepted_implementation") is not True:
        errors.append(f"{item_id} PROVEN transition lacks accepted implementation")
    for field in (
        "acceptance_evidence_refs",
        "implementation_evidence_refs",
        "proof_evidence_refs",
        "documentation_evidence_refs",
    ):
        references = proof.get(field)
        if not isinstance(references, list) or not references or any(
            not _repository_path_exists(project, reference) for reference in references
        ):
            errors.append(f"{item_id} PROVEN transition lacks retained {field}")
    for field in ("source_commit", "source_tree"):
        if not _safe_sha(proof.get(field)):
            errors.append(f"{item_id} PROVEN transition lacks immutable {field}")


def _validate_active_binding(
    record: dict[str, Any], project: dict[str, Any], errors: list[str]
) -> None:
    binding = record.get("active_binding")
    increments = binding.get("increments") if isinstance(binding, dict) else None
    if not isinstance(increments, list) or not increments:
        errors.append(f"unbound or partial ACTIVE identity for {record.get('item_id')}: increments")
        return
    planned = record.get("planned_increments")
    planned_ids = (
        [item.get("increment_id") for item in planned]
        if isinstance(planned, list) and all(isinstance(item, dict) for item in planned)
        else []
    )
    bound_ids = [item.get("increment_id") for item in increments if isinstance(item, dict)]
    if (
        not planned_ids
        or len(planned_ids) != len(set(planned_ids))
        or len(bound_ids) != len(increments)
        or len(bound_ids) != len(set(bound_ids))
        or set(bound_ids) != set(planned_ids)
    ):
        errors.append(
            f"unbound or partial ACTIVE identity for {record.get('item_id')}: "
            "bindings must exactly cover unique planned increments"
        )
    required = (
        "increment_id",
        "branch",
        "pr_url",
        "source_commit",
        "source_tree",
        "authoritative_refs",
    )
    for index, increment in enumerate(increments):
        if not isinstance(increment, dict):
            errors.append(f"unbound or partial ACTIVE identity for {record.get('item_id')}: increment {index}")
            continue
        for field in required:
            value = increment.get(field)
            if field in {"source_commit", "source_tree"}:
                valid = _safe_sha(value)
            elif field == "branch":
                valid = _valid_branch(value)
            elif field == "pr_url":
                valid = _valid_pr_url(value)
            elif field == "authoritative_refs":
                valid = isinstance(value, list) and bool(value) and all(isinstance(item, str) and item for item in value)
            else:
                valid = isinstance(value, str) and bool(value)
            if not valid:
                errors.append(
                    f"unbound or partial ACTIVE identity for {record.get('item_id')}: "
                    f"increment {index} field {field}"
                )
        for reference in increment.get("authoritative_refs", []) if isinstance(increment.get("authoritative_refs"), list) else []:
            if not _repository_path_exists(project, reference):
                errors.append(
                    f"unbound or partial ACTIVE identity for {record.get('item_id')}: "
                    f"authoritative reference {reference}"
                )


def _validate_state(
    project: dict[str, Any], errors: list[str], *, enforce_canonical_states: bool = True
) -> None:
    state = project.get("state")
    if not isinstance(state, dict):
        return
    expected_keys = {
        "schema_version",
        "record_id",
        "lifecycle_owner",
        "state_record_rule",
        "current_main_adr_inventory",
        "allocated_new_identities",
        "authoritative_planning_source",
        "current_sandbox_states",
        "projection_scope",
        "records",
    }
    unknown = set(state) - expected_keys
    missing = expected_keys - set(state)
    if missing:
        errors.append("planning state record missing keys: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("planning state record has unknown keys: " + ", ".join(sorted(unknown)))
    if state.get("schema_version") != "sssf.planning-state.v1":
        errors.append("planning state record schema is stale or unsupported")
    if state.get("record_id") != "sssf-planning-state":
        errors.append("planning state record identity is wrong")
    if state.get("lifecycle_owner") != LIFECYCLE_OWNER:
        errors.append("planning state record points at a competing lifecycle owner")
    if state.get("state_record_rule") != "This JSON record is the durable current-state record; Git commit prose is not state.":
        errors.append("planning state record does not disavow commit-message state")
    inventory = state.get("current_main_adr_inventory")
    if not isinstance(inventory, dict):
        errors.append("current-main ADR identity inventory is missing")
    else:
        if inventory.get("source_commit") != "991d3a64f1b96a8b9637f97060d692af3518228f":
            errors.append("current-main ADR identity inventory is not pinned to supplied main")
        if inventory.get("files") != EXPECTED_CURRENT_MAIN_ADRS:
            errors.append("current-main ADR identity inventory drifted")
    allocated = state.get("allocated_new_identities")
    if allocated != {
        "fut003": "ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md",
        "dsh": "ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md",
    }:
        errors.append("new ADR identity allocation is missing or not unique")

    records = state.get("records")
    if not isinstance(records, list):
        errors.append("planning state records are not a list")
        return
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            errors.append("planning state record entry is not an object")
            continue
        item_id = record.get("item_id")
        if item_id in by_id:
            errors.append(f"duplicate durable planning state record: {item_id}")
        by_id[item_id] = record
    if enforce_canonical_states and set(by_id) != set(EXPECTED_ITEM_STATES):
        errors.append("missing durable planning state record for one or more registered items")
    expected_items = EXPECTED_ITEM_STATES if enforce_canonical_states else {item_id: record.get("state") for item_id, record in by_id.items()}
    for item_id, expected_state in expected_items.items():
        record = by_id.get(item_id)
        if record is None:
            continue
        current = record.get("state")
        if enforce_canonical_states and current != expected_state:
            errors.append(f"canonical state drift for {item_id}: expected {expected_state}, got {current!r}")
        if current not in STATES:
            errors.append(f"unknown planning state for {item_id}: {current!r}")
            continue
        initial = record.get("initial_state")
        transitions = record.get("transition_history")
        if initial not in STATES or not isinstance(transitions, list) or not transitions:
            errors.append(f"{item_id} has no complete durable transition history")
            continue
        previous = initial
        deferred_return: str | None = None
        for index, transition in enumerate(transitions):
            previous, deferred_return = _validate_single_transition(
                transition,
                previous=previous,
                record=record,
                project=project,
                index=index,
                errors=errors,
                deferred_return=deferred_return,
            )
        if previous != current:
            errors.append(f"{item_id} durable transition history does not end at current state {current}")
        has_proven_transition = any(
            isinstance(transition, dict) and transition.get("to") == "PROVEN"
            for transition in transitions
        )
        if record.get("proven_proof") is not None and (
            current not in {"PROVEN", "SUPERSEDED"} or not has_proven_transition
        ):
            errors.append(
                f"{item_id} has a PROVEN proof claim without legal PROVEN history"
            )
        binding = record.get("active_binding")
        entered_active = any(
            isinstance(transition, dict) and transition.get("to") == "ACTIVE"
            for transition in transitions
        )
        if binding is not None and not entered_active:
            errors.append(f"{item_id} has an ACTIVE binding without an ACTIVE transition")
        if current == "ACTIVE" or entered_active:
            if (
                record.get("active_binding") is None
                and record.get("planning_authority_binding") is not None
            ):
                _validate_planning_authority_binding(record, project, errors)
            else:
                _validate_active_binding(record, project, errors)
        if current in TERMINAL_STATES and record.get("reentry_rule") not in ("terminal", None):
            errors.append(f"{item_id} terminal state has a re-entry rule")
        if current == "DEFERRED" and record.get("return_state") != deferred_return:
            errors.append(f"{item_id} deferred state does not retain its recorded return state")
        if current != "DEFERRED" and record.get("return_state") is not None:
            errors.append(f"{item_id} has a deferred return state while its canonical state is {current}")
    for record in records:
        if isinstance(record, dict):
            for reference in record.get("authoritative_refs", []):
                if not _path_exists(project, reference):
                    errors.append(f"broken planning cross-reference: {reference}")


def _parse_register_rows(text: str) -> tuple[list[dict[str, str]], str | None]:
    rows: list[dict[str, str]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.lstrip().startswith("|") or not re.search(r"\bFUT-[0-9]{3}\b", line):
            continue
        columns = [column.strip() for column in line.strip().split("|")]
        if len(columns) < 4 or not re.fullmatch(r"FUT-[0-9]{3}", columns[1]):
            return [], f"malformed FUT register row at line {line_number}"
        if not columns[2] or not columns[3]:
            return [], f"malformed FUT register row at line {line_number}"
        rows.append({"item_id": columns[1], "state": columns[3]})
    if not rows:
        return [], "register has no FUT rows"
    return rows, None


def _parse_future_register(text: str) -> tuple[list[dict[str, str]] | None, str | None]:
    rows, row_error = _parse_register_rows(text)
    if row_error:
        return None, row_error
    ids = [row["item_id"] for row in rows]
    unknown = sorted(set(ids) - set(GOVERNED_FUTURE_IDS))
    if unknown:
        return None, "unexpected FUT identities: " + ", ".join(unknown)
    duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicates:
        return None, "duplicate FUT identities: " + ", ".join(duplicates)
    missing = [item_id for item_id in GOVERNED_FUTURE_IDS if item_id not in ids]
    if missing:
        return None, "missing FUT identities: " + ", ".join(missing)
    invalid_states = sorted(
        f"{row['item_id']}={row['state']}"
        for row in rows
        if row["state"] not in STATES
    )
    if invalid_states:
        return None, "malformed FUT states: " + ", ".join(invalid_states)
    return rows, None


def _extract_register_items(text: str) -> list[dict[str, str]]:
    rows, _ = _parse_register_rows(text)
    return rows


def _extract_register_state(text: str, item_id: str) -> str | None:
    match = re.search(rf"\|\s*{re.escape(item_id)}\s*\|[^|]+\|\s*([^|]+?)\s*\|", text)
    return match.group(1).strip() if match else None


def _extract_lifecycle_heading_ids(text: str) -> list[str]:
    pattern = re.compile(
        r"(?m)^#{2,3}\s+(?P<identity>"
        r"(?:LAUNCH-[0-9]+|SBX-[0-9]+|WAYFINDER-[0-9]+|DSH-(?:0A|0B|[0-9]+))"
        r")\b"
    )
    return [match.group("identity") for match in pattern.finditer(text)]


def _identity_heading_blocks(text: str, identity: str) -> list[str]:
    pattern = re.compile(
        rf"(?ms)^#{{2,3}}\s+{re.escape(identity)}(?=\s|$).*?(?=^#{{2,3}}\s+|\Z)"
    )
    return [match.group(0) for match in pattern.finditer(text)]


def _identity_heading_block(text: str, identity: str) -> str:
    blocks = _identity_heading_blocks(text, identity)
    return blocks[0] if blocks else ""


def _planning_state_declarations(text: str) -> list[str]:
    return [
        match.group(1).strip()
        for match in re.finditer(
            r"(?i)planning\s+state\s*:\s*\**\s*`([^`]+)`", text
        )
    ]


def _sbx2_unlock_boundary_matches(text: str) -> list[str]:
    return [
        " ".join(match.group(0).split())
        for match in re.finditer(
            r"(?i)\bdo(?:es)?\s+not(?:\s+by\s+itself)?\s+establish\b"
            r"[^\n.]*\bSBX-2\s+unlock\b",
            text,
        )
    ]


def _parse_bound1_authority_blob(
    text: str, roadmap: str
) -> tuple[dict[str, str | None] | None, str | None]:
    titles = re.findall(r"(?m)^#\s+(BOUND-1)\b", text)
    if len(titles) != 1:
        return None, "BOUND-1 heading is missing or duplicated"
    states = _planning_state_declarations(text)
    if len(states) != 1:
        return None, "BOUND-1 state declaration is missing or duplicated"
    state = states[0].upper()
    if state not in STATES:
        return None, f"BOUND-1 state is malformed: {state}"
    relations = [
        " ".join(match.group(1).split())
        for match in re.finditer(
            r"(?i)\b(complete\s+and\s+qualify\s+before\s+`?"
            r"(SBX-2)`?\s+activation)\b",
            text,
        )
    ]
    if len(relations) != 1:
        return None, "BOUND-1 predecessor relationship is missing or duplicated"
    leave_held = re.findall(
        r"(?i)complete\s+and\s+qualify\s+before\s+`SBX-2`\s+can\s+leave\s+`HELD`",
        roadmap,
    )
    if len(leave_held) > 1:
        return None, "BOUND-1 leave-HELD relationship is duplicated"
    return {
        "predecessor": titles[0],
        "state": state,
        "before": "SBX-2",
        "required_phrase": relations[0],
        "leave_held_phrase": leave_held[0] if leave_held else None,
    }, None


def _heading_block(text: str, heading: str) -> str:
    match = re.search(
        rf"(?ms)^##\s+{re.escape(heading)}\s*$.*?(?=^##\s+|\Z)",
        text,
    )
    return match.group(0) if match else ""


def _validate_document_states(project: dict[str, Any], errors: list[str]) -> None:
    candidates = project["surfaces"]["candidates"]
    roadmap = project["surfaces"]["roadmap"]
    if _extract_register_state(candidates, "FUT-001") != "SEQUENCED":
        errors.append("FUT-001/DSH is not durably SEQUENCED and inactive")
    if _extract_register_state(candidates, "FUT-002") != "PRESERVE":
        errors.append("FUT-002 preserve state drifted")
    if _extract_register_state(candidates, "FUT-003") != "ACTIVE":
        errors.append("FUT-003 candidate register is not ACTIVE")
    fut001 = _heading_block(candidates, "FUT-001 — Bounded autonomous DSH execution cells")
    fut003 = _heading_block(candidates, "FUT-003 — FirstMate planning-transition awareness")
    for label, block, fragments in (
        (
            "FUT-001",
            fut001,
            ("`SEQUENCED`", "not active", "SSSF retains outer authority"),
        ),
        (
            "FUT-003",
            fut003,
            (
                "`ACTIVE`",
                "not `PROVEN`",
                "FP-001",
                "FM-FP-001",
                "authoritative planning generation",
            ),
        ),
    ):
        normalized = _normal(block)
        for fragment in fragments:
            if _normal(fragment) not in normalized:
                errors.append(f"{label} state record prose is missing boundary: {fragment}")
    if "## FUT-003 — FirstMate planning-transition awareness" not in roadmap:
        errors.append("roadmap is missing the FUT-003 planning section")
    else:
        roadmap_block = roadmap.split("## FUT-003 — FirstMate planning-transition awareness", 1)[1]
        roadmap_block = roadmap_block.split("\n## ", 1)[0]
        normalized = _normal(roadmap_block)
        for fragment in (
            "planning state: `ACTIVE`, not `PROVEN`",
            "no FirstMate watcher, producer, or consumer implementation",
            "authoritative planning generation",
        ):
            if _normal(fragment) not in normalized:
                errors.append(f"roadmap FUT-003 boundary is missing: {fragment}")
    adr = _normal(project["surfaces"]["adr_planning"])
    forbidden_stale = (
        "implementation unsequenced and inactive",
        "implementation is unsequenced and inactive",
        "this decision is not sequenced",
        "must not sequence implementation",
    )
    for fragment in forbidden_stale:
        if fragment in adr:
            errors.append(f"ADR-0005 has stale contradictory status language: {fragment}")
    for fragment in (
        "implementation active",
        "authoritative planning source",
        "normal FirstMate admission",
        "exact referenced source identity",
        "not proven",
        "does not create execution authority",
    ):
        if _normal(fragment) not in adr:
            errors.append(f"ADR-0005 is missing required boundary: {fragment}")


def _validate_router_and_authority(project: dict[str, Any], errors: list[str]) -> None:
    readme = _normal(project["surfaces"]["readme"])
    required = (
        "active is engineering authorization only",
        "active is intake eligibility only",
        "active is never task creation",
        "active is never execution authority",
        "active is never landing authority",
        "active is never pre_certification exit",
        "active is never acceptance",
        "active is never certification",
        "active is never live enablement",
        "active is never proven",
        "proven is proof state",
        "no planning record is runtime authority",
    )
    for fragment in required:
        if fragment not in readme:
            errors.append(f"planning router is missing authority clarification: {fragment}")
    dangerous = (
        "active is runtime authority",
        "active is landing authority",
        "active exits pre_certification",
        "active is accepted",
        "active is certified",
        "active is live-enabled",
        "active is proven",
    )
    for fragment in dangerous:
        if fragment in readme:
            errors.append(f"ACTIVE/proven/runtime boundary is unsafe: {fragment}")


def _validate_adr_identities(project: dict[str, Any], errors: list[str]) -> None:
    documents = project.get("adr_documents", {})
    identity_to_files: dict[str, list[str]] = {}
    for name, text in documents.items():
        filename_match = re.match(r"ADR-(\d{4})-", name)
        title_match = re.search(r"^#\s+ADR-(\d{4})\b", text, re.MULTILINE)
        if not filename_match or not title_match:
            errors.append(f"ADR identity could-not-be-observed or malformed: {name}")
            continue
        filename_identity = filename_match.group(1)
        title_identity = title_match.group(1)
        if filename_identity != title_identity:
            errors.append(f"ADR filename/title identity mismatch: {name}")
        identity_to_files.setdefault(filename_identity, []).append(name)
    # Existing 0003 historical filename collision is explicitly out of scope;
    # the newly allocated identity must nevertheless be singular.
    if identity_to_files.get("0007") != [
        "ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md"
    ]:
        errors.append("duplicate or missing ADR-0007 identity")
    if "ADR-0004-SSSF-FIRSTMATE-WINDOWS-FRONT-DOOR.md" not in documents:
        errors.append("current-main ADR-0004 Windows front-door identity was not preserved")
    if "ADR-0006-SANDBOX-PROVIDER-CONTRACT.md" not in documents:
        errors.append("current-main ADR-0006 SandboxProvider identity was not preserved")
    if "ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md" in documents:
        errors.append("DSH ADR retained the stale ADR-0004 identity")
    if project["surfaces"]["adr_dsh"].find("# ADR-0007") != 0:
        errors.append("DSH ADR-0007 title is missing")


def _validate_roadmap_sbx_hold(project: dict[str, Any], errors: list[str]) -> None:
    text = _normal(project["surfaces"]["roadmap"])
    required = (
        "sbx-0's sole durable provider-neutral handoff landed",
        "sbx-1 is a **landed implementation**",
        "sbx-1 is not activated",
        "sbx-1 is not accepted",
        "sbx-1 is not certified",
        "sbx-1 is not real-provider-proven",
        "does not unlock sbx-2",
        "sbx-2 is held",
        "planning state: `held`",
        "bound-1",
        "must complete and qualify before sbx-2 activation",
        "docker mechanism selection",
        "real-provider custody",
        "windows/wsl feasibility",
    )
    for fragment in required:
        if _normal(fragment) not in text:
            errors.append(f"roadmap regressed current SBX lifecycle/hold: {fragment}")


def _validate_manifest_and_ci(project: dict[str, Any], errors: list[str]) -> None:
    manifest = _normal(project["surfaces"]["manifest"])
    required_manifest = (
        "planning:",
        "lifecycle: docs/development/planning_lifecycle.md",
        "state_record: docs/development/planning_state.json",
        "projection_scope: docs/development/planning_state.json#projection_scope",
        "candidate_register: docs/development/future_candidates.md",
        "boundedness_predecessor: docs/increments/bound-1_boundedness_audit_and_enforcement.md",
        "roadmap: docs/development/roadmap.md",
        "validation_owner: docs/validation/check_planning_foundation.py",
        "active_requires_exact_identities: true",
    )
    for fragment in required_manifest:
        if fragment not in manifest:
            errors.append(f"manifest planning cross-reference/owner is missing: {fragment}")
    ci = project.get("ci_manifest")
    if not isinstance(ci, dict):
        return
    checks = ci.get("checks")
    matching = [
        check
        for check in checks
        if isinstance(check, dict) and check.get("id") == "planning-foundation-validator"
    ] if isinstance(checks, list) else []
    if len(matching) != 1:
        errors.append("planning foundation does not have exactly one CI validation owner")
    elif matching[0].get("command") != ["{python}", VALIDATION_OWNER]:
        errors.append("planning foundation CI owner command drifted")


def _validate_cross_references(project: dict[str, Any], errors: list[str]) -> None:
    for key in PLANNING_SURFACE_KEYS + ("lifecycle",):
        text = project["surfaces"].get(key, "")
        relative = SURFACE_PATHS[key]
        for target in MARKDOWN_LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if target_path.startswith("/"):
                continue
            # Resolve links relative to their owning document, while also
            # allowing a repository-root path in the manifest-like surfaces.
            candidate = posixpath.normpath((relative.parent / target_path).as_posix())
            root_candidate = posixpath.normpath(Path(target_path).as_posix())
            if (
                candidate not in _surface_paths(project)
                and root_candidate not in _surface_paths(project)
                and not (project["root"] / candidate).is_file()
                and not (project["root"] / root_candidate).is_file()
            ):
                errors.append(f"broken planning cross-reference: {relative} -> {target}")
    for key in PLANNING_SURFACE_KEYS:
        if key == "readme":
            continue
        if LIFECYCLE_OWNER.rsplit("/", 1)[-1].lower() not in project["surfaces"][key].lower() and key != "lifecycle":
            errors.append(f"{SURFACE_PATHS[key]} does not point to the canonical lifecycle owner")
    # An arrow graph outside the owner is a competing lifecycle authority.
    for key in PLANNING_SURFACE_KEYS:
        if re.search(r"EXPLORE\s*(?:->|→)\s*PRESERVE", project["surfaces"][key]):
            errors.append(f"competing lifecycle owner or graph found in {SURFACE_PATHS[key]}")


def _validate_authority_ownership(project: dict[str, Any], errors: list[str]) -> None:
    lifecycle = project["surfaces"]["lifecycle"]
    if lifecycle.count(LIFECYCLE_MARKER) != 1:
        errors.append("planning lifecycle has zero or multiple canonical owner markers")
    state = project.get("state")
    if isinstance(state, dict) and state.get("lifecycle_owner") != LIFECYCLE_OWNER:
        errors.append("planning state names a competing lifecycle owner")
    if VALIDATION_OWNER not in project["surfaces"]["manifest"]:
        errors.append("manifest does not name the single planning validation owner")


def validate_state_document(state: dict[str, Any], project: dict[str, Any] | None = None) -> list[str]:
    """Validate a state document in isolation for ACTIVE positive fixtures."""
    fixture = project or {
        "root": ROOT,
        "surfaces": {key: "" for key in SURFACE_PATHS},
        "adr_documents": {},
        "state": state,
        "state_error": None,
        "ci_manifest": {},
        "ci_error": None,
        "unreadable": [],
    }
    errors: list[str] = []
    original = fixture.get("state")
    fixture["state"] = state
    _validate_state(fixture, errors, enforce_canonical_states=False)
    fixture["state"] = original
    return errors


def _positive_active_fixture(project: dict[str, Any]) -> list[str]:
    state = copy.deepcopy(project.get("state"))
    if not isinstance(state, dict):
        return ["positive valid ACTIVE fixture could-not-be-observed"]
    record = next((item for item in state.get("records", []) if item.get("item_id") == "FUT-003"), None)
    if not isinstance(record, dict):
        return ["positive valid ACTIVE fixture has no FUT-003 record"]
    record.pop("planning_authority_binding", None)
    record["transition_history"] = record["transition_history"][:2]
    record["state"] = "ACTIVE"
    record["active_binding"] = {
        "increments": [
            {
                "increment_id": "FP-001",
                "branch": "fm/fp-001",
                "pr_url": "https://github.com/example/sssf/pull/101",
                "source_commit": "a" * 40,
                "source_tree": "b" * 40,
                "authoritative_refs": ["docs/development/FUTURE_CANDIDATES.md"],
            },
            {
                "increment_id": "FM-FP-001",
                "branch": "fm/fm-fp-001",
                "pr_url": "https://github.com/example/sssf/pull/102",
                "source_commit": "c" * 40,
                "source_tree": "d" * 40,
                "authoritative_refs": ["docs/development/FUTURE_CANDIDATES.md"],
            }
        ]
    }
    record["transition_history"].append(
        {
            "from": "SEQUENCED",
            "to": "ACTIVE",
            "evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"],
        }
    )
    errors = validate_state_document(state, project)
    return [f"positive valid ACTIVE fixture failed: {error}" for error in errors]


def _active_state_fixture(project: dict[str, Any]) -> dict[str, Any]:
    state = copy.deepcopy(project["state"])
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record.pop("planning_authority_binding", None)
    record["transition_history"] = record["transition_history"][:2]
    record["state"] = "ACTIVE"
    record["active_binding"] = {
        "increments": [
            {
                "increment_id": increment_id,
                "branch": f"fm/{increment_id.lower()}",
                "pr_url": f"https://github.com/example/sssf/pull/{index}",
                "source_commit": format(index, "040x"),
                "source_tree": format(index + 10, "040x"),
                "authoritative_refs": ["docs/development/FUTURE_CANDIDATES.md"],
            }
            for index, increment_id in enumerate(("FP-001", "FM-FP-001"), 1)
        ]
    }
    record["transition_history"].append(
        {
            "from": "SEQUENCED",
            "to": "ACTIVE",
            "evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"],
        }
    )
    return state


def _proven_state_fixture(project: dict[str, Any]) -> dict[str, Any]:
    state = _active_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    evidence = ["docs/development/FUTURE_CANDIDATES.md"]
    record["state"] = "PROVEN"
    record["transition_history"].append(
        {"from": "ACTIVE", "to": "PROVEN", "evidence_refs": evidence}
    )
    record["proven_proof"] = {
        "accepted_implementation": True,
        "acceptance_evidence_refs": evidence,
        "implementation_evidence_refs": evidence,
        "proof_evidence_refs": evidence,
        "documentation_evidence_refs": evidence,
        "source_commit": "e" * 40,
        "source_tree": "f" * 40,
    }
    return state


def _positive_proven_fixture(project: dict[str, Any]) -> list[str]:
    state = _proven_state_fixture(project)
    errors = validate_state_document(state, project)
    return [f"positive valid PROVEN fixture failed: {error}" for error in errors]


def _positive_superseded_proof_fixture(project: dict[str, Any]) -> list[str]:
    state = _proven_state_fixture(project)
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["state"] = "SUPERSEDED"
    record["transition_history"].append(
        {
            "from": "PROVEN",
            "to": "SUPERSEDED",
            "evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"],
        }
    )
    errors = validate_state_document(state, project)
    return [f"positive valid superseded PROVEN fixture failed: {error}" for error in errors]


def _positive_deferred_fixture(project: dict[str, Any]) -> list[str]:
    state = copy.deepcopy(project["state"])
    record = next(item for item in state["records"] if item["item_id"] == "FUT-003")
    record["transition_history"] = record["transition_history"][:2]
    record.pop("planning_authority_binding", None)
    evidence = ["docs/development/FUTURE_CANDIDATES.md"]
    record["state"] = "DEFERRED"
    record["return_state"] = "SEQUENCED"
    record["transition_history"].append(
        {"from": "SEQUENCED", "to": "DEFERRED", "return_to": "SEQUENCED", "evidence_refs": evidence}
    )
    errors = validate_state_document(state, project)
    record["state"] = "SEQUENCED"
    record.pop("return_state")
    record["transition_history"].append(
        {"from": "DEFERRED", "to": "SEQUENCED", "evidence_refs": evidence}
    )
    errors.extend(validate_state_document(state, project))
    return [f"positive valid DEFERRED fixture failed: {error}" for error in errors]


def _expect_red(
    name: str,
    mutated: dict[str, Any],
    expected: str,
    failures: list[str],
) -> None:
    status, errors = validate_project(mutated, run_controls=False)
    if status != "observed-bad" or not any(expected in error for error in errors):
        failures.append(name)


def _expect_authority_nonpass(
    name: str,
    project: dict[str, Any],
    mutate: Any,
    failures: list[str],
) -> None:
    observation = project.get("authority_observation")
    if not isinstance(observation, dict) or not isinstance(observation.get("source_blobs"), dict):
        failures.append(name)
        return
    mutated = copy.deepcopy(project)
    blobs = copy.deepcopy(observation["source_blobs"])
    try:
        mutate(blobs)
        replacement, replacement_error = _project_authoritative_planning_blobs(
            observation["source_commit"], observation["source_tree"], blobs
        )
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        replacement = None
        replacement_error = f"authority mutation control raised: {error}"
    mutated["authority_observation"] = replacement
    mutated["authority_observation_error"] = replacement_error
    status, _ = validate_project(mutated, run_controls=False)
    if status == "observed-good":
        failures.append(name)


def _remove_authority_heading(blobs: dict[str, str], identity: str) -> None:
    path = "docs/development/ROADMAP.md"
    blocks = _identity_heading_blocks(blobs[path], identity)
    if len(blocks) != 1:
        raise ValueError(f"cannot remove unique authority heading: {identity}")
    blobs[path] = blobs[path].replace(blocks[0], "", 1)


def _materialize_fixture_references(state: dict[str, Any], root: Path) -> None:
    """Create ordinary fixture artifacts without materializing remote identities."""
    references: set[str] = set()
    for record in state.get("records", []):
        if not isinstance(record, dict):
            continue
        for reference in record.get("authoritative_refs", []):
            if isinstance(reference, str):
                references.add(reference)
        for transition in record.get("transition_history", []):
            if isinstance(transition, dict):
                for reference in transition.get("evidence_refs", []):
                    if isinstance(reference, str):
                        references.add(reference)

    root.mkdir(parents=True, exist_ok=True)
    for reference in references:
        path_text = reference.split("#", 1)[0]
        if (
            not path_text
            or _is_remote_reference(reference)
            or _is_remote_reference(path_text)
        ):
            continue
        try:
            path = Path(path_text)
            if (
                path.is_absolute()
                or PureWindowsPath(path_text).is_absolute()
                or ".." in path.parts
            ):
                continue
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("planning validator transient fixture\n", encoding="utf-8")
        except (OSError, ValueError):
            continue


def _watched_symlink_escape_controls(
    project: dict[str, Any], failures: list[str], could_not_observe: list[str]
) -> None:
    """Exercise ACTIVE and every retained-PROVEN evidence path with real links."""
    active_name = "symlink-escape-active-authoritative-reference"
    proven_fields = {
        "acceptance_evidence_refs": "acceptance-evidence",
        "implementation_evidence_refs": "implementation-evidence",
        "proof_evidence_refs": "proof-evidence",
        "documentation_evidence_refs": "documentation-evidence",
    }
    control_names = [active_name]
    control_names.extend(
        f"symlink-escape-proven-{label}" for label in proven_fields.values()
    )

    def create_link(name: str, link: Path, target: Path) -> bool:
        try:
            link.symlink_to(target)
        except (NotImplementedError, OSError) as error:
            start = control_names.index(name)
            remaining = control_names[start:]
            if _is_windows_symlink_capability_error(error):
                could_not_observe.extend(
                    control for control in remaining if control not in could_not_observe
                )
            else:
                failures.extend(
                    f"{control}: unexpected symlink setup failure ({error})"
                    for control in remaining
                    if control not in failures
                )
            return False
        return True

    with tempfile.TemporaryDirectory(prefix="sssf-planning-symlink-controls-") as raw:
        transient = Path(raw).resolve()
        root = transient / "project"
        fixture = copy.deepcopy(project)
        fixture["root"] = root
        state = fixture.get("state")
        if not isinstance(state, dict):
            failures.append(active_name)
            failures.extend(control_names[1:])
            return
        _materialize_fixture_references(state, root)
        outside = transient / "outside"
        outside.mkdir(parents=True, exist_ok=True)

        active_target = outside / "active-authority.md"
        active_target.write_text("outside ACTIVE target\n", encoding="utf-8")
        active_link = root / "docs/development/active-authority-link.md"
        active_link.parent.mkdir(parents=True, exist_ok=True)
        if not create_link(active_name, active_link, active_target):
            return
        active_reference = active_link.relative_to(root).as_posix()
        active_state = _active_state_fixture(fixture)
        active_record = next(
            item for item in active_state["records"] if item["item_id"] == "FUT-003"
        )
        active_record["active_binding"]["increments"][0]["authoritative_refs"] = [
            active_reference
        ]
        active_errors = validate_state_document(active_state, fixture)
        if not any(
            f"authoritative reference {active_reference}" in error
            for error in active_errors
        ):
            failures.append(active_name)

        proven_state = _proven_state_fixture(fixture)
        proven_record = next(
            item for item in proven_state["records"] if item["item_id"] == "FUT-003"
        )
        for field in proven_fields:
            target = outside / f"{field}.json"
            target.write_text(f"outside {field} target\n", encoding="utf-8")
            link = root / "docs" / "development" / f"{field}-link.json"
            if not create_link(f"symlink-escape-proven-{proven_fields[field]}", link, target):
                return
            proven_record["proven_proof"][field] = [
                link.relative_to(root).as_posix()
            ]
        proven_errors = validate_state_document(proven_state, fixture)
        for field, label in proven_fields.items():
            if not any(
                f"lacks retained {field}" in error for error in proven_errors
            ):
                failures.append(f"symlink-escape-proven-{label}")


def _watched_red_controls(
    project: dict[str, Any], could_not_observe: list[str] | None = None
) -> list[str]:
    failures: list[str] = []
    control_cno = could_not_observe if could_not_observe is not None else []

    stale_adr = copy.deepcopy(project)
    stale_adr["surfaces"]["adr_planning"] = stale_adr["surfaces"]["adr_planning"].replace(
        "implementation `ACTIVE` under the authoritative planning generation",
        "implementation unsequenced and inactive",
    )
    _expect_red("stale-contradictory-adr-status", stale_adr, "stale contradictory status", failures)

    omitted_future = copy.deepcopy(project)
    omitted_future["state"]["projection_scope"]["future_items"].pop()
    _expect_red(
        "omitted-future-item-projection",
        omitted_future,
        "omits, adds, or demotes a current FUT item",
        failures,
    )

    omitted_lifecycle = copy.deepcopy(project)
    omitted_lifecycle["state"]["projection_scope"]["lifecycle_identities"] = [
        item
        for item in omitted_lifecycle["state"]["projection_scope"]["lifecycle_identities"]
        if item["identity"] != "WAYFINDER-1"
    ]
    _expect_red(
        "omitted-wayfinder-lifecycle-identity",
        omitted_lifecycle,
        "omits or demotes a LAUNCH/SBX/Wayfinder/DSH identity",
        failures,
    )

    demoted_lifecycle = copy.deepcopy(project)
    for item in demoted_lifecycle["state"]["projection_scope"]["lifecycle_identities"]:
        if item["identity"] == "SBX-1":
            item["state"] = "ACTIVE"
    _expect_red(
        "demoted-sbx-lifecycle-identity",
        demoted_lifecycle,
        "omits or demotes a LAUNCH/SBX/Wayfinder/DSH identity",
        failures,
    )

    omitted_bound1 = copy.deepcopy(project)
    omitted_bound1["state"]["projection_scope"]["lifecycle_identities"] = [
        item
        for item in omitted_bound1["state"]["projection_scope"]["lifecycle_identities"]
        if item["identity"] != "BOUND-1"
    ]
    omitted_bound1["state"]["projection_scope"]["mandatory_predecessors"] = []
    _expect_red(
        "omitted-bound1-predecessor",
        omitted_bound1,
        "BOUND-1 predecessor rule is missing or demoted",
        failures,
    )

    out_of_scope_readiness = copy.deepcopy(project)
    out_of_scope_readiness["state"]["projection_scope"]["not_answerable_queries"] = []
    _expect_red(
        "out-of-scope-sbx2-readiness",
        out_of_scope_readiness,
        "out-of-scope readiness query",
        failures,
    )

    stale_generation = copy.deepcopy(project)
    stale_commit = "5f83760a6d71bb798b9f652f21267fad4b743f16"
    stale_tree = "6e33db5ae5f7d43bf3a7f8c351d888c599d1997d"
    stale_generation_value = _authority_generation(stale_commit, stale_tree)
    stale_source = stale_generation["state"]["authoritative_planning_source"]
    stale_source.update(
        {
            "source_commit": stale_commit,
            "source_tree": stale_tree,
            "generation": stale_generation_value,
        }
    )
    stale_generation["state"]["projection_scope"]["state_basis"].update(
        {
            "source_commit": stale_commit,
            "source_tree": stale_tree,
            "generation": stale_generation_value,
        }
    )
    _expect_red(
        "candidate-authored-stale-generation-self-consistency",
        stale_generation,
        "stale, missing, or mismatched",
        failures,
    )

    def promote_sbx2_authority(blobs: dict[str, str]) -> None:
        path = "docs/development/ROADMAP.md"
        original = blobs[path]
        changed = original.replace("do not establish", "establish", 1)
        if changed == original:
            raise ValueError("SBX-2 unlock boundary mutation did not apply")
        blobs[path] = changed

    _expect_authority_nonpass(
        "authority-sbx2-promotion",
        project,
        promote_sbx2_authority,
        failures,
    )

    for identity in GOVERNED_LIFECYCLE_IDENTITIES:
        _expect_authority_nonpass(
            "authority-omitted-" + identity.lower(),
            project,
            lambda blobs, identity=identity: _remove_authority_heading(blobs, identity),
            failures,
        )

    def duplicate_heading(blobs: dict[str, str], identity: str) -> None:
        path = "docs/development/ROADMAP.md"
        blocks = _identity_heading_blocks(blobs[path], identity)
        if len(blocks) != 1:
            raise ValueError(f"cannot duplicate unique authority heading: {identity}")
        blobs[path] += "\n" + blocks[0]

    for identity in ("LAUNCH-1", "SBX-3", "DSH-1"):
        _expect_authority_nonpass(
            "authority-duplicate-" + identity.lower() + "-heading",
            project,
            lambda blobs, identity=identity: duplicate_heading(blobs, identity),
            failures,
        )

    def duplicate_launch_state(blobs: dict[str, str]) -> None:
        path = "docs/development/ROADMAP.md"
        block = _identity_heading_blocks(blobs[path], "LAUNCH-1")[0]
        blobs[path] = blobs[path].replace(
            block,
            block + "\n**Planning state: `ACTIVE`.**",
            1,
        )

    _expect_authority_nonpass(
        "authority-duplicate-launch-state",
        project,
        duplicate_launch_state,
        failures,
    )

    def contradictory_bound1_state(blobs: dict[str, str]) -> None:
        path = "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"
        blobs[path] += "\n> **Planning state:** `ACTIVE`.\n"

    _expect_authority_nonpass(
        "authority-contradictory-bound1-state",
        project,
        contradictory_bound1_state,
        failures,
    )

    def remove_bound1_relationship(blobs: dict[str, str]) -> None:
        path = "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"
        original = blobs[path]
        changed = original.replace(
            "complete and qualify before `SBX-2` activation",
            "predecessor relationship removed",
            1,
        )
        if changed == original:
            raise ValueError("BOUND-1 relationship mutation did not apply")
        blobs[path] = changed

    _expect_authority_nonpass(
        "authority-removed-bound1-predecessor",
        project,
        remove_bound1_relationship,
        failures,
    )

    def duplicate_future_row(blobs: dict[str, str]) -> None:
        path = "docs/development/FUTURE_CANDIDATES.md"
        row = next(line for line in blobs[path].splitlines() if line.startswith("| FUT-001 |"))
        blobs[path] += "\n" + row

    _expect_authority_nonpass(
        "authority-duplicate-future-item",
        project,
        duplicate_future_row,
        failures,
    )

    def malformed_future_state(blobs: dict[str, str]) -> None:
        path = "docs/development/FUTURE_CANDIDATES.md"
        original = blobs[path]
        changed = original.replace("| FUT-013 | Agent engineering skill repositories as research sources | PRESERVE |", "| FUT-013 | Agent engineering skill repositories as research sources | BROKEN |", 1)
        if changed == original:
            raise ValueError("FUT malformed-state mutation did not apply")
        blobs[path] = changed

    _expect_authority_nonpass(
        "authority-malformed-future-state",
        project,
        malformed_future_state,
        failures,
    )

    illegal = copy.deepcopy(project)
    illegal_record = next(item for item in illegal["state"]["records"] if item["item_id"] == "FUT-003")
    illegal_record["transition_history"][1]["to"] = "ACTIVE"
    _expect_red("illegal-transition", illegal, "illegal/unknown/skipped transition", failures)

    unknown = copy.deepcopy(project)
    unknown_record = next(item for item in unknown["state"]["records"] if item["item_id"] == "FUT-003")
    unknown_record["transition_history"][1]["to"] = "NOT-A-STATE"
    _expect_red("unknown-transition", unknown, "illegal/unknown/skipped transition", failures)

    skipped = copy.deepcopy(project)
    skipped_record = next(item for item in skipped["state"]["records"] if item["item_id"] == "FUT-003")
    skipped_record["transition_history"][1]["from"] = "CANDIDATE"
    _expect_red("skipped-transition", skipped, "illegal/unknown/skipped transition", failures)

    missing_sequenced = copy.deepcopy(project)
    missing_sequenced["state"]["records"] = [
        item for item in missing_sequenced["state"]["records"] if item["item_id"] != "FUT-003"
    ]
    _expect_red("missing-durable-sequenced-record", missing_sequenced, "missing durable planning state record", failures)

    unbound_active = copy.deepcopy(project)
    active_record = next(item for item in unbound_active["state"]["records"] if item["item_id"] == "FUT-003")
    active_record.pop("planning_authority_binding", None)
    active_record["state"] = "ACTIVE"
    active_record["transition_history"].append(
        {"from": "SEQUENCED", "to": "ACTIVE", "evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"]}
    )
    active_record["active_binding"] = None
    _expect_red("unbound-active-identity", unbound_active, "unbound or partial ACTIVE identity", failures)

    partial_active = copy.deepcopy(unbound_active)
    partial_record = next(item for item in partial_active["state"]["records"] if item["item_id"] == "FUT-003")
    partial_record["active_binding"] = {"increments": [{"increment_id": "FP-001", "branch": "fm/fp-001"}]}
    _expect_red("partial-active-identity", partial_active, "unbound or partial ACTIVE identity", failures)

    for name, mutate in (
        ("omitted-active-increment", lambda increments: increments.pop()),
        (
            "extra-active-increment",
            lambda increments: increments.append({**increments[0], "increment_id": "EXTRA-001"}),
        ),
        ("duplicate-active-increment", lambda increments: increments.__setitem__(1, copy.deepcopy(increments[0]))),
    ):
        active_state = _active_state_fixture(project)
        active_record = next(item for item in active_state["records"] if item["item_id"] == "FUT-003")
        mutate(active_record["active_binding"]["increments"])
        if not any("exactly cover unique planned increments" in error for error in validate_state_document(active_state, project)):
            failures.append(name)

    incomplete_proof = _active_state_fixture(project)
    proof_record = next(item for item in incomplete_proof["records"] if item["item_id"] == "FUT-003")
    proof_record["state"] = "PROVEN"
    proof_record["transition_history"].append(
        {"from": "ACTIVE", "to": "PROVEN", "evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"]}
    )
    proof_record["proven_proof"] = {"proof_evidence_refs": ["docs/development/FUTURE_CANDIDATES.md"]}
    if not any("PROVEN transition lacks" in error for error in validate_state_document(incomplete_proof, project)):
        failures.append("incomplete-proven-proof-contract")

    for name, reference in (
        ("remote-proven-evidence", "https://example.invalid/proof.json"),
        ("absolute-proven-evidence", "/etc/hosts"),
        ("parent-proven-evidence", "../proof.json"),
    ):
        escaped_proof = _proven_state_fixture(project)
        escaped_proof_record = next(
            item for item in escaped_proof["records"] if item["item_id"] == "FUT-003"
        )
        escaped_proof_record["proven_proof"]["proof_evidence_refs"] = [reference]
        if not any(
            "lacks retained proof_evidence_refs" in error
            for error in validate_state_document(escaped_proof, project)
        ):
            failures.append(name)

    for name, field, value in (
        ("whitespace-active-branch", "branch", " bad branch "),
        ("malformed-active-branch", "branch", "bad..branch"),
        ("non-pr-active-identity", "pr_url", "not-a-pr"),
        ("insecure-active-pr", "pr_url", "http://github.com/example/sssf/pull/1"),
        ("queried-active-pr", "pr_url", "https://github.com/example/sssf/pull/1?x=1"),
        ("fragmented-active-pr", "pr_url", "https://github.com/example/sssf/pull/1#x"),
        ("nonpositive-active-pr", "pr_url", "https://github.com/example/sssf/pull/0"),
    ):
        malformed_active = _active_state_fixture(project)
        malformed_record = next(
            item for item in malformed_active["records"] if item["item_id"] == "FUT-003"
        )
        malformed_record["active_binding"]["increments"][0][field] = value
        if not any(
            f"increment 0 field {field}" in error
            for error in validate_state_document(malformed_active, project)
        ):
            failures.append(name)

    active_with_proof = _active_state_fixture(project)
    active_proof_record = next(
        item for item in active_with_proof["records"] if item["item_id"] == "FUT-003"
    )
    evidence = ["docs/development/FUTURE_CANDIDATES.md"]
    active_proof_record["proven_proof"] = {
        "accepted_implementation": True,
        "acceptance_evidence_refs": evidence,
        "implementation_evidence_refs": evidence,
        "proof_evidence_refs": evidence,
        "documentation_evidence_refs": evidence,
        "source_commit": "e" * 40,
        "source_tree": "f" * 40,
    }
    if not any(
        "PROVEN proof claim without legal PROVEN history" in error
        for error in validate_state_document(active_with_proof, project)
    ):
        failures.append("proven-proof-outside-proven-state")

    broken_active_reference = _active_state_fixture(project)
    broken_reference_record = next(
        item
        for item in broken_active_reference["records"]
        if item["item_id"] == "FUT-003"
    )
    broken_reference_record["active_binding"]["increments"][0][
        "authoritative_refs"
    ] = ["docs/does-not-exist.md"]
    if not any(
        "authoritative reference docs/does-not-exist.md" in error
        for error in validate_state_document(broken_active_reference, project)
    ):
        failures.append("broken-active-authoritative-reference")

    for name, reference in (
        ("remote-active-authoritative-reference", "https://example.invalid/authority.md"),
        ("absolute-active-authoritative-reference", "/etc/hosts"),
        ("parent-active-authoritative-reference", "../authority.md"),
    ):
        escaped_reference = _active_state_fixture(project)
        escaped_record = next(
            item for item in escaped_reference["records"] if item["item_id"] == "FUT-003"
        )
        escaped_record["active_binding"]["increments"][0]["authoritative_refs"] = [reference]
        if not any(
            f"authoritative reference {reference}" in error
            for error in validate_state_document(escaped_reference, project)
        ):
            failures.append(name)
    _watched_symlink_escape_controls(project, failures, control_cno)

    invented_return = copy.deepcopy(project["state"])
    deferred_record = next(item for item in invented_return["records"] if item["item_id"] == "FUT-003")
    evidence = ["docs/development/FUTURE_CANDIDATES.md"]
    deferred_record["state"] = "DECIDED"
    deferred_record["transition_history"].extend(
        [
            {"from": "SEQUENCED", "to": "DEFERRED", "return_to": "SEQUENCED", "evidence_refs": evidence},
            {"from": "DEFERRED", "to": "DECIDED", "return_to": "DECIDED", "evidence_refs": evidence},
        ]
    )
    if not any("deferred re-entry" in error for error in validate_state_document(invented_return, project)):
        failures.append("invented-deferred-return-state")

    unsafe_router = copy.deepcopy(project)
    unsafe_router["surfaces"]["readme"] = unsafe_router["surfaces"]["readme"].replace(
        "`ACTIVE` is engineering authorization only. `ACTIVE` is intake eligibility",
        "`ACTIVE` is runtime authority.",
        1,
    )
    _expect_red(
        "active-not-proven-runtime-or-landing-authority",
        unsafe_router,
        "planning router is missing authority clarification",
        failures,
    )

    duplicate_adr = copy.deepcopy(project)
    duplicate_adr["adr_documents"]["ADR-0007-DUPLICATE.md"] = "# ADR-0007 — duplicate identity\n"
    _expect_red("duplicate-adr-identity", duplicate_adr, "duplicate or missing ADR-0007 identity", failures)

    stale_roadmap = copy.deepcopy(project)
    stale_roadmap["surfaces"]["roadmap"] = stale_roadmap["surfaces"]["roadmap"].replace(
        "SBX-2 is held.", "SBX-2 is planned."
    )
    _expect_red("stale-roadmap-sbx-regression", stale_roadmap, "roadmap regressed current SBX lifecycle/hold", failures)

    competing_owner = copy.deepcopy(project)
    competing_owner["surfaces"]["candidates"] += "\nEXPLORE -> PRESERVE -> CANDIDATE -> DECIDED\n"
    _expect_red("competing-lifecycle-owner", competing_owner, "competing lifecycle owner or graph", failures)

    broken_link = copy.deepcopy(project)
    broken_link["surfaces"]["candidates"] += "\n[broken planning reference](docs/missing-planning-record.md)\n"
    _expect_red("broken-planning-cross-reference", broken_link, "broken planning cross-reference", failures)

    failures.extend(_watched_test_closure_controls())
    failures.extend(_positive_active_fixture(project))
    failures.extend(_positive_proven_fixture(project))
    failures.extend(_positive_superseded_proof_fixture(project))
    failures.extend(_positive_deferred_fixture(project))
    return failures


def validate_project(
    project: dict[str, Any],
    *,
    run_controls: bool = True,
    control_cno: list[str] | None = None,
    control_failures: list[str] | None = None,
) -> tuple[str, list[str]]:
    errors: list[str] = []
    cno: list[str] = []
    red_failures: list[str] = []
    _check_required_files(project, errors, cno)
    if cno:
        errors.extend(cno)
        if control_cno is not None:
            control_cno.extend(cno)
        return "could-not-observe", errors
    _validate_authoritative_planning_source(project, errors)
    _validate_lifecycle(project, errors)
    _validate_state(project, errors)
    _validate_document_states(project, errors)
    _validate_router_and_authority(project, errors)
    _validate_adr_identities(project, errors)
    _validate_roadmap_sbx_hold(project, errors)
    _validate_manifest_and_ci(project, errors)
    _validate_cross_references(project, errors)
    _validate_authority_ownership(project, errors)
    state_records = project.get("state", {}).get("records") if isinstance(project.get("state"), dict) else None
    can_run_controls = isinstance(state_records, list) and {
        item.get("item_id") for item in state_records if isinstance(item, dict)
    } >= set(EXPECTED_ITEM_STATES)
    if run_controls and can_run_controls:
        red_failures = _watched_red_controls(project, cno)
        if red_failures:
            errors.append("watched-red controls did not go red: " + ", ".join(red_failures))
    if control_cno is not None:
        control_cno.extend(item for item in cno if item not in control_cno)
    if control_failures is not None:
        control_failures.extend(item for item in red_failures if item not in control_failures)
    status = _fold_property_outcome(errors, cno)
    return status, errors


def validate_path(
    root: Path = ROOT, *, control_cno: list[str] | None = None
) -> tuple[str, list[str], list[str]]:
    project = load_project(root)
    red_failures: list[str] = []
    status, errors = validate_project(
        project, control_cno=control_cno, control_failures=red_failures
    )
    return status, errors, red_failures


def main() -> int:
    control_cno: list[str] = []
    status, errors, red_failures = validate_path(ROOT, control_cno=control_cno)
    closure_status, closure_errors = run_test_closure()
    if closure_status == "observed-bad":
        status = "observed-bad"
        errors.extend("test closure: " + error for error in closure_errors)
    elif closure_status == "could-not-observe":
        if status != "observed-bad":
            status = "could-not-observe"
        control_cno.extend(
            "test-closure: " + error
            for error in closure_errors
            if "test-closure: " + error not in control_cno
        )
    result = _machine_result(status, errors=errors, cno=control_cno)
    print(f"planning foundation validation: {status}")
    print(json.dumps(result, sort_keys=True))
    print(f"lifecycle owner: {LIFECYCLE_OWNER}")
    print(f"validation owner: {VALIDATION_OWNER}")
    print(
        "watched-red: stale-contradictory-adr-status, omitted-future-item-projection, "
        "omitted-wayfinder-lifecycle-identity, demoted-sbx-lifecycle-identity, "
        "omitted-bound1-predecessor, out-of-scope-sbx2-readiness, "
        "candidate-authored-stale-generation-self-consistency, authority-sbx2-promotion, "
        "authority-omitted-governed-identities, authority-duplicate-headings-and-states, "
        "authority-removed-bound1-predecessor, authority-future-register-integrity, "
        "illegal-transition, unknown-transition, skipped-transition, missing-durable-sequenced-record, "
        "unbound-active-identity, partial-active-identity, "
        "omitted-active-increment, extra-active-increment, duplicate-active-increment, "
        "incomplete-proven-proof-contract, invented-deferred-return-state, "
        "remote-proven-evidence, absolute-proven-evidence, parent-proven-evidence, "
        "whitespace-active-branch, malformed-active-branch, non-pr-active-identity, "
        "insecure-active-pr, queried-active-pr, fragmented-active-pr, nonpositive-active-pr, "
        "proven-proof-outside-proven-state, broken-active-authoritative-reference, "
        "remote-active-authoritative-reference, absolute-active-authoritative-reference, "
        "parent-active-authoritative-reference, "
        "symlink-escape-active-authoritative-reference, "
        "symlink-escape-proven-acceptance-evidence, "
        "symlink-escape-proven-implementation-evidence, "
        "symlink-escape-proven-proof-evidence, "
        "symlink-escape-proven-documentation-evidence, "
        "closure-zero-selection, closure-selector-typo, closure-nonexistent-identity, "
        "closure-required-identity-removed, closure-collection-failure, "
        "closure-required-pass, closure-required-fail, closure-fail-over-collection-cno, "
        "active-not-proven-runtime-or-landing-authority, duplicate-adr-identity, "
        "stale-roadmap-sbx-regression, competing-lifecycle-owner, "
        "broken-planning-cross-reference"
    )
    if status == "could-not-observe":
        for control in control_cno:
            print(f"unverified CNO control: {control}")
        print("symlink property was not claimed as executed")
    elif errors:
        for error in errors:
            print(f"- {error}")
        for control in control_cno:
            print(f"unverified CNO control: {control}")
    elif red_failures:
        for failure in red_failures:
            print(f"- watched-red control did not fail closed: {failure}")
    else:
        print("positive case: canonical lifecycle, authoritative planning generation, and current SBX holds")
        print("positive ACTIVE fixture: exact increment/branch/PR/source identities validate in memory")
        print("positive PROVEN fixture: accepted proof contract validates in memory")
        print("positive SUPERSEDED fixture: historical accepted proof remains valid in memory")
        print("positive DEFERRED fixture: retained return state validates in memory")
        print("watched-red: all controls observed-bad under in-memory defects")
        print("side effects: none")
    return _validator_exit_code(status)


if __name__ == "__main__":
    raise SystemExit(main())
