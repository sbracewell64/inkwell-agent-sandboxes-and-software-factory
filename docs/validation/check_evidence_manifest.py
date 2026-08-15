from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))

from evidence_manifest import (  # noqa: E402
    Observation,
    ValidationContext,
    canonical_manifest_bytes,
    validate_manifest,
)

FIXTURE = ROOT / "docs/validation/fixtures/evidence_manifest/positive"
MANIFEST = FIXTURE / "manifest.json"
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


def run_controls() -> list[str]:
    errors: list[str] = []
    raw = MANIFEST.read_bytes()
    parsed = load_manifest()
    if canonical_manifest_bytes(parsed) != raw:
        errors.append("positive fixture does not round-trip to identical canonical bytes")
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
