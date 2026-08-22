from __future__ import annotations

import argparse
from dataclasses import dataclass
import errno
from enum import Enum
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import stat
import sys
import tempfile
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = "sssf.evidence-manifest.v1"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,255}$")
WORKTREE_ROLES = frozenset({"contribution", "proof-clone", "runtime", "archive"})
TERMINAL_OUTCOMES = frozenset({"succeeded", "failed", "cancelled", "cno"})
EVIDENCE_CLASSES = frozenset({"qualifying", "diagnostic"})
ARTIFACT_TYPES = frozenset({"binary", "json", "jsonl", "sqlite3", "text"})

# A manifest names artifacts a run produced, so both the bytes it reads and the
# directory chain it walks to reach them are attacker- and accident-reachable
# growth. Neither is truncated: exceeding either ceiling is a typed refusal,
# because a partially-read artifact must never digest as a whole one.
# BOUNDEDNESS-OWNER: sssf.evidence.artifact_read_bytes
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024
# BOUNDEDNESS-OWNER: sssf.evidence.artifact_path_depth
MAX_ARTIFACT_PATH_DEPTH = 64

# This executable module is the only schema/serialization/validation owner.
# The schema command emits this projection for tooling and documentation.
EVIDENCE_MANIFEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory/blob/main/tools/evidence_manifest.py#sssf.evidence-manifest.v1",
    "title": "SSSF offline run-bound evidence manifest v1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema_version",
        "repository",
        "run",
        "purpose",
        "required_phases",
        "required_dimensions",
        "inventory",
    ],
    "properties": {
        "schema_version": {"const": SCHEMA_VERSION},
        "repository": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "canonical_url",
                "base_sha",
                "candidate_sha",
                "branch",
                "worktree_role",
            ],
            "properties": {
                "canonical_url": {"type": "string", "minLength": 1},
                "base_sha": {"type": "string", "pattern": SHA1_RE.pattern},
                "candidate_sha": {"type": "string", "pattern": SHA1_RE.pattern},
                "branch": {"type": "string", "minLength": 1},
                "worktree_role": {"enum": sorted(WORKTREE_ROLES)},
            },
        },
        "run": {
            "type": "object",
            "additionalProperties": False,
            "required": ["run_id", "adw_id", "terminal_outcome"],
            "properties": {
                "run_id": {"type": "string", "minLength": 1},
                "adw_id": {"type": ["string", "null"]},
                "terminal_outcome": {"enum": sorted(TERMINAL_OUTCOMES)},
            },
        },
        "purpose": {"type": "string", "minLength": 1},
        "required_phases": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "required_dimensions": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
        "inventory": {
            "type": "array",
            "minItems": 1,
            "items": {"$ref": "#/$defs/inventory_item"},
        },
    },
    "$defs": {
        "inventory_item": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "sequence",
                "path",
                "artifact_type",
                "byte_length",
                "sha256",
                "producer",
                "run_id",
                "adw_id",
                "phase",
                "purpose",
                "terminal_outcome",
                "evidence_class",
                "claimed_dimensions",
            ],
            "properties": {
                "sequence": {"type": "integer", "minimum": 0},
                "path": {"type": "string", "minLength": 1},
                "artifact_type": {"enum": sorted(ARTIFACT_TYPES)},
                "byte_length": {"type": "integer", "minimum": 1},
                "sha256": {"type": "string", "pattern": SHA256_RE.pattern},
                "producer": {"type": "string", "minLength": 1},
                "run_id": {"type": "string", "minLength": 1},
                "adw_id": {"type": ["string", "null"]},
                "phase": {"type": "string", "minLength": 1},
                "purpose": {"type": "string", "minLength": 1},
                "terminal_outcome": {"enum": sorted(TERMINAL_OUTCOMES)},
                "evidence_class": {"enum": sorted(EVIDENCE_CLASSES)},
                "claimed_dimensions": {
                    "type": "array",
                    "uniqueItems": True,
                    "items": {"type": "string", "minLength": 1},
                },
            },
        }
    },
}


class Observation(str, Enum):
    OBSERVED_GOOD = "observed-good"
    OBSERVED_BAD = "observed-bad"
    CNO = "could-not-observe"


