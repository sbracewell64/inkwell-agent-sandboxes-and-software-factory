from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import types

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

import evidence_manifest as manifest_module  # noqa: E402
from evidence_manifest import (  # noqa: E402
    Observation,
    ValidationContext,
    canonical_manifest_bytes,
    validate_manifest,
)

FIXTURE = ROOT / "docs/validation/fixtures/evidence_manifest/positive"
MANIFEST = FIXTURE / "manifest.json"
TOOL_SOURCE = TOOLS / "evidence_manifest.py"
EVIDENCE_DIR = ROOT / "docs/evidence/hd08"
CONTEXT = ValidationContext(
    canonical_url=(
        "https://github.com/sbracewell64/"
        "inkwell-agent-sandboxes-and-software-factory.git"
    ),
    base_sha="04e5484a6190f033d25e1626b96a4cca93b7f755",
    candidate_sha="1111111111111111111111111111111111111111",
    branch="fixture/hd08",
    worktree_role="proof-clone",
    run_id="fixture-run-001",
    adw_id="fixture-adw-001",
    purpose="hd08-fixture-proof",
    required_phases=("BUILD", "TEST"),
    required_dimensions=(
        "artifact-integrity",
        "deterministic-tests",
        "trace-session",
    ),
)


def load_manifest(path: Path = MANIFEST) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(root: Path, manifest: dict[str, object]) -> None:
    (root / "manifest.json").write_bytes(canonical_manifest_bytes(manifest))


def validate(root: Path, context: ValidationContext = CONTEXT):
    return validate_manifest(root / "manifest.json", root, context)


def expect(
    errors: list[str],
    label: str,
    actual: Observation,
    expected: Observation,
) -> None:
    if actual is not expected:
        errors.append(f"{label}: expected {expected.value}, got {actual.value}")


def set_artifact(item: dict[str, object], path: Path) -> None:
    raw = path.read_bytes()
    item["byte_length"] = len(raw)
    item["sha256"] = hashlib.sha256(raw).hexdigest()


