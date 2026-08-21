"""Validate deterministic CI and watch each non-vacuity failure control go red."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import ci_gate  # noqa: E402

WORKFLOW = Path(".github/workflows/ci.yml")
MANIFEST = Path("ci/checks.json")
EXPECTED_ACTIONS = {
    "actions/checkout": "11bd71901bbe5b1630ceea73d27597364c9af683",
    "actions/setup-python": "a26af69be951a213d495a4c3e4e4022e16d87065",
    "oven-sh/setup-bun": "735343b667d3e6f658f44d0eca948eb6282f2b76",
    "extractions/setup-just": "dd310ad5a97d8e7b41793f8ef055398d51ad4de6",
}
B4_002_SCOPE_SUBJECT = {
    "id": "B4-002-production-integration-boundary",
    "evidence_kind": "historical-byte-identity",
    "repository": "https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git",
    "evaluation": {
        "head": "923c0e4ce6be4ed3a141d3ee2fb7f186962c37ae",
        "tree": "6e840e665ffc043c3ad3778f68876f5d85ae3303",
        "canonical_main": "a984f6cf0a89503d3db8855ccd820b83e9ee60a1",
        "files": [
            "adws/adw_modules/agent_pi.py",
            "adws/adw_modules/agents.py",
            "adws/adw_modules/data_types.py",
            "adws/adw_modules/console.py",
            "adws/adw_modules/gates.py",
            "adws/adw_modules/permissions.py",
        ],
    },
    "authorization_scope": "historical-b4-002-increment-boundary-only",
    "current_production_qualification": "NON_PASS",
    "global_production_qualification": "NON_PASS",
}
B4_002_HISTORICAL_CONSUMPTION = "historical-b4-002-increment-boundary-only"


EXPECTED_CHECKS = {
    "ci-contract-and-watched-red-controls": (
        "{python}", "docs/validation/check_ci_contract.py"
    ),
    "agent-bootstrap-validator": (
        "{python}", "docs/validation/check_agent_bootstrap.py"
    ),
    "line-ending-validator": (
        "{python}", "docs/validation/check_line_endings.py", "--require-worktree-lf"
    ),
    "sqlite-free-observability-validator": (
        "{python}", "docs/validation/check_obs_query.py"
    ),
    "sandbox-source-contract-validator": (
        "{python}", "docs/validation/check_sandbox_source_contract.py"
    ),
    "executor-supervisor-and-pi-adapter-validator": (
        "{python}", "docs/validation/check_executor_supervisor.py"
    ),
    "production-extension-path-validator": (
        "{python}", "docs/validation/check_production_extension_path.py"
    ),
    "sbx0-semantics-inventory-validator": (
        "{python}", "docs/validation/check_sbx0_inventory.py"
    ),
    "sandbox-provider-contract-validator": (
        "{python}", "docs/validation/check_sandbox_provider.py"
    ),
    "inkwell-unit-tests": ("just", "inkwell", "test"),
}


def b4_002_scope_authorization(subject: object, consumption: str) -> str:
    """Return PASS only for the immutable B4-002 historical subject boundary."""
    if subject != B4_002_SCOPE_SUBJECT:
        return "NON_PASS"
    if consumption != B4_002_HISTORICAL_CONSUMPTION:
        return "NON_PASS"
    return "PASS"


def proof_scope_errors(document: object) -> list[str]:
    if not isinstance(document, dict):
        return ["verification contract document is not an object"]
    contract = document.get("verification_contract")
    if not isinstance(contract, dict) or contract.get("schema_version") != 1:
        return ["verification contract is missing or has an unsupported schema"]
    subjects = contract.get("proof_subjects")
    if not isinstance(subjects, list) or len(subjects) != 1:
        return ["verification contract must declare exactly one B4-002 proof subject"]
    subject = subjects[0]
    if b4_002_scope_authorization(subject, B4_002_HISTORICAL_CONSUMPTION) != "PASS":
        return ["B4-002 proof subject does not bind the exact historical repository/head/tree/file scope"]
    errors = []
    for consumption in ("current-production-qualification", "global-production-qualification"):
        if b4_002_scope_authorization(subject, consumption) == "PASS":
            errors.append(f"B4-002 historical evidence authorized {consumption}")
    return errors


def contract_errors(root: Path) -> list[str]:
    errors: list[str] = []
    workflow_path = root / WORKFLOW
    workflow_files = sorted((root / ".github" / "workflows").glob("*.y*ml"))

    if workflow_files != [workflow_path]:
        errors.append("workflow path drift: expected only .github/workflows/ci.yml")
    if not workflow_path.is_file():
        return errors or ["workflow path drift: ci.yml is missing"]

    text = workflow_path.read_text(encoding="utf-8")
    required_fragments = (
        "on:\n  pull_request:\n    branches: [main]\n  push:\n    branches: [main]",
        "permissions:\n  contents: read",
        "concurrency:\n  group: deterministic-ci-${{ github.event.pull_request.number || github.ref }}\n  cancel-in-progress: true",
        "timeout-minutes: 10",
        "fail-fast: false",
        "os: [ubuntu-24.04, windows-2022]",
        "ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}",
        "persist-credentials: false",
        "python-version: '3.12.8'",
        "check-latest: false",
        "token: ''",
        "bun-version: '1.3.14'",
        "no-cache: true",
        "just-version: '1.58.0'",
        "github-token: ''",
        "python tools/ci_gate.py run --evidence ci-evidence-${{ runner.os }}.json",
    )
    for fragment in required_fragments:
        if fragment not in text:
            errors.append(f"workflow contract missing: {fragment.splitlines()[0]}")

    for forbidden in ("pull_request_target:", "paths:", "paths-ignore:", "secrets."):
        if forbidden in text:
            errors.append(f"workflow contains forbidden trigger/credential surface: {forbidden}")

    observed_actions = dict(
        re.findall(r"uses:\s+([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([0-9a-f]{40})", text)
    )
    if observed_actions != EXPECTED_ACTIONS:
        errors.append(f"action pins differ: {observed_actions!r}")
    if len(re.findall(r"^\s*uses:", text, flags=re.MULTILINE)) != len(EXPECTED_ACTIONS):
        errors.append("an action is unpinned or an unexpected action was added")

    manifest_path = root / MANIFEST
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"verification contract could not be observed: {exc}")
        return errors
    errors.extend(proof_scope_errors(document))
    try:
        checks = ci_gate.load_checks(manifest_path)
    except ValueError as exc:
        errors.append(str(exc))
        return errors

    observed_checks = {
        check["id"]: tuple(check["command"])
        for check in checks
    }
    if observed_checks != EXPECTED_CHECKS:
        errors.append(f"enumerated offline checks differ: {observed_checks!r}")
    return errors


def fixture_manifest(path: Path, command: list[str], timeout: int = 5) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "checks": [
                    {"id": "control", "command": command, "timeout_seconds": timeout}
                ],
            }
        ),
        encoding="utf-8",
    )


def read_evidence(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def watched_red_errors() -> list[str]:
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sssf-ci-controls-") as raw_temp:
        temp = Path(raw_temp)

        empty_manifest = temp / "empty.json"
        empty_evidence = temp / "empty-evidence.json"
        empty_manifest.write_text('{"schema_version": 1, "checks": []}', encoding="utf-8")
        if ci_gate.execute(empty_manifest, empty_evidence) == 0:
            errors.append("empty check discovery did not go red")
        empty = read_evidence(empty_evidence)
        if (empty["conclusion"], empty["discovered_checks"]) != ("could-not-observe", 0):
            errors.append("empty check discovery lost CNO evidence")

        failing_manifest = temp / "failing.json"
        failing_evidence = temp / "failing-evidence.json"
        fixture_manifest(failing_manifest, ["{python}", "-c", "raise SystemExit(7)"])
        if ci_gate.execute(failing_manifest, failing_evidence) == 0:
            errors.append("deliberately failing validator did not go red")
        if read_evidence(failing_evidence)["conclusion"] != "observed-bad":
            errors.append("failing validator was not preserved as observed-bad")

        missing_manifest = temp / "missing.json"
        missing_evidence = temp / "missing-evidence.json"
        fixture_manifest(missing_manifest, ["sssf-tool-that-does-not-exist-6f65d2"])
        if ci_gate.execute(missing_manifest, missing_evidence) == 0:
            errors.append("missing tool did not go red")
        if read_evidence(missing_evidence)["conclusion"] != "could-not-observe":
            errors.append("missing tool was narrowed away from CNO")

        timeout_manifest = temp / "timeout.json"
        timeout_evidence = temp / "timeout-evidence.json"
        fixture_manifest(
            timeout_manifest,
            ["{python}", "-c", "import time; time.sleep(2)"],
            timeout=1,
        )
        if ci_gate.execute(timeout_manifest, timeout_evidence) == 0:
            errors.append("timeout did not go red")
        if read_evidence(timeout_evidence)["conclusion"] != "could-not-observe":
            errors.append("timeout was narrowed away from CNO")

        cancel_manifest = temp / "cancel.json"
        cancel_evidence = temp / "cancel-evidence.json"
        fixture_manifest(cancel_manifest, ["{python}", "-c", "import time; time.sleep(2)"])
        ci_gate._CANCEL_REQUESTED = True
        try:
            if ci_gate.execute(cancel_manifest, cancel_evidence) == 0:
                errors.append("cancellation did not go red")
        finally:
            ci_gate._CANCEL_REQUESTED = False
        cancelled = read_evidence(cancel_evidence)
        if cancelled["conclusion"] != "could-not-observe":
            errors.append("cancellation was narrowed away from CNO")

        contract_root = temp / "contract"
        (contract_root / ".github" / "workflows").mkdir(parents=True)
        (contract_root / "ci").mkdir()
        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        shutil.copy2(ROOT / MANIFEST, contract_root / MANIFEST)

        workflow_text = (contract_root / WORKFLOW).read_text(encoding="utf-8")
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace("pull_request:", "pull_request_target:", 1),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("trigger drift did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "os: [ubuntu-24.04, windows-2022]", "os: []", 1
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("empty OS matrix did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "          ref: ${{ github.event_name == 'pull_request' && github.event.pull_request.head.sha || github.sha }}\n",
                "",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("missing exact-head checkout did not go red")

        shutil.copy2(ROOT / WORKFLOW, contract_root / WORKFLOW)
        (contract_root / WORKFLOW).write_text(
            workflow_text.replace(
                "github.event.pull_request.head.sha || github.sha",
                "github.sha || github.sha",
                1,
            ),
            encoding="utf-8",
        )
        if not contract_errors(contract_root):
            errors.append("substituted exact-head checkout did not go red")

        (contract_root / WORKFLOW).unlink()
        shutil.copy2(ROOT / WORKFLOW, contract_root / ".github" / "workflows" / "drift.yml")
        if not contract_errors(contract_root):
            errors.append("workflow path drift did not go red")

        contract_document = json.loads((contract_root / MANIFEST).read_text(encoding="utf-8"))
        bad_head = copy.deepcopy(contract_document)
        bad_head["verification_contract"]["proof_subjects"][0]["evaluation"]["head"] = "0" * 40
        if b4_002_scope_authorization(
            bad_head["verification_contract"]["proof_subjects"][0],
            B4_002_HISTORICAL_CONSUMPTION,
        ) == "PASS":
            errors.append("B4-002 head-scope drift did not go red")

        global_claim = copy.deepcopy(contract_document)
        global_claim["verification_contract"]["proof_subjects"][0][
            "authorization_scope"
        ] = "global-production-qualification"
        if b4_002_scope_authorization(
            global_claim["verification_contract"]["proof_subjects"][0],
            "global-production-qualification",
        ) == "PASS":
            errors.append("B4-002 global production consumption did not go red")

    return errors


def main() -> int:
    errors = contract_errors(ROOT)
    if not errors:
        errors.extend(watched_red_errors())

    if errors:
        print("B4-001 deterministic CI contract: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("B4-001 deterministic CI contract: PASS")
    print(f"{len(EXPECTED_CHECKS)} offline checks enumerated; Linux and Windows matrix is nonempty")
    print("watched-red: empty discovery/matrix, validator failure, missing tool")
    print("watched-red: cancellation/timeout and workflow path/trigger drift")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