@dataclass(frozen=True)
class ValidationContext:
    canonical_url: str
    base_sha: str
    candidate_sha: str
    branch: str
    worktree_role: str
    run_id: str
    adw_id: str | None
    purpose: str
    required_phases: tuple[str, ...]
    required_dimensions: tuple[str, ...]


@dataclass(frozen=True)
class ValidatedInventoryItem:
    path: str
    artifact_type: str
    byte_length: int
    sha256: str
    producer: str
    run_id: str


@dataclass(frozen=True)
class ValidationResult:
    observation: Observation
    issues: tuple[str, ...]
    checked_inventory: tuple[str, ...] = ()
    validated_inventory: tuple[ValidatedInventoryItem, ...] = ()

    @property
    def is_qualifying(self) -> bool:
        return self.observation is Observation.OBSERVED_GOOD


class DuplicateKeyError(ValueError):
    pass


class ArtifactRefusal(Exception):
    def __init__(self, observation: Observation, message: str) -> None:
        super().__init__(message)
        self.observation = observation


def canonical_json_bytes(value: Any) -> bytes:
    """Return the sole canonical JSON encoding: sorted UTF-8 keys plus LF."""
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def canonical_manifest_bytes(manifest: Mapping[str, Any]) -> bytes:
    """Serialize a manifest. Shape and evidence validation remain explicit."""
    return canonical_json_bytes(manifest)


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _parse_json(raw: bytes) -> Any:
    text = raw.decode("utf-8")
    return json.loads(text, object_pairs_hook=_object_without_duplicate_keys)


def _is_plain_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _token(value: Any, label: str, errors: list[str], *, nullable: bool = False) -> bool:
    if nullable and value is None:
        return True
    if not isinstance(value, str) or TOKEN_RE.fullmatch(value) is None:
        errors.append(f"{label} must be a nonempty bounded identity token")
        return False
    return True