def intermediate_directory_symlink_swap_control(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="sssf-hd08-symlink-swap-") as temp_dir:
        temp = Path(temp_dir)
        root = temp / "root"
        nested = root / "nested"
        outside = temp / "outside"
        nested.mkdir(parents=True)
        outside.mkdir()
        inside_bytes = b"inside-root-evidence\n"
        outside_bytes = b"outside-root-substitution\n"
        (nested / "payload.txt").write_bytes(inside_bytes)
        (outside / "payload.txt").write_bytes(outside_bytes)
        context = ValidationContext(
            canonical_url=CONTEXT.canonical_url,
            base_sha=CONTEXT.base_sha,
            candidate_sha=CONTEXT.candidate_sha,
            branch=CONTEXT.branch,
            worktree_role=CONTEXT.worktree_role,
            run_id="symlink-swap-run",
            adw_id=None,
            purpose="symlink-swap-control",
            required_phases=("BUILD",),
            required_dimensions=("path-confinement",),
        )
        document = {
            "schema_version": "sssf.evidence-manifest.v1",
            "repository": {
                "canonical_url": context.canonical_url,
                "base_sha": context.base_sha,
                "candidate_sha": context.candidate_sha,
                "branch": context.branch,
                "worktree_role": context.worktree_role,
            },
            "run": {
                "run_id": context.run_id,
                "adw_id": None,
                "terminal_outcome": "succeeded",
            },
            "purpose": context.purpose,
            "required_phases": ["BUILD"],
            "required_dimensions": ["path-confinement"],
            "inventory": [
                {
                    "sequence": 0,
                    "path": "nested/payload.txt",
                    "artifact_type": "text",
                    "byte_length": len(outside_bytes),
                    "sha256": hashlib.sha256(outside_bytes).hexdigest(),
                    "producer": "race-control",
                    "run_id": context.run_id,
                    "adw_id": None,
                    "phase": "BUILD",
                    "purpose": context.purpose,
                    "terminal_outcome": "succeeded",
                    "evidence_class": "qualifying",
                    "claimed_dimensions": ["path-confinement"],
                }
            ],
        }
        write_manifest(root, document)
        original_open = manifest_module.os.open
        original_read = manifest_module.os.read
        original_primitive_check = getattr(
            manifest_module,
            "_descriptor_primitives_available",
            None,
        )
        swapped = False
        captured_reads: list[bytes] = []

        def swap_then_open(path, flags, *args, **kwargs):
            nonlocal swapped
            path_text = str(path)
            if not swapped and path_text.endswith("payload.txt"):
                swapped = True
                nested.rename(root / "validated-nested")
                nested.symlink_to(outside, target_is_directory=True)
            return original_open(path, flags, *args, **kwargs)

        def record_read(descriptor: int, length: int) -> bytes:
            chunk = original_read(descriptor, length)
            captured_reads.append(chunk)
            return chunk

        manifest_module.os.open = swap_then_open
        manifest_module.os.read = record_read
        if original_primitive_check is not None:
            manifest_module._descriptor_primitives_available = lambda: True
        try:
            result = validate_manifest(root / "manifest.json", root, context)
        finally:
            manifest_module.os.open = original_open
            manifest_module.os.read = original_read
            if original_primitive_check is not None:
                manifest_module._descriptor_primitives_available = original_primitive_check

        if not swapped:
            errors.append("intermediate-directory-symlink-swap: boundary was not exercised")
        if result.observation is Observation.OBSERVED_GOOD:
            errors.append(
                "intermediate-directory-symlink-swap: outside-root bytes were accepted"
            )
        if "nested/payload.txt" in result.checked_inventory:
            errors.append(
                "intermediate-directory-symlink-swap: escaped artifact entered checked inventory"
            )
        if outside_bytes in b"".join(captured_reads):
            errors.append(
                "intermediate-directory-symlink-swap: outside-root bytes were read"
            )


def descriptor_path_controls(errors: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="sssf-hd08-descriptor-controls-") as temp_dir:
        temp = Path(temp_dir)

        root_link = temp / "root-link"
        root_link.symlink_to(FIXTURE, target_is_directory=True)
        root_result = validate_manifest(root_link / "manifest.json", root_link, CONTEXT)
        expect(
            errors,
            "root symlink",
            root_result.observation,
            Observation.OBSERVED_BAD,
        )

        original_primitive_check = manifest_module._descriptor_primitives_available
        manifest_module._descriptor_primitives_available = lambda: False
        try:
            unsupported = validate_manifest(MANIFEST, FIXTURE, CONTEXT)
        finally:
            manifest_module._descriptor_primitives_available = original_primitive_check
        expect(
            errors,
            "unsupported descriptor host",
            unsupported.observation,
            Observation.CNO,
        )

        changing_root = temp / "identity-change"
        shutil.copytree(FIXTURE, changing_root)
        changing_path = changing_root / "artifacts/build-result.json"
        original_read = manifest_module.os.read
        changed = False

        def read_then_change(descriptor: int, length: int) -> bytes:
            nonlocal changed
            chunk = original_read(descriptor, length)
            if chunk and not changed:
                changed = True
                with changing_path.open("ab") as stream:
                    stream.write(b"changed-during-read\n")
            return chunk

        manifest_module.os.read = read_then_change
        try:
            changed_result = validate_manifest(
                changing_root / "manifest.json",
                changing_root,
                CONTEXT,
            )
        finally:
            manifest_module.os.read = original_read
        if not changed:
            errors.append("artifact identity-change control was not exercised")
        expect(
            errors,
            "artifact identity change",
            changed_result.observation,
            Observation.CNO,
        )