def _exact_keys(value: Any, expected: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        errors.append(f"{label} keys mismatch (missing={missing}, extra={extra})")
        return False
    return True


def _sorted_unique_tokens(value: Any, label: str, errors: list[str], *, nonempty: bool) -> bool:
    if not isinstance(value, list):
        errors.append(f"{label} must be an array")
        return False
    if nonempty and not value:
        errors.append(f"{label} must be nonempty")
        return False
    valid = True
    for index, item in enumerate(value):
        valid = _token(item, f"{label}[{index}]", errors) and valid
    if valid and value != sorted(set(value)):
        errors.append(f"{label} must be sorted and duplicate-free")
        valid = False
    return valid


def _valid_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and value == path.as_posix()
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _validate_shape(manifest: Any) -> list[str]:
    errors: list[str] = []
    top_keys = {
        "schema_version",
        "repository",
        "run",
        "purpose",
        "required_phases",
        "required_dimensions",
        "inventory",
    }
    if not _exact_keys(manifest, top_keys, "manifest", errors):
        return errors

    if manifest["schema_version"] != SCHEMA_VERSION:
        # Version refusal is classified before shape validation by validate_manifest.
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")

    repository = manifest["repository"]
    repository_keys = {
        "canonical_url",
        "base_sha",
        "candidate_sha",
        "branch",
        "worktree_role",
    }
    if _exact_keys(repository, repository_keys, "repository", errors):
        canonical_url = repository["canonical_url"]
        if not isinstance(canonical_url, str) or not canonical_url.startswith("https://"):
            errors.append("repository.canonical_url must be a nonempty HTTPS URL")
        for name in ("base_sha", "candidate_sha"):
            if not isinstance(repository[name], str) or SHA1_RE.fullmatch(repository[name]) is None:
                errors.append(f"repository.{name} must be a lowercase 40-character Git SHA")
        _token(repository["branch"], "repository.branch", errors)
        if repository["worktree_role"] not in WORKTREE_ROLES:
            errors.append("repository.worktree_role is unsupported")

    run = manifest["run"]
    if _exact_keys(run, {"run_id", "adw_id", "terminal_outcome"}, "run", errors):
        _token(run["run_id"], "run.run_id", errors)
        _token(run["adw_id"], "run.adw_id", errors, nullable=True)
        if run["terminal_outcome"] not in TERMINAL_OUTCOMES:
            errors.append("run.terminal_outcome is unsupported")

    _token(manifest["purpose"], "purpose", errors)
    _sorted_unique_tokens(manifest["required_phases"], "required_phases", errors, nonempty=True)
    _sorted_unique_tokens(
        manifest["required_dimensions"], "required_dimensions", errors, nonempty=True
    )

    inventory = manifest["inventory"]
    if not isinstance(inventory, list):
        errors.append("inventory must be an array")
        return errors
    if not inventory:
        errors.append("inventory must be nonempty")
        return errors

    item_keys = {
        "sequence",
        "path",
        "artifact_type",
        "byte_length",
        "sha256",
        "producer",
        "run_id",
        "adw_id",
        "phase",
        "purpose",
        "terminal_outcome",
        "evidence_class",
        "claimed_dimensions",
    }
    paths: list[str] = []
    for index, item in enumerate(inventory):
        label = f"inventory[{index}]"
        if not _exact_keys(item, item_keys, label, errors):
            continue
        if not _is_plain_int(item["sequence"]) or item["sequence"] != index:
            errors.append(f"{label}.sequence must equal its zero-based canonical position")
        if not _valid_relative_path(item["path"]):
            errors.append(f"{label}.path must be a normalized relative POSIX path")
        else:
            paths.append(item["path"])
        if item["artifact_type"] not in ARTIFACT_TYPES:
            errors.append(f"{label}.artifact_type is unsupported")
        if not _is_plain_int(item["byte_length"]) or item["byte_length"] < 1:
            errors.append(f"{label}.byte_length must be a positive integer")
        if not isinstance(item["sha256"], str) or SHA256_RE.fullmatch(item["sha256"]) is None:
            errors.append(f"{label}.sha256 must be lowercase SHA-256 hex")
        for field in ("producer", "run_id", "phase", "purpose"):
            _token(item[field], f"{label}.{field}", errors)
        _token(item["adw_id"], f"{label}.adw_id", errors, nullable=True)
        if item["terminal_outcome"] not in TERMINAL_OUTCOMES:
            errors.append(f"{label}.terminal_outcome is unsupported")
        if item["evidence_class"] not in EVIDENCE_CLASSES:
            errors.append(f"{label}.evidence_class is unsupported")
        dimensions_valid = _sorted_unique_tokens(
            item["claimed_dimensions"],
            f"{label}.claimed_dimensions",
            errors,
            nonempty=item["evidence_class"] == "qualifying",
        )
        if dimensions_valid and item["evidence_class"] == "diagnostic" and item["claimed_dimensions"]:
            errors.append(f"{label}: diagnostic evidence cannot claim acceptance dimensions")

    if paths and paths != sorted(paths):
        errors.append("inventory must be ordered by path; identity-preserving reorder is refused")
    if len(paths) != len(set(paths)):
        errors.append("inventory contains duplicate artifact paths")
    return errors


def _descriptor_primitives_available() -> bool:
    return (
        hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
    )


def _opened_identity(metadata: os.stat_result) -> tuple[int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        metadata.st_nlink,
    )


def _changed_identity(
    before: os.stat_result,
    after: os.stat_result,
) -> bool:
    return _opened_identity(before) != _opened_identity(after)


def _path_open_error(
    exc: OSError,
    *,
    relative: str,
    component: str,
) -> ArtifactRefusal:
    if exc.errno == errno.ELOOP:
        return ArtifactRefusal(
            Observation.OBSERVED_BAD,
            f"symlink artifact/path component refused: {relative}",
        )
    return ArtifactRefusal(
        Observation.CNO,
        f"artifact component is unavailable: {relative}: {component}: {exc}",
    )


def _read_frozen_artifact(root: Path, relative: str) -> bytes:
    if not _descriptor_primitives_available():
        raise ArtifactRefusal(
            Observation.CNO,
            "host lacks descriptor-relative no-follow artifact primitives",
        )
    try:
        root_before = root.lstat()
    except (FileNotFoundError, PermissionError, OSError) as exc:
        raise ArtifactRefusal(
            Observation.CNO,
            f"artifact root is unavailable: {exc}",
        ) from exc
    if stat.S_ISLNK(root_before.st_mode):
        raise ArtifactRefusal(
            Observation.OBSERVED_BAD,
            "artifact root is a symlink",
        )
    if not stat.S_ISDIR(root_before.st_mode):
        raise ArtifactRefusal(
            Observation.CNO,
            "artifact root is not a directory",
        )

    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC

    descriptors: list[int] = []
    try:
        try:
            root_descriptor = os.open(root, directory_flags)
        except OSError as exc:
            if root.is_symlink():
                raise ArtifactRefusal(
                    Observation.OBSERVED_BAD,
                    "artifact root became a symlink",
                ) from exc
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact root could not be opened safely: {exc}",
            ) from exc
        descriptors.append(root_descriptor)
        root_after = os.fstat(root_descriptor)
        if not stat.S_ISDIR(root_after.st_mode):
            raise ArtifactRefusal(
                Observation.CNO,
                "opened artifact root is not a directory",
            )
        if _changed_identity(root_before, root_after):
            raise ArtifactRefusal(
                Observation.CNO,
                "artifact root identity changed while being opened",
            )

        current_descriptor = root_descriptor
        parts = PurePosixPath(relative).parts
        if len(parts) > MAX_ARTIFACT_PATH_DEPTH:
            raise ArtifactRefusal(
                Observation.OBSERVED_BAD,
                f"artifact path depth exceeds {MAX_ARTIFACT_PATH_DEPTH}: {relative}",
            )
        for component in parts[:-1]:
            try:
                before = os.stat(
                    component,
                    dir_fd=current_descriptor,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise _path_open_error(
                    exc,
                    relative=relative,
                    component=component,
                ) from exc
            if stat.S_ISLNK(before.st_mode):
                raise ArtifactRefusal(
                    Observation.OBSERVED_BAD,
                    f"symlink artifact/path component refused: {relative}",
                )
            if not stat.S_ISDIR(before.st_mode):
                raise ArtifactRefusal(
                    Observation.CNO,
                    f"artifact path component is not a directory: {relative}",
                )
            try:
                next_descriptor = os.open(
                    component,
                    directory_flags,
                    dir_fd=current_descriptor,
                )
            except OSError as exc:
                raise _path_open_error(
                    exc,
                    relative=relative,
                    component=component,
                ) from exc
            descriptors.append(next_descriptor)
            after = os.fstat(next_descriptor)
            if not stat.S_ISDIR(after.st_mode) or _changed_identity(before, after):
                raise ArtifactRefusal(
                    Observation.CNO,
                    f"artifact directory identity changed while being opened: {relative}",
                )
            current_descriptor = next_descriptor

        final_component = parts[-1]
        try:
            path_before = os.stat(
                final_component,
                dir_fd=current_descriptor,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise _path_open_error(
                exc,
                relative=relative,
                component=final_component,
            ) from exc
        if stat.S_ISLNK(path_before.st_mode):
            raise ArtifactRefusal(
                Observation.OBSERVED_BAD,
                f"symlink artifact refused: {relative}",
            )
        if not stat.S_ISREG(path_before.st_mode):
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact is not a regular file: {relative}",
            )
        if path_before.st_nlink != 1:
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact link count is not exactly one: {relative}",
            )
        try:
            artifact_descriptor = os.open(
                final_component,
                file_flags,
                dir_fd=current_descriptor,
            )
        except OSError as exc:
            raise _path_open_error(
                exc,
                relative=relative,
                component=final_component,
            ) from exc
        descriptors.append(artifact_descriptor)
        opened = os.fstat(artifact_descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or _changed_identity(path_before, opened)
        ):
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact identity changed while being opened: {relative}",
            )

        chunks: list[bytes] = []
        read_bytes = 0
        try:
            while True:
                chunk = os.read(artifact_descriptor, 1024 * 1024)
                if not chunk:
                    break
                read_bytes += len(chunk)
                if read_bytes > MAX_ARTIFACT_BYTES:
                    # REJECT, not truncate: a digest over a prefix would claim
                    # to identify an artifact it never finished reading.
                    raise ArtifactRefusal(
                        Observation.OBSERVED_BAD,
                        f"artifact exceeds the {MAX_ARTIFACT_BYTES} byte read ceiling: {relative}",
                    )
                chunks.append(chunk)
            after_read = os.fstat(artifact_descriptor)
        except OSError as exc:
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact read failed: {relative}: {exc}",
            ) from exc
        complete_before = (
            opened.st_dev,
            opened.st_ino,
            stat.S_IFMT(opened.st_mode),
            opened.st_nlink,
            opened.st_size,
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        )
        complete_after = (
            after_read.st_dev,
            after_read.st_ino,
            stat.S_IFMT(after_read.st_mode),
            after_read.st_nlink,
            after_read.st_size,
            after_read.st_mtime_ns,
            after_read.st_ctime_ns,
        )
        if complete_before != complete_after:
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact changed while being frozen: {relative}",
            )
        raw = b"".join(chunks)
        if not raw:
            raise ArtifactRefusal(
                Observation.CNO,
                f"artifact is empty: {relative}",
            )
        return raw
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _quote_sqlite_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _validate_sqlite_snapshot(
    raw: bytes,
    *,
    qualifying: bool,
    label: str,
    run_id: str,
    adw_id: str | None,
) -> None:
    with tempfile.TemporaryDirectory(prefix="sssf-manifest-sqlite-") as temp_dir:
        snapshot = Path(temp_dir) / "artifact.db"
        snapshot.write_bytes(raw)
        try:
            connection = sqlite3.connect(
                snapshot.as_uri() + "?mode=ro&immutable=1", uri=True, timeout=1.0
            )
            connection.execute("PRAGMA query_only=ON")
            integrity = connection.execute("PRAGMA quick_check").fetchone()
            if integrity != ("ok",):
                raise ArtifactRefusal(Observation.OBSERVED_BAD, f"malformed SQLite artifact: {label}")
            tables = [
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            has_rows = any(
                connection.execute(
                    f"SELECT 1 FROM {_quote_sqlite_identifier(table)} LIMIT 1"
                ).fetchone()
                is not None
                for table in tables
            )
            identity_column = "adw_id" if adw_id is not None else "run_id"
            identity_value = adw_id if adw_id is not None else run_id
            identity_row_found = False
            for table in tables:
                columns = {
                    row[1]
                    for row in connection.execute(
                        f"PRAGMA table_info({_quote_sqlite_identifier(table)})"
                    )
                }
                if identity_column not in columns:
                    continue
                row = connection.execute(
                    f"SELECT 1 FROM {_quote_sqlite_identifier(table)} "
                    f"WHERE {_quote_sqlite_identifier(identity_column)} = ? LIMIT 1",
                    (identity_value,),
                ).fetchone()
                if row is not None:
                    identity_row_found = True
                    break
        except sqlite3.Error as exc:
            raise ArtifactRefusal(
                Observation.OBSERVED_BAD, f"malformed SQLite artifact: {label}: {exc}"
            ) from exc
        finally:
            if "connection" in locals():
                connection.close()
    if qualifying and not has_rows:
        raise ArtifactRefusal(
            Observation.CNO,
            f"qualifying SQLite artifact has no rows in user tables: {label}",
        )
    if qualifying and not identity_row_found:
        raise ArtifactRefusal(
            Observation.CNO,
            f"qualifying SQLite artifact has no bound {identity_column} row: {label}",
        )


def _parse_frozen_artifact(
    raw: bytes,
    artifact_type: str,
    *,
    qualifying: bool,
    label: str,
    run_id: str,
    adw_id: str | None,
) -> None:
    # Hash/length checks happen before this function. Parsing never reopens the source.
    try:
        if artifact_type == "json":
            _parse_json(raw)
        elif artifact_type == "jsonl":
            lines = raw.splitlines()
            if not lines:
                raise ValueError("no JSONL records")
            for line in lines:
                if not line.strip():
                    raise ValueError("blank JSONL record")
                _parse_json(line)
        elif artifact_type == "text":
            raw.decode("utf-8")
        elif artifact_type == "sqlite3":
            _validate_sqlite_snapshot(
                raw,
                qualifying=qualifying,
                label=label,
                run_id=run_id,
                adw_id=adw_id,
            )
    except ArtifactRefusal:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        raise ArtifactRefusal(
            Observation.OBSERVED_BAD, f"malformed {artifact_type} artifact: {label}: {exc}"
        ) from exc


def _context_mismatches(manifest: dict[str, Any], context: ValidationContext) -> list[str]:
    repository = manifest["repository"]
    run = manifest["run"]
    expected = {
        "repository.canonical_url": (repository["canonical_url"], context.canonical_url),
        "repository.base_sha": (repository["base_sha"], context.base_sha),
        "repository.candidate_sha": (repository["candidate_sha"], context.candidate_sha),
        "repository.branch": (repository["branch"], context.branch),
        "repository.worktree_role": (repository["worktree_role"], context.worktree_role),
        "run.run_id": (run["run_id"], context.run_id),
        "run.adw_id": (run["adw_id"], context.adw_id),
        "purpose": (manifest["purpose"], context.purpose),
    }
    mismatches = [
        f"{label} does not match the validation context"
        for label, (actual, wanted) in expected.items()
        if actual != wanted
    ]
    if tuple(manifest["required_phases"]) != tuple(sorted(set(context.required_phases))):
        mismatches.append("required_phases do not match the validation context")
    if tuple(manifest["required_dimensions"]) != tuple(
        sorted(set(context.required_dimensions))
    ):
        mismatches.append("required_dimensions do not match the validation context")
    return mismatches


def validate_manifest(
    manifest_path: Path,
    artifact_root: Path,
    context: ValidationContext,
) -> ValidationResult:
    bad: list[str] = []
    cno: list[str] = []
    checked: list[str] = []
    validated: list[ValidatedInventoryItem] = []

    try:
        raw_manifest = manifest_path.read_bytes()
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return ValidationResult(Observation.CNO, (f"manifest is unreadable: {exc}",))
    if not raw_manifest:
        return ValidationResult(Observation.CNO, ("manifest is empty",))

    try:
        parsed = _parse_json(raw_manifest)
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        return ValidationResult(Observation.OBSERVED_BAD, (f"manifest is malformed: {exc}",))
    if not isinstance(parsed, dict):
        return ValidationResult(Observation.OBSERVED_BAD, ("manifest root must be an object",))
    if parsed.get("schema_version") != SCHEMA_VERSION:
        return ValidationResult(
            Observation.CNO,
            ("unknown schema version; v1 performs no implicit migration",),
        )
    empty_required = [
        name
        for name in ("required_phases", "required_dimensions", "inventory")
        if isinstance(parsed.get(name), list) and not parsed[name]
    ]
    if empty_required:
        return ValidationResult(
            Observation.CNO,
            (f"required evidence declarations are empty: {empty_required}",),
        )

    shape_errors = _validate_shape(parsed)
    if shape_errors:
        return ValidationResult(Observation.OBSERVED_BAD, tuple(shape_errors))
    try:
        canonical = canonical_manifest_bytes(parsed)
    except (TypeError, ValueError) as exc:
        return ValidationResult(Observation.OBSERVED_BAD, (f"manifest cannot be serialized: {exc}",))
    if raw_manifest != canonical:
        return ValidationResult(
            Observation.OBSERVED_BAD,
            ("manifest bytes are not the canonical sorted-key UTF-8 encoding",),
        )

    bad.extend(_context_mismatches(parsed, context))
    run = parsed["run"]
    required_phases = set(parsed["required_phases"])
    required_dimensions = set(parsed["required_dimensions"])
    qualifying_phases: set[str] = set()
    qualifying_dimensions: set[str] = set()

    if run["terminal_outcome"] != "succeeded":
        bad.append("a qualifying manifest requires run.terminal_outcome=succeeded")

    for item in parsed["inventory"]:
        path = item["path"]
        qualifying = item["evidence_class"] == "qualifying"
        if item["run_id"] != run["run_id"]:
            bad.append(f"{path}: run_id does not bind to the manifest run")
        if item["adw_id"] != run["adw_id"]:
            bad.append(f"{path}: adw_id does not bind to the manifest run")
        if item["purpose"] != parsed["purpose"]:
            bad.append(f"{path}: purpose does not bind to the manifest purpose")
        if item["phase"] not in required_phases:
            bad.append(f"{path}: phase is not declared in required_phases")
        claimed = set(item["claimed_dimensions"])
        if not claimed.issubset(required_dimensions):
            bad.append(f"{path}: claims an undeclared acceptance dimension")
        qualifying_identity_ok = (
            qualifying
            and item["terminal_outcome"] == "succeeded"
            and item["run_id"] == run["run_id"]
            and item["adw_id"] == run["adw_id"]
            and item["purpose"] == parsed["purpose"]
            and item["phase"] in required_phases
            and claimed.issubset(required_dimensions)
        )
        if qualifying and item["terminal_outcome"] != "succeeded":
            bad.append(f"{path}: failed/CNO artifact cannot be qualifying evidence")

        try:
            frozen = _read_frozen_artifact(artifact_root, path)
            digest = hashlib.sha256(frozen).hexdigest()
            if len(frozen) != item["byte_length"]:
                bad.append(f"{path}: byte_length mismatch")
            if digest != item["sha256"]:
                bad.append(f"{path}: SHA-256 mismatch/tamper observed")
            if len(frozen) == item["byte_length"] and digest == item["sha256"]:
                _parse_frozen_artifact(
                    frozen,
                    item["artifact_type"],
                    qualifying=qualifying,
                    label=path,
                    run_id=item["run_id"],
                    adw_id=item["adw_id"],
                )
                checked.append(path)
                validated.append(
                    ValidatedInventoryItem(
                        path=path,
                        artifact_type=item["artifact_type"],
                        byte_length=item["byte_length"],
                        sha256=item["sha256"],
                        producer=item["producer"],
                        run_id=item["run_id"],
                    )
                )
                if qualifying_identity_ok:
                    qualifying_phases.add(item["phase"])
                    qualifying_dimensions.update(claimed)
        except ArtifactRefusal as exc:
            if exc.observation is Observation.OBSERVED_BAD:
                bad.append(str(exc))
            else:
                cno.append(str(exc))

    missing_phases = sorted(required_phases - qualifying_phases)
    missing_dimensions = sorted(required_dimensions - qualifying_dimensions)
    if missing_phases:
        cno.append(f"no qualifying item for required phases: {missing_phases}")
    if missing_dimensions:
        cno.append(f"no qualifying item for required dimensions: {missing_dimensions}")
    if not checked:
        cno.append("checked inventory is empty")

    if bad:
        return ValidationResult(Observation.OBSERVED_BAD, tuple(bad + cno), tuple(checked), tuple(validated))
    if cno:
        return ValidationResult(Observation.CNO, tuple(cno), tuple(checked), tuple(validated))
    return ValidationResult(Observation.OBSERVED_GOOD, (), tuple(checked), tuple(validated))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Serialize/schema-check and validate offline SSSF evidence manifests."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("schema", help="Print the canonical v1 JSON Schema projection.")
    validate = subparsers.add_parser("validate", help="Validate a manifest and frozen artifacts.")
    validate.add_argument("--manifest", type=Path, required=True)
    validate.add_argument("--artifact-root", type=Path, required=True)
    validate.add_argument("--repository", required=True)
    validate.add_argument("--base-sha", required=True)
    validate.add_argument("--candidate-sha", required=True)
    validate.add_argument("--branch", required=True)
    validate.add_argument("--worktree-role", choices=sorted(WORKTREE_ROLES), required=True)
    validate.add_argument("--run-id", required=True)
    validate.add_argument("--adw-id")
    validate.add_argument("--purpose", required=True)
    validate.add_argument("--require-phase", action="append", required=True)
    validate.add_argument("--require-dimension", action="append", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "schema":
        sys.stdout.buffer.write(canonical_json_bytes(EVIDENCE_MANIFEST_SCHEMA))
        return 0

    context = ValidationContext(
        canonical_url=args.repository,
        base_sha=args.base_sha,
        candidate_sha=args.candidate_sha,
        branch=args.branch,
        worktree_role=args.worktree_role,
        run_id=args.run_id,
        adw_id=args.adw_id,
        purpose=args.purpose,
        required_phases=tuple(args.require_phase),
        required_dimensions=tuple(args.require_dimension),
    )
    result = validate_manifest(args.manifest, args.artifact_root, context)
    print(f"evidence-manifest: {result.observation.value}")
    print(f"checked-inventory: {len(result.checked_inventory)}")
    for path in result.checked_inventory:
        print(f"checked: {path}")
    for issue in result.issues:
        print(f"- {issue}")
    if result.observation is Observation.OBSERVED_GOOD:
        return 0
    if result.observation is Observation.OBSERVED_BAD:
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