INTERMEDIATE_TOCTTOU_MUTATIONS = (
    (
        """                next_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=current_descriptor,
                )""",
        """                next_descriptor = os.open(
                    component,
                    directory_flags & ~os.O_NOFOLLOW,
                    dir_fd=current_descriptor,
                )""",
    ),
    (
        "            if not stat.S_ISDIR(after.st_mode) or _changed_identity(before, after):",
        "            if not stat.S_ISDIR(after.st_mode):",
    ),
)


def defective_intermediate_variant() -> tuple[types.ModuleType, str]:
    """Build the bounded defective variant used to calibrate the intermediate
    time-of-check-to-time-of-use control.

    It removes exactly two intermediate-component protections and nothing else:
    the no-follow flag on the descriptor-relative open, and the identity
    reconciliation of the descriptor that open returned. The mutated program is
    content-addressed so the calibration binds to exact bytes rather than to a
    Git object that may stop being fetchable.
    """
    source = TOOL_SOURCE.read_bytes().decode("utf-8")
    for original, replacement in INTERMEDIATE_TOCTTOU_MUTATIONS:
        if source.count(original) != 1:
            raise RuntimeError(
                "intermediate-component-tocttou: defective variant could not be "
                "built; expected exactly one occurrence of a mutation site"
            )
        source = source.replace(original, replacement)
    mutated = source.encode("utf-8")
    digest = hashlib.sha256(mutated).hexdigest()
    module = types.ModuleType("evidence_manifest_intermediate_defect")
    module.__file__ = str(TOOL_SOURCE)
    # dataclasses resolves a class's defining module through sys.modules, so the
    # variant has to be registered before its body executes.
    sys.modules[module.__name__] = module
    exec(compile(mutated, "<hd08-intermediate-defect>", "exec"), module.__dict__)
    return module, digest


def intermediate_component_tocttou_control(module: types.ModuleType) -> list[str]:
    """Swap an intermediate path component for an outside-root symlink inside the
    window between its no-follow stat and its descriptor-relative open.

    Returns the findings observed against `module`. An empty list means the
    implementation refused the swap without reading or admitting outside bytes.
    """
    findings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sssf-hd08-intermediate-tocttou-") as temp_dir:
        temp = Path(temp_dir)
        root = temp / "root"
        nested = root / "nested"
        outside = temp / "outside"
        nested.mkdir(parents=True)
        outside.mkdir()
        inside_bytes = b"inside-root-intermediate-evidence\n"
        outside_bytes = b"outside-root-intermediate-substitution\n"
        (nested / "payload.txt").write_bytes(inside_bytes)
        (outside / "payload.txt").write_bytes(outside_bytes)
        context = ValidationContext(
            canonical_url=CONTEXT.canonical_url,
            base_sha=CONTEXT.base_sha,
            candidate_sha=CONTEXT.candidate_sha,
            branch=CONTEXT.branch,
            worktree_role=CONTEXT.worktree_role,
            run_id="intermediate-tocttou-run",
            adw_id=None,
            purpose="intermediate-component-tocttou-control",
            required_phases=("BUILD",),
            required_dimensions=("path-confinement",),
        )
        document = {
            "schema_version": "sssf.evidence-manifest.v1",
            "repository": {
                "canonical_url": context.canonical_url,
                "base_sha": context.base_sha,
                "candidate_sha": context.candidate_sha,
                "branch": context.branch,
                "worktree_role": context.worktree_role,
            },
            "run": {
                "run_id": context.run_id,
                "adw_id": None,
                "terminal_outcome": "succeeded",
            },
            "purpose": context.purpose,
            "required_phases": ["BUILD"],
            "required_dimensions": ["path-confinement"],
            "inventory": [
                {
                    "sequence": 0,
                    "path": "nested/payload.txt",
                    "artifact_type": "text",
                    "byte_length": len(outside_bytes),
                    "sha256": hashlib.sha256(outside_bytes).hexdigest(),
                    "producer": "intermediate-race-control",
                    "run_id": context.run_id,
                    "adw_id": None,
                    "phase": "BUILD",
                    "purpose": context.purpose,
                    "terminal_outcome": "succeeded",
                    "evidence_class": "qualifying",
                    "claimed_dimensions": ["path-confinement"],
                }
            ],
        }
        (root / "manifest.json").write_bytes(module.canonical_manifest_bytes(document))

        original_stat = module.os.stat
        original_read = module.os.read
        original_primitive_check = getattr(
            module,
            "_descriptor_primitives_available",
            None,
        )
        swapped = False
        captured_reads: list[bytes] = []

        def stat_then_swap(path, *args, dir_fd=None, follow_symlinks=True, **kwargs):
            observed = original_stat(
                path,
                *args,
                dir_fd=dir_fd,
                follow_symlinks=follow_symlinks,
                **kwargs,
            )
            nonlocal swapped
            if (
                not swapped
                and dir_fd is not None
                and not follow_symlinks
                and str(path) == "nested"
            ):
                # The no-follow check has just observed the genuine directory.
                # Replace the component before the descriptor-relative open.
                swapped = True
                nested.rename(root / "checked-nested")
                nested.symlink_to(outside, target_is_directory=True)
            return observed

        def record_read(descriptor: int, length: int) -> bytes:
            chunk = original_read(descriptor, length)
            captured_reads.append(chunk)
            return chunk

        module.os.stat = stat_then_swap
        module.os.read = record_read
        if original_primitive_check is not None:
            module._descriptor_primitives_available = lambda: True
        try:
            result = module.validate_manifest(root / "manifest.json", root, context)
        finally:
            module.os.stat = original_stat
            module.os.read = original_read
            if original_primitive_check is not None:
                module._descriptor_primitives_available = original_primitive_check

        if not swapped:
            findings.append(
                "intermediate-component-tocttou: boundary was not exercised"
            )
        # The defective variant carries its own Observation enum, so identity
        # comparison across modules would silently never match. Compare values.
        if result.observation.value == Observation.OBSERVED_GOOD.value:
            findings.append(
                "intermediate-component-tocttou: outside-root bytes were accepted"
            )
        if "nested/payload.txt" in result.checked_inventory:
            findings.append(
                "intermediate-component-tocttou: escaped artifact entered checked inventory"
            )
        if outside_bytes in b"".join(captured_reads):
            findings.append(
                "intermediate-component-tocttou: outside-root bytes were read"
            )
    return findings


def intermediate_component_tocttou_controls(errors: list[str]) -> None:
    """Run the intermediate-component control against the production
    implementation, then calibrate it watched-red against the bounded defective
    variant, then bind the calibration to its supplemental evidence file."""
    for finding in intermediate_component_tocttou_control(manifest_module):
        errors.append(finding)

    defective_module, digest = defective_intermediate_variant()
    defective_findings = intermediate_component_tocttou_control(defective_module)
    if not defective_findings:
        errors.append(
            "intermediate-component-tocttou: control stayed green against the "
            "defective variant, so it proves nothing"
        )
        return

    evidence = EVIDENCE_DIR / f"intermediate-component-tocttou-red-{digest[:12]}.txt"
    if not evidence.is_file():
        errors.append(
            "intermediate-component-tocttou: supplemental content-addressed "
            f"evidence is missing: {evidence.name}"
        )
        return
    recorded = evidence.read_text(encoding="utf-8")
    if f"defective_program_sha256: {digest}" not in recorded:
        errors.append(
            "intermediate-component-tocttou: supplemental evidence does not bind "
            f"the exact defective program digest {digest}"
        )
    for finding in defective_findings:
        if finding not in recorded:
            errors.append(
                "intermediate-component-tocttou: supplemental evidence does not "
                f"record observed finding: {finding}"
            )


def run_controls() -> list[str]:
    errors: list[str] = []
    raw = MANIFEST.read_bytes()
    parsed = load_manifest()
    if canonical_manifest_bytes(parsed) != raw:
        errors.append("positive fixture does not round-trip to identical canonical bytes")
    intermediate_directory_symlink_swap_control(errors)
    intermediate_component_tocttou_controls(errors)
    descriptor_path_controls(errors)
    positive = validate_manifest(MANIFEST, FIXTURE, CONTEXT)
    expect(errors, "positive fixture", positive.observation, Observation.OBSERVED_GOOD)
    if positive.checked_inventory != (
        "artifacts/build-result.json",
        "artifacts/session.db",
        "artifacts/test-report.txt",
        "diagnostics/failed-attempt.log",
    ):
        errors.append("positive fixture did not verify the complete offline inventory")

    with tempfile.TemporaryDirectory(prefix="sssf-hd08-controls-") as temp_dir:
        temp = Path(temp_dir)

        def fresh(name: str) -> tuple[Path, dict[str, object]]:
            target = temp / name
            shutil.copytree(FIXTURE, target)
            return target, deepcopy(parsed)

        empty_dir, empty_manifest = fresh("empty-directory")
        (empty_dir / "artifacts/build-result.json").unlink()
        (empty_dir / "artifacts/build-result.json").mkdir()
        write_manifest(empty_dir, empty_manifest)
        expect(errors, "empty directory", validate(empty_dir).observation, Observation.CNO)

        empty_file, _ = fresh("empty-manifest")
        (empty_file / "manifest.json").write_bytes(b"")
        expect(errors, "empty manifest", validate(empty_file).observation, Observation.CNO)

        empty_inventory, empty_inventory_doc = fresh("empty-inventory")
        empty_inventory_doc["inventory"] = []
        write_manifest(empty_inventory, empty_inventory_doc)
        expect(errors, "empty inventory", validate(empty_inventory).observation, Observation.CNO)

        for label, field, value in (
            ("wrong repository", "canonical_url", "https://example.invalid/wrong.git"),
            ("wrong base", "base_sha", "2" * 40),
            ("wrong candidate", "candidate_sha", "3" * 40),
            ("wrong branch", "branch", "fixture/other"),
            ("wrong worktree role", "worktree_role", "archive"),
        ):
            target, document = fresh(label.replace(" ", "-"))
            repository = document["repository"]
            assert isinstance(repository, dict)
            repository[field] = value
            write_manifest(target, document)
            expect(errors, label, validate(target).observation, Observation.OBSERVED_BAD)

        declared_phase, declared_phase_doc = fresh("declared-phase")
        write_manifest(declared_phase, declared_phase_doc)
        declared_phase_result = validate(declared_phase)
        expect(
            errors,
            "declared phase positive control",
            declared_phase_result.observation,
            Observation.OBSERVED_GOOD,
        )

        wrong_phase, wrong_phase_doc = fresh("wrong-phase")
        inventory = wrong_phase_doc["inventory"]
        assert isinstance(inventory, list)
        qualifying_item = inventory[0]
        assert isinstance(qualifying_item, dict)
        original_item = deepcopy(qualifying_item)
        qualifying_item["phase"] = "UNDECLARED"
        unchanged_item = deepcopy(qualifying_item)
        unchanged_item["phase"] = original_item["phase"]
        if unchanged_item != original_item:
            errors.append("wrong phase control changed fields other than phase")
        write_manifest(wrong_phase, wrong_phase_doc)
        wrong_phase_result = validate(wrong_phase)
        expect(
            errors,
            "wrong phase",
            wrong_phase_result.observation,
            Observation.OBSERVED_BAD,
        )
        phase_reason = (
            "artifacts/build-result.json: phase is not declared in required_phases"
        )
        if wrong_phase_result.issues.count(phase_reason) != 1:
            errors.append(
                "wrong phase: expected exact undeclared-phase reason once, got "
                f"{wrong_phase_result.issues!r}"
            )

        wrong_run, wrong_run_doc = fresh("wrong-run")
        run = wrong_run_doc["run"]
        assert isinstance(run, dict)
        run["run_id"] = "other-run"
        write_manifest(wrong_run, wrong_run_doc)
        expect(errors, "wrong run ID", validate(wrong_run).observation, Observation.OBSERVED_BAD)

        wrong_adw, wrong_adw_doc = fresh("wrong-adw")
        run = wrong_adw_doc["run"]
        assert isinstance(run, dict)
        run["adw_id"] = "other-adw"
        write_manifest(wrong_adw, wrong_adw_doc)
        expect(errors, "wrong ADW ID", validate(wrong_adw).observation, Observation.OBSERVED_BAD)

        failed, failed_doc = fresh("failed-unrelated")
        inventory = failed_doc["inventory"]
        assert isinstance(inventory, list)
        first = inventory[0]
        assert isinstance(first, dict)
        first["run_id"] = "failed-other-run"
        first["terminal_outcome"] = "failed"
        write_manifest(failed, failed_doc)
        expect(
            errors,
            "failed unrelated run",
            validate(failed).observation,
            Observation.OBSERVED_BAD,
        )

        diagnostics, diagnostics_doc = fresh("diagnostic-only")
        inventory = diagnostics_doc["inventory"]
        assert isinstance(inventory, list)
        for item in inventory:
            assert isinstance(item, dict)
            item["evidence_class"] = "diagnostic"
            item["claimed_dimensions"] = []
        write_manifest(diagnostics, diagnostics_doc)
        expect(errors, "diagnostic only", validate(diagnostics).observation, Observation.CNO)

        tampered, _ = fresh("tampered")
        (tampered / "artifacts/test-report.txt").write_text(
            "tampered after manifest creation\n", encoding="utf-8"
        )
        expect(errors, "tampered artifact", validate(tampered).observation, Observation.OBSERVED_BAD)

        missing_phase, missing_phase_doc = fresh("missing-phase")
        inventory = missing_phase_doc["inventory"]
        assert isinstance(inventory, list)
        test_item = inventory[2]
        assert isinstance(test_item, dict)
        test_item["evidence_class"] = "diagnostic"
        test_item["claimed_dimensions"] = []
        write_manifest(missing_phase, missing_phase_doc)
        expect(errors, "absent required phase", validate(missing_phase).observation, Observation.CNO)

        missing_dimension, missing_dimension_doc = fresh("missing-dimension")
        inventory = missing_dimension_doc["inventory"]
        assert isinstance(inventory, list)
        second = inventory[1]
        assert isinstance(second, dict)
        second["claimed_dimensions"] = ["artifact-integrity"]
        write_manifest(missing_dimension, missing_dimension_doc)
        expect(
            errors,
            "absent required dimension",
            validate(missing_dimension).observation,
            Observation.CNO,
        )

        duplicate, duplicate_doc = fresh("duplicate")
        inventory = duplicate_doc["inventory"]
        assert isinstance(inventory, list)
        inventory.insert(1, deepcopy(inventory[0]))
        for index, item in enumerate(inventory):
            assert isinstance(item, dict)
            item["sequence"] = index
        write_manifest(duplicate, duplicate_doc)
        expect(
            errors,
            "duplicate ambiguous entries",
            validate(duplicate).observation,
            Observation.OBSERVED_BAD,
        )

        reordered, reordered_doc = fresh("reordered")
        inventory = reordered_doc["inventory"]
        assert isinstance(inventory, list)
        inventory[0], inventory[1] = inventory[1], inventory[0]
        write_manifest(reordered, reordered_doc)
        expect(
            errors,
            "identity-preserving reorder",
            validate(reordered).observation,
            Observation.OBSERVED_BAD,
        )

        traversal, traversal_doc = fresh("traversal")
        inventory = traversal_doc["inventory"]
        assert isinstance(inventory, list)
        first = inventory[0]
        assert isinstance(first, dict)
        first["path"] = "../escape.json"
        write_manifest(traversal, traversal_doc)
        expect(errors, "path traversal", validate(traversal).observation, Observation.OBSERVED_BAD)

        symlink, symlink_doc = fresh("symlink")
        source = symlink / "artifacts/build-result.json"
        source.unlink()
        source.symlink_to("test-report.txt")
        inventory = symlink_doc["inventory"]
        assert isinstance(inventory, list)
        first = inventory[0]
        assert isinstance(first, dict)
        first["artifact_type"] = "text"
        set_artifact(first, source)
        write_manifest(symlink, symlink_doc)
        expect(errors, "symlink path escape", validate(symlink).observation, Observation.OBSERVED_BAD)

        malformed, _ = fresh("malformed")
        (malformed / "manifest.json").write_text("{not json}\n", encoding="utf-8")
        expect(errors, "malformed schema", validate(malformed).observation, Observation.OBSERVED_BAD)

        duplicate_key, _ = fresh("duplicate-key")
        (duplicate_key / "manifest.json").write_text(
            '{"schema_version":"sssf.evidence-manifest.v1",'
            '"schema_version":"sssf.evidence-manifest.v1"}\n',
            encoding="utf-8",
        )
        expect(
            errors,
            "duplicate JSON key",
            validate(duplicate_key).observation,
            Observation.OBSERVED_BAD,
        )

        unknown, unknown_doc = fresh("unknown-version")
        unknown_doc["schema_version"] = "sssf.evidence-manifest.v99"
        write_manifest(unknown, unknown_doc)
        expect(errors, "unknown schema", validate(unknown).observation, Observation.CNO)

        noncanonical, noncanonical_doc = fresh("noncanonical")
        (noncanonical / "manifest.json").write_text(
            json.dumps(noncanonical_doc, indent=2) + "\n", encoding="utf-8"
        )
        expect(
            errors,
            "noncanonical manifest bytes",
            validate(noncanonical).observation,
            Observation.OBSERVED_BAD,
        )

        wrong_db, wrong_db_doc = fresh("wrong-database-adw")
        db_path = wrong_db / "artifacts/session.db"
        connection = sqlite3.connect(db_path)
        connection.execute("UPDATE sessions SET adw_id = 'other-adw'")
        connection.commit()
        connection.close()
        inventory = wrong_db_doc["inventory"]
        assert isinstance(inventory, list)
        session_item = inventory[1]
        assert isinstance(session_item, dict)
        set_artifact(session_item, db_path)
        write_manifest(wrong_db, wrong_db_doc)
        expect(
            errors,
            "database row for wrong ADW",
            validate(wrong_db).observation,
            Observation.CNO,
        )

        empty_db, empty_db_doc = fresh("empty-db")
        db_path = empty_db / "artifacts/build-result.json"
        db_path.unlink()
        connection = sqlite3.connect(db_path)
        connection.execute("CREATE TABLE sessions (run_id TEXT)")
        connection.commit()
        connection.close()
        inventory = empty_db_doc["inventory"]
        assert isinstance(inventory, list)
        first = inventory[0]
        assert isinstance(first, dict)
        first["artifact_type"] = "sqlite3"
        set_artifact(first, db_path)
        write_manifest(empty_db, empty_db_doc)
        expect(errors, "empty database", validate(empty_db).observation, Observation.CNO)

    return errors


def main() -> int:
    errors = run_controls()
    if errors:
        print("HD-08 evidence manifest controls: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("HD-08 evidence manifest controls: PASS")
    print("positive fixture round-trips canonical bytes and verifies every hash offline")
    print("watched-red identity, emptiness, diagnostic, tamper, duplicate, and path controls observed")
    print("wrong-phase-control: PASS")
    print("intermediate-directory-symlink-swap: PASS")
    print("intermediate-component-tocttou-control: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
