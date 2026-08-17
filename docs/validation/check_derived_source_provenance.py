"""HD-15 preventive exact-provenance contract for any future derived SSSF source.

This validator is a gate, not a door. It authorises no migration and creates no
import path. It exists so that if assessment-derived source ever enters this
repository, the exact input that produced it is bound to immutable Git objects
and verified against bytes before the change can go green.

Two standing laws are enforced here directly.

Absence is not a pass. When the enumerated universe holds no derived source,
the population verdict is ``NOT_APPLICABLE`` -- a form of could-not-observe --
and is never printed, ranked, or documented as ``PASS``. A reader must be able
to tell "we checked and there is none" (``NOT_APPLICABLE``) from "we did not
look" (``CANNOT_OBSERVE``) from "there is derived source and it complies"
(``PASS``).

Discovery is not identity. A branch name, a tag name, a path that looks like an
input, or a commit message that mentions one identifies a candidate and
establishes nothing. Only an exact commit, tree, and content hash resolved
against an immutable input binds a claim, so name-shaped provenance is refused
even when the name happens to resolve to the correct object.

Precedence is FAIL > CANNOT_OBSERVE > NOT_APPLICABLE > PASS. An incomplete
universe never masks a real violation, and an empty universe never becomes a
certification.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]

SCHEMA_VERSION = "sssf.derived-source-provenance.v1"
REQUIRED_CAVEAT = "OVERALL_B3_NOT_COMPLETE"

RECORDS_DIR = "docs/provenance/derived_source"
RECORDS_README = f"{RECORDS_DIR}/README.md"
CONTRACT_DOC = "docs/reference/DERIVED_SOURCE_PROVENANCE.md"
INCREMENT_DOC = "docs/increments/HD-15_DERIVED_SOURCE_PROVENANCE.md"

# The marker is assembled from halves so this validator's own source does not
# contain the literal token it searches for. Only the documents that must teach
# the token are allowed to carry it.
MARKER = "SSSF-DERIVED" "-SOURCE"
MARKER_BYTES = MARKER.encode("ascii")
MARKER_DOC_PATHS = (CONTRACT_DOC, INCREMENT_DOC)

SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RECORD_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
PLACEHOLDER_RE = re.compile(r"[<>]")
PLACEHOLDER_WORDS = frozenset({"", "tbd", "todo", "unknown", "n/a", "none", "-"})

EXTRACTION_METHODS = frozenset({"verbatim-copy", "transcribed", "adapted"})

TEMPLATE_FENCE = "```json"

_DETERMINISTIC_ENV = {
    "GIT_AUTHOR_NAME": "SSSF Calibration",
    "GIT_AUTHOR_EMAIL": "calibration@sssf.invalid",
    "GIT_AUTHOR_DATE": "1700000000 +0000",
    "GIT_COMMITTER_NAME": "SSSF Calibration",
    "GIT_COMMITTER_EMAIL": "calibration@sssf.invalid",
    "GIT_COMMITTER_DATE": "1700000000 +0000",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_TERMINAL_PROMPT": "0",
    "GIT_ATTR_NOSYSTEM": "1",
}


class Verdict(str, Enum):
    """The population verdict. Never collapse these to a Boolean."""

    FAIL = "FAIL"
    CANNOT_OBSERVE = "CANNOT_OBSERVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PASS = "PASS"


_RANK = {
    Verdict.PASS: 0,
    Verdict.NOT_APPLICABLE: 1,
    Verdict.CANNOT_OBSERVE: 2,
    Verdict.FAIL: 3,
}


def strongest(verdicts: list[Verdict]) -> Verdict:
    """Apply the settled precedence: FAIL > CANNOT_OBSERVE > NOT_APPLICABLE > PASS."""
    return max(verdicts, key=lambda verdict: _RANK[verdict])


class GitUnavailable(Exception):
    """Git could not be executed at all: could-not-observe, never a pass."""


class GitError(Exception):
    """A Git invocation refused. The caller decides bad-versus-CNO."""


def git(repo: Path, *args: str, stdin: bytes | None = None) -> bytes:
    env = dict(os.environ)
    env.update(_DETERMINISTIC_ENV)
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
    except FileNotFoundError as exc:  # pragma: no cover - host without git
        raise GitUnavailable("git executable not found") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip().splitlines()
        raise GitError(f"git {' '.join(args)}: {detail[-1] if detail else 'failed'}")
    return completed.stdout


def git_ok(repo: Path, *args: str) -> bool:
    try:
        git(repo, *args)
    except GitError:
        return False
    return True


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def split_lines(payload: bytes) -> list[bytes]:
    """LF-delimited lines with no phantom trailing entry."""
    lines = payload.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def slice_bytes(payload: bytes, start: int, end: int) -> bytes:
    """The canonical slice: selected lines, each LF-terminated."""
    lines = split_lines(payload)
    return b"".join(line + b"\n" for line in lines[start - 1:end])


def is_placeholder(value: object) -> bool:
    if not isinstance(value, str):
        return True
    stripped = value.strip()
    return bool(PLACEHOLDER_RE.search(stripped)) or stripped.lower() in PLACEHOLDER_WORDS


@dataclass(frozen=True)
class PopulationResult:
    """A three-valued population assessment; ``verdict`` is derived once."""

    verdict: Verdict
    observed_bad: tuple[str, ...] = ()
    could_not_observe: tuple[str, ...] = ()
    records_checked: tuple[str, ...] = ()
    marked_files: tuple[str, ...] = ()
    universe_files: int = 0
    verified_bindings: int = 0

    def __bool__(self) -> bool:  # pragma: no cover - defensive
        raise TypeError("PopulationResult has four values; compare .verdict explicitly")


@dataclass
class _Findings:
    bad: list[str] = field(default_factory=list)
    cno: list[str] = field(default_factory=list)
    bindings: int = 0


# ---------------------------------------------------------------------------
# Record shape
# ---------------------------------------------------------------------------


def _require_mapping(node: object, label: str, findings: _Findings) -> dict | None:
    if not isinstance(node, dict):
        findings.bad.append(f"{label}: must be an object")
        return None
    return node


def _require_hex(
    node: dict, key: str, label: str, pattern: re.Pattern[str], findings: _Findings
) -> str | None:
    value = node.get(key)
    if not isinstance(value, str) or not pattern.match(value):
        width = 40 if pattern is SHA1_RE else 64
        findings.bad.append(
            f"{label}.{key}: exact {width}-character lowercase hex identity is required; "
            f"a branch or tag name is discovery, not identity (observed {value!r})"
        )
        return None
    return value


def _require_prose(node: dict, key: str, label: str, findings: _Findings) -> str | None:
    value = node.get(key)
    if is_placeholder(value):
        findings.bad.append(f"{label}.{key}: unfilled or placeholder value {value!r}")
        return None
    return value  # type: ignore[return-value]


def _require_range(node: object, label: str, findings: _Findings) -> tuple[int, int] | None:
    if (
        not isinstance(node, list)
        or len(node) != 2
        or not all(isinstance(bound, int) and not isinstance(bound, bool) for bound in node)
    ):
        findings.bad.append(f"{label}: must be a two-element [start, end] integer range")
        return None
    start, end = node
    if start < 1 or end < start:
        findings.bad.append(f"{label}: invalid 1-based inclusive range {node!r}")
        return None
    return start, end


def record_shape(record: object, label: str, findings: _Findings) -> dict | None:
    """Structural contract. Every field a later stage verifies must exist here."""
    document = _require_mapping(record, label, findings)
    if document is None:
        return None

    expected_keys = {
        "schema_version",
        "record_id",
        "caveats",
        "input",
        "extraction",
        "license",
        "destination",
        "transformed_files",
    }
    observed_keys = set(document)
    if observed_keys != expected_keys:
        missing = sorted(expected_keys - observed_keys)
        extra = sorted(observed_keys - expected_keys)
        findings.bad.append(f"{label}: key drift (missing={missing}, unexpected={extra})")
        return None

    if document["schema_version"] != SCHEMA_VERSION:
        findings.bad.append(
            f"{label}.schema_version: expected {SCHEMA_VERSION!r}, "
            f"observed {document['schema_version']!r}"
        )
    record_id = document["record_id"]
    if not isinstance(record_id, str) or not RECORD_ID_RE.match(record_id):
        findings.bad.append(f"{label}.record_id: expected a kebab-case slug, observed {record_id!r}")

    caveats = document["caveats"]
    if not isinstance(caveats, list) or not all(isinstance(item, str) for item in caveats):
        findings.bad.append(f"{label}.caveats: must be a list of strings")
    elif REQUIRED_CAVEAT not in caveats:
        findings.bad.append(
            f"{label}.caveats: the {REQUIRED_CAVEAT} could-not-observe caveat must remain visible"
        )

    source = _require_mapping(document["input"], f"{label}.input", findings)
    if source is not None:
        _require_prose(source, "source_repository", f"{label}.input", findings)
        _require_prose(source, "source_path", f"{label}.input", findings)
        _require_hex(source, "commit", f"{label}.input", SHA1_RE, findings)
        _require_hex(source, "tree", f"{label}.input", SHA1_RE, findings)
        _require_hex(source, "blob", f"{label}.input", SHA1_RE, findings)
        _require_hex(source, "content_sha256", f"{label}.input", SHA256_RE, findings)
        length = source.get("content_bytes")
        if not isinstance(length, int) or isinstance(length, bool) or length <= 0:
            findings.bad.append(f"{label}.input.content_bytes: positive integer required")
        immutable = _require_mapping(
            source.get("immutable_input"), f"{label}.input.immutable_input", findings
        )
        if immutable is not None:
            if immutable.get("kind") != "git-bundle":
                findings.bad.append(
                    f"{label}.input.immutable_input.kind: only 'git-bundle' is accepted; "
                    "an unretained input cannot be verified"
                )
            _require_prose(immutable, "path", f"{label}.input.immutable_input", findings)

    extraction = _require_mapping(document["extraction"], f"{label}.extraction", findings)
    if extraction is not None:
        method = extraction.get("method")
        if method not in EXTRACTION_METHODS:
            findings.bad.append(
                f"{label}.extraction.method: expected one of {sorted(EXTRACTION_METHODS)}, "
                f"observed {method!r}"
            )
        _require_prose(extraction, "performed_by", f"{label}.extraction", findings)
        _require_prose(extraction, "custody", f"{label}.extraction", findings)

    licence = _require_mapping(document["license"], f"{label}.license", findings)
    if licence is not None:
        _require_prose(licence, "identifier", f"{label}.license", findings)
        _require_prose(licence, "notice_path", f"{label}.license", findings)
        _require_hex(licence, "notice_sha256", f"{label}.license", SHA256_RE, findings)

    destination = _require_mapping(document["destination"], f"{label}.destination", findings)
    if destination is not None:
        _require_prose(destination, "repository", f"{label}.destination", findings)
        _require_hex(destination, "base_commit", f"{label}.destination", SHA1_RE, findings)
        _require_hex(destination, "head_commit", f"{label}.destination", SHA1_RE, findings)
        _require_hex(destination, "head_tree", f"{label}.destination", SHA1_RE, findings)

    transformed = document["transformed_files"]
    if not isinstance(transformed, list) or not transformed:
        findings.bad.append(f"{label}.transformed_files: a nonempty list is required")
        return document
    for index, entry in enumerate(transformed):
        entry_label = f"{label}.transformed_files[{index}]"
        item = _require_mapping(entry, entry_label, findings)
        if item is None:
            continue
        _require_prose(item, "destination_path", entry_label, findings)
        _require_hex(item, "destination_blob", entry_label, SHA1_RE, findings)
        _require_hex(item, "destination_sha256", entry_label, SHA256_RE, findings)
        base_blob = item.get("base_blob")
        if base_blob is not None and not (
            isinstance(base_blob, str) and SHA1_RE.match(base_blob)
        ):
            findings.bad.append(
                f"{entry_label}.base_blob: null (path absent at base) or exact 40-hex required"
            )
        ranges = item.get("ranges")
        if not isinstance(ranges, list) or not ranges:
            findings.bad.append(f"{entry_label}.ranges: a nonempty list is required")
            continue
        for position, raw_range in enumerate(ranges):
            range_label = f"{entry_label}.ranges[{position}]"
            mapping = _require_mapping(raw_range, range_label, findings)
            if mapping is None:
                continue
            _require_range(mapping.get("derived_lines"), f"{range_label}.derived_lines", findings)
            _require_range(mapping.get("input_lines"), f"{range_label}.input_lines", findings)
            _require_hex(
                mapping, "destination_slice_sha256", range_label, SHA256_RE, findings
            )
            _require_hex(mapping, "input_slice_sha256", range_label, SHA256_RE, findings)
    return document


# ---------------------------------------------------------------------------
# Byte-level verification against the immutable input and the destination
# ---------------------------------------------------------------------------


def _open_bundle(
    root: Path,
    bundle_rel: str,
    label: str,
    findings: _Findings,
    scratch: Path,
    tracked: set[str],
):
    relative = Path(bundle_rel)
    if relative.is_absolute() or bundle_rel not in tracked:
        findings.bad.append(
            f"{label}: immutable input bundle {bundle_rel!r} must be a tracked "
            "repository-relative file"
        )
        return None
    try:
        tree_entry = git(root, "ls-tree", "HEAD", "--", bundle_rel).decode().strip()
    except GitError as exc:
        findings.cno.append(f"{label}: retained bundle identity could not be read ({exc})")
        return None
    if not tree_entry:
        findings.bad.append(
            f"{label}: immutable input bundle {bundle_rel!r} is tracked but not retained in HEAD"
        )
        return None
    mode = tree_entry.split(maxsplit=1)[0]
    if mode not in {"100644", "100755"}:
        findings.bad.append(
            f"{label}: immutable input bundle {bundle_rel!r} must be a retained regular file, "
            f"observed Git mode {mode}"
        )
        return None
    try:
        retained_bytes = git(root, "cat-file", "blob", f"HEAD:{bundle_rel}")
    except GitError as exc:
        findings.cno.append(f"{label}: retained immutable input bundle could not be read ({exc})")
        return None
    bundle = scratch / f"bundle-{sha256_hex(bundle_rel.encode('utf-8'))[:12]}.bundle"
    _write(bundle, retained_bytes)
    view = scratch / f"input-{sha256_hex(bundle_rel.encode('utf-8'))[:12]}.git"
    if view.exists():
        return view
    try:
        git(scratch, "init", "--bare", "--quiet", str(view))
        git(view, "bundle", "verify", str(bundle))
        git(
            view,
            "fetch",
            "--quiet",
            str(bundle),
            "refs/heads/*:refs/heads/*",
            "refs/tags/*:refs/tags/*",
        )
    except GitError as exc:
        findings.cno.append(f"{label}: immutable input bundle is unusable ({exc})")
        shutil.rmtree(view, ignore_errors=True)
        return None
    return view


def _read_blob(repo: Path, treeish: str, path: str, label: str, findings: _Findings):
    try:
        blob = git(repo, "rev-parse", "--verify", f"{treeish}:{path}").decode().strip()
    except GitError:
        findings.bad.append(f"{label}: {path!r} is not present in tree {treeish}")
        return None, None
    if not SHA1_RE.match(blob):
        findings.cno.append(f"{label}: unexpected object identity {blob!r} for {path!r}")
        return None, None
    try:
        payload = git(repo, "cat-file", "blob", blob)
    except GitError as exc:
        findings.cno.append(f"{label}: blob {blob} could not be read ({exc})")
        return None, None
    return blob, payload


def verify_input(
    root: Path,
    document: dict,
    label: str,
    findings: _Findings,
    scratch: Path,
    tracked: set[str],
) -> bytes | None:
    source = document["input"]
    immutable = source.get("immutable_input")
    if not isinstance(immutable, dict) or not isinstance(immutable.get("path"), str):
        return None
    view = _open_bundle(root, immutable["path"], label, findings, scratch, tracked)
    if view is None:
        return None

    commit = source["commit"]
    try:
        kind = git(view, "cat-file", "-t", commit).decode().strip()
    except GitError:
        findings.bad.append(
            f"{label}.input.commit: {commit} is not present in the retained immutable input"
        )
        return None
    if kind != "commit":
        findings.bad.append(f"{label}.input.commit: {commit} is a {kind}, not a commit")
        return None

    observed_tree = git(view, "rev-parse", "--verify", f"{commit}^{{tree}}").decode().strip()
    if observed_tree != source["tree"]:
        findings.bad.append(
            f"{label}.input.tree: commit {commit} carries tree {observed_tree}, "
            f"not the claimed {source['tree']}"
        )
        return None

    blob, payload = _read_blob(
        view, source["tree"], source["source_path"], f"{label}.input", findings
    )
    if blob is None or payload is None:
        return None
    if blob != source["blob"]:
        findings.bad.append(
            f"{label}.input.blob: {source['source_path']!r} resolves to {blob}, "
            f"not the claimed {source['blob']}"
        )
        return None

    observed_digest = sha256_hex(payload)
    if observed_digest != source["content_sha256"]:
        findings.bad.append(
            f"{label}.input.content_sha256: input bytes hash to {observed_digest}, "
            f"not the claimed {source['content_sha256']}"
        )
        return None
    if len(payload) != source["content_bytes"]:
        findings.bad.append(
            f"{label}.input.content_bytes: input is {len(payload)} bytes, "
            f"not the claimed {source['content_bytes']}"
        )
        return None
    findings.bindings += 1
    return payload


def verify_destination(
    root: Path, document: dict, label: str, findings: _Findings, tracked: set[str]
) -> None:
    destination = document["destination"]
    head = destination["head_commit"]
    base = destination["base_commit"]

    for name, commit in (("head_commit", head), ("base_commit", base)):
        try:
            kind = git(root, "cat-file", "-t", commit).decode().strip()
        except GitError:
            findings.bad.append(
                f"{label}.destination.{name}: {commit} is not present in this repository's history"
            )
            return
        if kind != "commit":
            findings.bad.append(f"{label}.destination.{name}: {commit} is a {kind}, not a commit")
            return

    observed_head_tree = git(root, "rev-parse", "--verify", f"{head}^{{tree}}").decode().strip()
    if observed_head_tree != destination["head_tree"]:
        findings.bad.append(
            f"{label}.destination.head_tree: head {head} carries tree {observed_head_tree}, "
            f"not the claimed {destination['head_tree']}"
        )
        return
    if base == head:
        findings.bad.append(
            f"{label}.destination: base and head are the same commit, so no diff introduced the "
            "derived source"
        )
        return
    if not git_ok(root, "merge-base", "--is-ancestor", base, head):
        findings.bad.append(
            f"{label}.destination: base {base} is not an ancestor of head {head}"
        )
        return
    if not git_ok(root, "merge-base", "--is-ancestor", head, "HEAD"):
        findings.cno.append(
            f"{label}.destination: head {head} is not reachable from the current HEAD, so the "
            "recorded destination diff cannot be observed here"
        )
        return

    licence = document["license"]
    notice_blob, notice_bytes = _read_blob(
        root, destination["head_tree"], licence["notice_path"], f"{label}.license", findings
    )
    if notice_bytes is not None:
        observed = sha256_hex(notice_bytes)
        if observed != licence["notice_sha256"]:
            findings.bad.append(
                f"{label}.license.notice_sha256: notice bytes hash to {observed}, "
                f"not the claimed {licence['notice_sha256']}"
            )
        else:
            findings.bindings += 1

    input_payload = document.pop("_input_payload", None)
    for index, item in enumerate(document["transformed_files"]):
        entry_label = f"{label}.transformed_files[{index}]"
        path = item["destination_path"]
        if path not in tracked:
            findings.bad.append(f"{entry_label}: {path!r} is not a tracked file in this repository")
            continue
        blob, payload = _read_blob(root, destination["head_tree"], path, entry_label, findings)
        if blob is None or payload is None:
            continue
        if blob != item["destination_blob"]:
            findings.bad.append(
                f"{entry_label}.destination_blob: {path!r} resolves to {blob} at head, "
                f"not the claimed {item['destination_blob']}"
            )
            continue
        observed = sha256_hex(payload)
        if observed != item["destination_sha256"]:
            findings.bad.append(
                f"{entry_label}.destination_sha256: destination bytes hash to {observed}, "
                f"not the claimed {item['destination_sha256']}"
            )
            continue

        worktree_file = root / path
        try:
            worktree_bytes = worktree_file.read_bytes()
        except OSError as exc:
            findings.cno.append(f"{entry_label}: {path!r} could not be read ({exc})")
            continue
        if sha256_hex(worktree_bytes) != observed:
            findings.bad.append(
                f"{entry_label}: the working-tree copy of {path!r} differs from the recorded "
                "destination head, so the record no longer describes the shipped bytes"
            )
            continue

        base_blob = item.get("base_blob")
        try:
            observed_base = git(
                root, "rev-parse", "--verify", f"{base}:{path}"
            ).decode().strip()
        except GitError:
            observed_base = None
        if observed_base != base_blob:
            findings.bad.append(
                f"{entry_label}.base_blob: {path!r} is {observed_base!r} at base {base}, "
                f"not the claimed {base_blob!r}"
            )
            continue
        if observed_base == blob:
            findings.bad.append(
                f"{entry_label}: {path!r} is unchanged between base and head, so the recorded "
                "destination diff does not contain this derived file"
            )
            continue
        if MARKER_BYTES not in worktree_bytes:
            findings.bad.append(
                f"{entry_label}: {path!r} does not carry the derived-source marker, so a reader "
                "of the file cannot learn it is derived"
            )
            continue

        _verify_ranges(item, entry_label, payload, input_payload, findings)


def _verify_ranges(
    item: dict,
    entry_label: str,
    destination_payload: bytes,
    input_payload: bytes | None,
    findings: _Findings,
) -> None:
    destination_lines = len(split_lines(destination_payload))
    input_lines = len(split_lines(input_payload)) if input_payload is not None else None
    previous_end = 0
    for position, mapping in enumerate(item["ranges"]):
        range_label = f"{entry_label}.ranges[{position}]"
        derived_start, derived_end = mapping["derived_lines"]
        source_start, source_end = mapping["input_lines"]

        if derived_start <= previous_end:
            findings.bad.append(
                f"{range_label}: derived ranges must be ordered and non-overlapping"
            )
            return
        previous_end = derived_end

        if derived_end > destination_lines:
            findings.bad.append(
                f"{range_label}.derived_lines: claims through line {derived_end} of a "
                f"{destination_lines}-line destination file"
            )
            continue

        derived_extent = derived_end - derived_start + 1
        source_extent = source_end - source_start + 1
        if derived_extent > source_extent:
            findings.bad.append(
                f"{range_label}: claimed derived extent of {derived_extent} lines exceeds the "
                f"{source_extent}-line input proof it cites"
            )
            continue

        observed_destination = sha256_hex(
            slice_bytes(destination_payload, derived_start, derived_end)
        )
        if observed_destination != mapping["destination_slice_sha256"]:
            findings.bad.append(
                f"{range_label}.destination_slice_sha256: destination lines "
                f"{derived_start}-{derived_end} hash to {observed_destination}, "
                f"not the claimed {mapping['destination_slice_sha256']}"
            )
            continue

        if input_payload is None or input_lines is None:
            findings.cno.append(
                f"{range_label}: the immutable input was not verifiable, so this derived range "
                "is not bound to an input"
            )
            continue
        if source_end > input_lines:
            findings.bad.append(
                f"{range_label}.input_lines: cites through line {source_end} of a "
                f"{input_lines}-line input, so the claim exceeds its input proof"
            )
            continue
        observed_input = sha256_hex(slice_bytes(input_payload, source_start, source_end))
        if observed_input != mapping["input_slice_sha256"]:
            findings.bad.append(
                f"{range_label}.input_slice_sha256: input lines {source_start}-{source_end} "
                f"hash to {observed_input}, not the claimed {mapping['input_slice_sha256']}"
            )
            continue
        findings.bindings += 1


# ---------------------------------------------------------------------------
# Population assessment
# ---------------------------------------------------------------------------


def tracked_files(root: Path) -> list[str]:
    payload = git(root, "ls-files", "-z")
    return [name for name in payload.decode("utf-8", "surrogateescape").split("\0") if name]


def assess(root: Path, marker_doc_paths: tuple[str, ...] = MARKER_DOC_PATHS) -> PopulationResult:
    """Enumerate the universe and derive one four-valued population verdict."""
    findings = _Findings()
    try:
        universe = tracked_files(root)
    except (GitUnavailable, GitError) as exc:
        return PopulationResult(
            verdict=Verdict.CANNOT_OBSERVE,
            could_not_observe=(f"universe could not be enumerated ({exc}); we did not look",),
        )

    marked: list[str] = []
    for name in universe:
        candidate = root / name
        try:
            payload = candidate.read_bytes()
        except OSError as exc:
            findings.cno.append(f"tracked file {name!r} could not be read ({exc})")
            continue
        if MARKER_BYTES in payload:
            marked.append(name)

    allowed = set(marker_doc_paths)
    for name in marker_doc_paths:
        if name not in universe:
            findings.cno.append(
                f"marker-bearing contract document {name!r} is absent from the tracked universe"
            )
        elif name not in marked:
            findings.bad.append(
                f"marker-bearing contract document {name!r} no longer teaches the derived-source "
                "marker, so the marker scan is unanchored"
            )

    record_paths = sorted(
        name
        for name in universe
        if name.startswith(f"{RECORDS_DIR}/") and name.endswith(".json")
    )

    parsed_records: list[tuple[str, object]] = []
    documents: list[tuple[str, dict]] = []
    for name in record_paths:
        label = name
        try:
            raw = (root / name).read_bytes()
        except OSError as exc:
            findings.cno.append(f"provenance record {name!r} could not be read ({exc})")
            continue
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.bad.append(f"provenance record {name!r} is not valid JSON ({exc})")
            continue
        parsed_records.append((label, parsed))
        before_shape = len(findings.bad)
        document = record_shape(parsed, label, findings)
        if isinstance(document, dict) and document.get("record_id") != Path(name).stem:
            findings.bad.append(
                f"{label}.record_id: must match filename stem {Path(name).stem!r}, "
                f"observed {document.get('record_id')!r}"
            )
        # Byte-level verification reads fields the shape stage just proved present;
        # a structurally broken record is already red and is not probed further.
        if document is not None and len(findings.bad) == before_shape:
            documents.append((label, document))

    claimed_paths: set[str] = set()
    for _, parsed in parsed_records:
        transformed = parsed.get("transformed_files") if isinstance(parsed, dict) else None
        if isinstance(transformed, list):
            for item in transformed:
                if isinstance(item, dict) and isinstance(item.get("destination_path"), str):
                    claimed_paths.add(item["destination_path"])

    for name in sorted(set(marked) - allowed - claimed_paths):
        findings.bad.append(
            f"{name!r} carries the derived-source marker but no provenance record claims it; "
            "an unrecorded derived file is indistinguishable from independent repair"
        )

    with tempfile.TemporaryDirectory(prefix="sssf-hd15-input-") as raw_scratch:
        scratch = Path(raw_scratch)
        universe_set = set(universe)
        for label, document in documents:
            before_bad = len(findings.bad)
            payload = verify_input(root, document, label, findings, scratch, universe_set)
            if len(findings.bad) == before_bad:
                document["_input_payload"] = payload
                verify_destination(root, document, label, findings, universe_set)

    if findings.bad:
        verdict = Verdict.FAIL
    elif findings.cno:
        verdict = Verdict.CANNOT_OBSERVE
    elif not documents:
        verdict = Verdict.NOT_APPLICABLE
    else:
        verdict = Verdict.PASS

    return PopulationResult(
        verdict=verdict,
        observed_bad=tuple(findings.bad),
        could_not_observe=tuple(findings.cno),
        records_checked=tuple(label for label, _ in documents),
        marked_files=tuple(sorted(set(marked) - allowed)),
        universe_files=len(universe),
        verified_bindings=findings.bindings,
    )


# ---------------------------------------------------------------------------
# Contract surface: the template must exist, be schema-shaped, and be inert
# ---------------------------------------------------------------------------


def extract_template(root: Path) -> tuple[object | None, str | None]:
    doc = root / CONTRACT_DOC
    if not doc.is_file():
        return None, f"contract document {CONTRACT_DOC} is absent"
    text = doc.read_text(encoding="utf-8")
    blocks = re.findall(r"```json\n(.*?)```", text, flags=re.DOTALL)
    if len(blocks) != 1:
        return None, f"{CONTRACT_DOC} must carry exactly one JSON template block, found {len(blocks)}"
    try:
        return json.loads(blocks[0]), None
    except json.JSONDecodeError as exc:
        return None, f"{CONTRACT_DOC} template block is not valid JSON ({exc})"


def contract_errors(root: Path) -> list[str]:
    errors: list[str] = []

    template, problem = extract_template(root)
    if problem is not None:
        errors.append(problem)
    else:
        findings = _Findings()
        record_shape(template, "template", findings)
        if not findings.bad:
            errors.append(
                "the shipped template is accepted as a real provenance record; a placeholder "
                "template must never satisfy the contract"
            )
        if isinstance(template, dict):
            if template.get("schema_version") != SCHEMA_VERSION:
                errors.append(f"template schema_version drifted from {SCHEMA_VERSION}")
            caveats = template.get("caveats")
            if not isinstance(caveats, list) or REQUIRED_CAVEAT not in caveats:
                errors.append(f"template does not carry the {REQUIRED_CAVEAT} caveat")
            if set(template) != {
                "schema_version",
                "record_id",
                "caveats",
                "input",
                "extraction",
                "license",
                "destination",
                "transformed_files",
            }:
                errors.append("template key set drifted from the enforced record shape")

    readme = root / RECORDS_README
    if not readme.is_file():
        errors.append(f"{RECORDS_README} is absent, so the record registry is undeclared")

    for name in MARKER_DOC_PATHS:
        if not (root / name).is_file():
            errors.append(f"marker-bearing contract document {name} is absent")

    return errors


# ---------------------------------------------------------------------------
# Calibration: watched-red controls built from immutable objects in a sandbox
# ---------------------------------------------------------------------------

CALIBRATION_INPUT_PATH = "src/hardening/gate.py"
CALIBRATION_DEST_PATH = "apps/example/derived_gate.py"
CALIBRATION_NOTICE_PATH = "apps/example/DERIVED_LICENSE.txt"

CALIBRATION_INPUT_BYTES = (
    b"# assessment workspace module\n"
    b"import sys\n"
    b"\n"
    b"def outcome(violations, observations):\n"
    b'    """Three values, never two."""\n'
    b"    if violations:\n"
    b'        return "FAIL"\n'
    b"    if not observations:\n"
    b'        return "COULD_NOT_OBSERVE"\n'
    b'    return "PASS"\n'
    b"\n"
    b"\n"
    b"def main():\n"
    b"    return 0\n"
)

CALIBRATION_NOTICE_BYTES = b"Copyright (c) assessment workspace.\nSPDX-License-Identifier: MIT\n"

# Derived destination lines 5-14 correspond to input lines 3-12.
CALIBRATION_DEST_BYTES = (
    b"# " + MARKER_BYTES + b": see docs/reference/DERIVED_SOURCE_PROVENANCE.md\n"
    b"# record: docs/provenance/derived_source/calibration-derived-gate.json\n"
    b"\n"
    b"\n"
    b"import sys\n"
    b"\n"
    b"def outcome(violations, observations):\n"
    b'    """Three values, never two."""\n'
    b"    if violations:\n"
    b'        return "FAIL"\n'
    b"    if not observations:\n"
    b'        return "COULD_NOT_OBSERVE"\n'
    b'    return "PASS"\n'
    b"\n"
    b"\n"
    b"def main():\n"
    b"    return 0\n"
)

CALIBRATION_BASE_BYTES = b"# placeholder module\n"

CALIBRATION_UNMARKED_PATH = "apps/example/unmarked_copy.py"
CALIBRATION_UNMARKED_BYTES = CALIBRATION_DEST_BYTES.replace(
    b"# " + MARKER_BYTES + b": see docs/reference/DERIVED_SOURCE_PROVENANCE.md\n",
    b"# copied module\n",
    1,
)

# Pinned Git object identities of the calibration input, computed from the object
# format itself rather than read back from the builder. If a host reproduces
# different identities the calibration is could-not-observe, never a quiet pass.
EXPECTED_INPUT_COMMIT = "608d78d5801a4ca511e0428122c4d251925c86d0"
EXPECTED_INPUT_TREE = "876699347641193e4df3aea55560ce0a5d7487b2"
EXPECTED_INPUT_BLOB = "ea7bd823e9716439389e4ac49caacdd540229617"
EXPECTED_INPUT_CONTENT_SHA256 = (
    "a036168cea1e90cfcebf2fad15bd6fc1ff641ed066a252428c529eae737c79e1"
)
EXPECTED_INPUT_CONTENT_BYTES = 262

CALIBRATION_INPUT_BRANCH = "assessment/hardening-source"
CALIBRATION_INPUT_TAG = "assessment-v1"


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _commit_tree(repo: Path, entries: dict[str, str], message: str, parent: str | None) -> str:
    """Build a (possibly nested) tree from blob ids, then commit it with plumbing."""

    def build(prefix: str) -> str:
        children: dict[str, str] = {}
        lines: list[str] = []
        for name, blob in entries.items():
            if not name.startswith(prefix):
                continue
            remainder = name[len(prefix):]
            head, _, tail = remainder.partition("/")
            if tail:
                children.setdefault(head, "")
            else:
                lines.append(f"100644 blob {blob}\t{head}")
        for directory in sorted(children):
            sub = build(f"{prefix}{directory}/")
            lines.append(f"040000 tree {sub}\t{directory}")
        payload = ("\n".join(sorted(lines, key=lambda line: line.split("\t", 1)[1])) + "\n")
        return git(repo, "mktree", stdin=payload.encode("utf-8")).decode().strip()

    tree = build("")
    args = ["commit-tree", tree, "-m", message]
    if parent is not None:
        args.extend(["-p", parent])
    return git(repo, *args).decode().strip()


def _hash_blob(repo: Path, payload: bytes) -> str:
    return git(repo, "hash-object", "-w", "--stdin", stdin=payload).decode().strip()


def build_input_repository(scratch: Path) -> tuple[Path, Path, list[str]]:
    """Materialise the immutable calibration input and bundle it. Fixture-only."""
    problems: list[str] = []
    repo = scratch / "assessment-input.git"
    git(scratch, "init", "--bare", "--quiet", str(repo))

    blob = _hash_blob(repo, CALIBRATION_INPUT_BYTES)
    commit = _commit_tree(repo, {CALIBRATION_INPUT_PATH: blob}, "hardening gate", None)
    tree = git(repo, "rev-parse", "--verify", f"{commit}^{{tree}}").decode().strip()

    git(repo, "update-ref", f"refs/heads/{CALIBRATION_INPUT_BRANCH}", commit)
    git(repo, "update-ref", f"refs/tags/{CALIBRATION_INPUT_TAG}", commit)

    for label, observed, expected in (
        ("blob", blob, EXPECTED_INPUT_BLOB),
        ("tree", tree, EXPECTED_INPUT_TREE),
        ("commit", commit, EXPECTED_INPUT_COMMIT),
    ):
        if observed != expected:
            problems.append(
                f"calibration input {label} is {observed}, not the independently authored "
                f"{expected}; the immutable input is not reproducible on this host"
            )

    bundle = scratch / "assessment-input.bundle"
    git(repo, "bundle", "create", str(bundle), "--all")
    return repo, bundle, problems


CALIBRATION_BUNDLE_REL = "docs/evidence/hd15/calibration-assessment-input.bundle"
CALIBRATION_INVALID_BUNDLE_REL = "docs/evidence/hd15/invalid-assessment-input.bundle"
CALIBRATION_SYMLINK_BUNDLE_REL = "docs/evidence/hd15/symlink-assessment-input.bundle"


def build_destination_base(scratch: Path) -> Path:
    """A throwaway destination worktree before any derived source exists."""
    repo = scratch / "destination"
    repo.mkdir()
    git(scratch, "init", "--quiet", "--initial-branch", "main", str(repo))

    _write(repo / CALIBRATION_DEST_PATH, CALIBRATION_BASE_BYTES)
    _write(repo / CALIBRATION_NOTICE_PATH, CALIBRATION_NOTICE_BYTES)
    for name in MARKER_DOC_PATHS:
        _write(repo / name, f"marker taught here: {MARKER}\n".encode("utf-8"))
    _write(repo / RECORDS_README, b"registry\n")
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "base")
    return repo


def advance_destination(repo: Path, bundle: Path) -> dict:
    """Land the derived source, then hand back the honest record describing it."""
    base_commit = git(repo, "rev-parse", "HEAD").decode().strip()
    base_blob = git(repo, "rev-parse", f"{base_commit}:{CALIBRATION_DEST_PATH}").decode().strip()

    _write(repo / CALIBRATION_DEST_PATH, CALIBRATION_DEST_BYTES)
    _write(repo / CALIBRATION_UNMARKED_PATH, CALIBRATION_UNMARKED_BYTES)
    _write(repo / CALIBRATION_BUNDLE_REL, bundle.read_bytes())
    _write(repo / CALIBRATION_INVALID_BUNDLE_REL, b"not a Git bundle\n")
    symlink = repo / CALIBRATION_SYMLINK_BUNDLE_REL
    symlink.parent.mkdir(parents=True, exist_ok=True)
    symlink.symlink_to(Path(CALIBRATION_BUNDLE_REL).name)
    git(repo, "add", "--all")
    git(repo, "commit", "--quiet", "-m", "import derived gate")
    head_commit = git(repo, "rev-parse", "HEAD").decode().strip()
    head_tree = git(repo, "rev-parse", f"{head_commit}^{{tree}}").decode().strip()
    dest_blob = git(repo, "rev-parse", f"{head_commit}:{CALIBRATION_DEST_PATH}").decode().strip()

    record = {
        "schema_version": SCHEMA_VERSION,
        "record_id": "calibration-derived-gate",
        "caveats": [REQUIRED_CAVEAT],
        "input": {
            "source_repository": "file:///calibration/assessment-workspace.git",
            "source_path": CALIBRATION_INPUT_PATH,
            "commit": EXPECTED_INPUT_COMMIT,
            "tree": EXPECTED_INPUT_TREE,
            "blob": EXPECTED_INPUT_BLOB,
            "content_sha256": EXPECTED_INPUT_CONTENT_SHA256,
            "content_bytes": EXPECTED_INPUT_CONTENT_BYTES,
            "immutable_input": {"kind": "git-bundle", "path": CALIBRATION_BUNDLE_REL},
        },
        "extraction": {
            "method": "verbatim-copy",
            "performed_by": "HD-15 calibration harness",
            "custody": "bundle retained in the destination repository at the recorded path",
        },
        "license": {
            "identifier": "MIT",
            "notice_path": CALIBRATION_NOTICE_PATH,
            "notice_sha256": sha256_hex(CALIBRATION_NOTICE_BYTES),
        },
        "destination": {
            "repository": "file:///calibration/destination.git",
            "base_commit": base_commit,
            "head_commit": head_commit,
            "head_tree": head_tree,
        },
        "transformed_files": [
            {
                "destination_path": CALIBRATION_DEST_PATH,
                "destination_blob": dest_blob,
                "destination_sha256": sha256_hex(CALIBRATION_DEST_BYTES),
                "base_blob": base_blob,
                "ranges": [
                    {
                        "derived_lines": [5, 14],
                        "destination_slice_sha256": sha256_hex(
                            slice_bytes(CALIBRATION_DEST_BYTES, 5, 14)
                        ),
                        "input_lines": [3, 12],
                        "input_slice_sha256": sha256_hex(
                            slice_bytes(CALIBRATION_INPUT_BYTES, 3, 12)
                        ),
                    }
                ],
            }
        ],
    }
    return record


def write_record(repo: Path, record: dict) -> None:
    path = repo / RECORDS_DIR / f"{record['record_id']}.json"
    _write(path, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    git(repo, "add", "--all")


def commit_record(repo: Path, record: dict) -> None:
    write_record(repo, record)
    git(repo, "commit", "--quiet", "-m", "record derived-source provenance")


def clone_of(value):
    return json.loads(json.dumps(value))


def calibration_errors() -> list[str]:
    """Watch every control go red before trusting any green."""
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sssf-hd15-calibration-") as raw:
        scratch = Path(raw)
        try:
            _, bundle, problems = build_input_repository(scratch)
        except (GitUnavailable, GitError) as exc:
            return [f"CNO: calibration input could not be materialised ({exc})"]
        errors.extend(problems)
        if problems:
            return errors

        repo = build_destination_base(scratch)

        empty = assess(repo)
        if empty.verdict is not Verdict.NOT_APPLICABLE:
            errors.append(
                f"absence control: expected NOT_APPLICABLE, observed {empty.verdict.value} "
                f"({empty.observed_bad + empty.could_not_observe})"
            )
        if empty.verdict is Verdict.PASS:
            errors.append("absence control: absence was rendered as a pass")
        if empty.records_checked or empty.marked_files:
            errors.append("absence control: an empty universe reported derived source")
        if empty.universe_files < 1:
            errors.append("absence control: the universe itself was empty, so nothing was checked")

        honest = advance_destination(repo, bundle)

        unrecorded = assess(repo)
        if unrecorded.verdict is not Verdict.FAIL:
            errors.append(
                "unrecorded-marker control: a marked file with no record did not go red "
                f"(observed {unrecorded.verdict.value})"
            )
        elif not any(
            "no provenance record claims it" in finding for finding in unrecorded.observed_bad
        ):
            errors.append(
                f"unrecorded-marker control: went red for the wrong reason "
                f"({unrecorded.observed_bad})"
            )

        commit_record(repo, honest)

        green = assess(repo)
        if green.verdict is not Verdict.PASS:
            errors.append(
                "positive control: an honest complete record did not pass "
                f"({green.verdict.value}: {green.observed_bad + green.could_not_observe})"
            )
        if green.verified_bindings < 3:
            errors.append(
                f"positive control: only {green.verified_bindings} byte-level bindings were "
                "verified; the contract would be vacuous"
            )
        if list(green.records_checked) != [f"{RECORDS_DIR}/calibration-derived-gate.json"]:
            errors.append("positive control: the record registry was not enumerated")

        errors.extend(_mutation_controls(repo, honest, bundle))
    return errors


def _apply(repo: Path, record: dict) -> PopulationResult:
    write_record(repo, record)
    return assess(repo)


def _restore(repo: Path, honest: dict) -> None:
    write_record(repo, honest)


def _expect_red(
    repo: Path,
    honest: dict,
    label: str,
    mutate,
    expected: Verdict,
    fragment: str,
    errors: list[str],
) -> None:
    mutant = clone_of(honest)
    mutate(mutant)
    result = _apply(repo, mutant)
    findings = result.observed_bad + result.could_not_observe
    if result.verdict is not expected:
        errors.append(
            f"{label}: expected {expected.value}, observed {result.verdict.value} ({findings})"
        )
    elif not any(fragment in finding for finding in findings):
        errors.append(f"{label}: went {expected.value} for the wrong reason ({findings})")
    _restore(repo, honest)


def _mutation_controls(repo: Path, honest: dict, bundle: Path) -> list[str]:
    errors: list[str] = []
    base_tree = git(
        repo, "rev-parse", "--verify", f"{honest['destination']['base_commit']}^{{tree}}"
    ).decode().strip()
    head_tree = honest["destination"]["head_tree"]
    unmarked_blob = git(repo, "rev-parse", f"{head_tree}:{CALIBRATION_UNMARKED_PATH}").decode().strip()
    notice_blob = git(repo, "rev-parse", f"{head_tree}:{CALIBRATION_NOTICE_PATH}").decode().strip()

    def drop_commit(record: dict) -> None:
        del record["input"]["commit"]

    _expect_red(
        repo, honest, "missing source commit", drop_commit, Verdict.FAIL, "input.commit:", errors
    )

    def drop_tree(record: dict) -> None:
        del record["input"]["tree"]

    _expect_red(
        repo, honest, "missing source tree", drop_tree, Verdict.FAIL, "input.tree:", errors
    )

    def branch_name_identity(record: dict) -> None:
        record["input"]["commit"] = CALIBRATION_INPUT_BRANCH

    _expect_red(
        repo,
        honest,
        "branch name as identity",
        branch_name_identity,
        Verdict.FAIL,
        "not identity",
        errors,
    )

    def tag_name_identity(record: dict) -> None:
        record["input"]["commit"] = CALIBRATION_INPUT_TAG

    _expect_red(
        repo,
        honest,
        "tag name as identity",
        tag_name_identity,
        Verdict.FAIL,
        "not identity",
        errors,
    )

    def drop_caveat(record: dict) -> None:
        record["caveats"] = ["SOME_OTHER_NOTE"]

    _expect_red(
        repo, honest, "missing B3 caveat", drop_caveat, Verdict.FAIL, REQUIRED_CAVEAT, errors
    )

    def overreaching_range(record: dict) -> None:
        entry = record["transformed_files"][0]["ranges"][0]
        entry["derived_lines"] = [5, 16]
        entry["destination_slice_sha256"] = sha256_hex(slice_bytes(CALIBRATION_DEST_BYTES, 5, 16))

    _expect_red(
        repo,
        honest,
        "derived range exceeds input proof",
        overreaching_range,
        Verdict.FAIL,
        "exceeds the",
        errors,
    )

    def overreaching_input(record: dict) -> None:
        entry = record["transformed_files"][0]["ranges"][0]
        entry["input_lines"] = [3, 40]
        entry["input_slice_sha256"] = sha256_hex(slice_bytes(CALIBRATION_INPUT_BYTES, 3, 40))

    _expect_red(
        repo,
        honest,
        "input range beyond the proven input",
        overreaching_input,
        Verdict.FAIL,
        "exceeds its input proof",
        errors,
    )

    def tampered_content(record: dict) -> None:
        record["input"]["content_sha256"] = sha256_hex(b"different bytes\n")

    _expect_red(
        repo,
        honest,
        "input content hash not verified against bytes",
        tampered_content,
        Verdict.FAIL,
        "input bytes hash to",
        errors,
    )

    def tampered_tree(record: dict) -> None:
        record["input"]["tree"] = "0" * 40

    _expect_red(
        repo,
        honest,
        "input tree not bound to the commit",
        tampered_tree,
        Verdict.FAIL,
        "carries tree",
        errors,
    )

    def absent_commit(record: dict) -> None:
        record["input"]["commit"] = "1" * 40

    _expect_red(
        repo,
        honest,
        "input commit absent from the immutable input",
        absent_commit,
        Verdict.FAIL,
        "not present in the retained immutable input",
        errors,
    )

    def wrong_source_path(record: dict) -> None:
        record["input"]["source_path"] = "src/hardening/absent.py"

    _expect_red(
        repo,
        honest,
        "source path absent from the claimed tree",
        wrong_source_path,
        Verdict.FAIL,
        "is not present in tree",
        errors,
    )

    def tampered_input_slice(record: dict) -> None:
        record["transformed_files"][0]["ranges"][0]["input_slice_sha256"] = "b" * 64

    _expect_red(
        repo,
        honest,
        "input slice hash not verified against bytes",
        tampered_input_slice,
        Verdict.FAIL,
        "input lines 3-12",
        errors,
    )

    def tampered_destination(record: dict) -> None:
        record["transformed_files"][0]["destination_sha256"] = "c" * 64

    _expect_red(
        repo,
        honest,
        "destination hash not verified against bytes",
        tampered_destination,
        Verdict.FAIL,
        "destination bytes hash to",
        errors,
    )

    def unchanged_base(record: dict) -> None:
        entry = record["transformed_files"][0]
        entry["base_blob"] = entry["destination_blob"]

    _expect_red(
        repo,
        honest,
        "base blob not bound to the destination diff",
        unchanged_base,
        Verdict.FAIL,
        "at base",
        errors,
    )

    def swapped_base_head(record: dict) -> None:
        destination = record["destination"]
        destination["base_commit"], destination["head_commit"] = (
            destination["head_commit"],
            destination["base_commit"],
        )
        destination["head_tree"] = base_tree

    _expect_red(
        repo,
        honest,
        "base is not an ancestor of head",
        swapped_base_head,
        Verdict.FAIL,
        "is not an ancestor of",
        errors,
    )

    def unmarked_destination(record: dict) -> None:
        entry = record["transformed_files"][0]
        entry["destination_path"] = CALIBRATION_UNMARKED_PATH
        entry["destination_blob"] = unmarked_blob
        entry["destination_sha256"] = sha256_hex(CALIBRATION_UNMARKED_BYTES)
        entry["base_blob"] = None
        entry["ranges"][0]["destination_slice_sha256"] = sha256_hex(
            slice_bytes(CALIBRATION_UNMARKED_BYTES, 5, 14)
        )

    _expect_red(
        repo,
        honest,
        "recorded derived file does not carry the marker",
        unmarked_destination,
        Verdict.FAIL,
        "does not carry the derived-source marker",
        errors,
    )

    def undiffed_destination(record: dict) -> None:
        entry = record["transformed_files"][0]
        entry["destination_path"] = CALIBRATION_NOTICE_PATH
        entry["destination_blob"] = notice_blob
        entry["destination_sha256"] = sha256_hex(CALIBRATION_NOTICE_BYTES)
        entry["base_blob"] = notice_blob
        entry["ranges"] = [
            {
                "derived_lines": [1, 2],
                "destination_slice_sha256": sha256_hex(
                    slice_bytes(CALIBRATION_NOTICE_BYTES, 1, 2)
                ),
                "input_lines": [1, 2],
                "input_slice_sha256": sha256_hex(slice_bytes(CALIBRATION_INPUT_BYTES, 1, 2)),
            }
        ]

    _expect_red(
        repo,
        honest,
        "recorded file is unchanged between base and head",
        undiffed_destination,
        Verdict.FAIL,
        "unchanged between base and head",
        errors,
    )

    def untracked_destination(record: dict) -> None:
        record["transformed_files"][0]["destination_path"] = "apps/example/never_added.py"

    _expect_red(
        repo,
        honest,
        "recorded destination path is not tracked",
        untracked_destination,
        Verdict.FAIL,
        "is not a tracked file",
        errors,
    )

    def missing_license(record: dict) -> None:
        record["license"]["notice_sha256"] = "d" * 64

    _expect_red(
        repo,
        honest,
        "license notice hash not verified against bytes",
        missing_license,
        Verdict.FAIL,
        "notice bytes hash to",
        errors,
    )

    def placeholder_custody(record: dict) -> None:
        record["extraction"]["custody"] = "<who held it>"

    _expect_red(
        repo,
        honest,
        "placeholder custody",
        placeholder_custody,
        Verdict.FAIL,
        "placeholder value",
        errors,
    )

    def missing_bundle(record: dict) -> None:
        record["input"]["immutable_input"]["path"] = "docs/evidence/hd15/absent.bundle"

    _expect_red(
        repo,
        honest,
        "unretained immutable input",
        missing_bundle,
        Verdict.FAIL,
        "must be a tracked repository-relative file",
        errors,
    )

    def external_bundle(record: dict) -> None:
        record["input"]["immutable_input"]["path"] = str(bundle)

    _expect_red(
        repo,
        honest,
        "external immutable input",
        external_bundle,
        Verdict.FAIL,
        "must be a tracked repository-relative file",
        errors,
    )

    def symlink_bundle(record: dict) -> None:
        record["input"]["immutable_input"]["path"] = CALIBRATION_SYMLINK_BUNDLE_REL

    _expect_red(
        repo,
        honest,
        "symlink immutable input",
        symlink_bundle,
        Verdict.FAIL,
        "must be a retained regular file",
        errors,
    )

    retained_bundle = repo / CALIBRATION_BUNDLE_REL
    retained_bundle.write_bytes(b"uncommitted replacement\n")
    tampered_worktree = assess(repo)
    if tampered_worktree.verdict is not Verdict.PASS:
        errors.append(
            "worktree bundle isolation: committed bundle bytes did not remain authoritative "
            f"({tampered_worktree.verdict.value}: "
            f"{tampered_worktree.observed_bad + tampered_worktree.could_not_observe})"
        )
    retained_bundle.write_bytes(bundle.read_bytes())

    mismatched_path = repo / RECORDS_DIR / "wrong-record-name.json"
    _write(mismatched_path, (json.dumps(honest, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    git(repo, "add", str(mismatched_path.relative_to(repo)))
    mismatched = assess(repo)
    mismatch_findings = mismatched.observed_bad + mismatched.could_not_observe
    if mismatched.verdict is not Verdict.FAIL:
        errors.append(
            "record filename identity: expected FAIL, observed "
            f"{mismatched.verdict.value} ({mismatch_findings})"
        )
    elif not any("must match filename stem" in finding for finding in mismatch_findings):
        errors.append(f"record filename identity: went FAIL for the wrong reason ({mismatch_findings})")
    mismatched_path.unlink()
    git(repo, "add", "--all")

    # Precedence: a real violation must not be masked by an incomplete universe.
    mixed = clone_of(honest)
    mixed["input"]["content_sha256"] = sha256_hex(b"tampered\n")
    write_record(repo, mixed)
    unverifiable = clone_of(honest)
    unverifiable["record_id"] = "calibration-unverifiable"
    unverifiable["input"]["immutable_input"]["path"] = CALIBRATION_INVALID_BUNDLE_REL
    write_record(repo, unverifiable)
    precedence = assess(repo)
    if precedence.verdict is not Verdict.FAIL:
        errors.append(
            "precedence control: a violation alongside an incomplete universe reported "
            f"{precedence.verdict.value} instead of FAIL"
        )
    if not precedence.could_not_observe:
        errors.append("precedence control: the could-not-observe finding was discarded")
    (repo / RECORDS_DIR / "calibration-unverifiable.json").unlink()
    git(repo, "add", "--all")
    _restore(repo, honest)

    # The marker scan is only meaningful while the documents that teach the marker
    # still carry it; a silently reworded contract document must go red.
    anchor = repo / MARKER_DOC_PATHS[0]
    original = anchor.read_bytes()
    anchor.write_bytes(b"the marker was quietly removed from the contract document\n")
    unanchored = assess(repo)
    if unanchored.verdict is not Verdict.FAIL:
        errors.append(
            "marker-anchor control: a contract document that stopped teaching the marker "
            f"reported {unanchored.verdict.value} instead of FAIL"
        )
    elif not any("no longer teaches" in finding for finding in unanchored.observed_bad):
        errors.append(
            f"marker-anchor control: went red for the wrong reason ({unanchored.observed_bad})"
        )
    anchor.write_bytes(original)

    final = assess(repo)
    if final.verdict is not Verdict.PASS:
        errors.append(
            "restoration control: the honest record no longer passes after the mutation "
            f"sweep ({final.verdict.value}: {final.observed_bad + final.could_not_observe})"
        )
    return errors


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    parser.add_argument("--skip-calibration", action="store_true", help=argparse.SUPPRESS)
    options = parser.parse_args()
    root = Path(options.root).resolve()

    observed_bad = contract_errors(root)
    could_not_observe: list[str] = []

    if not options.skip_calibration:
        for finding in calibration_errors():
            if finding.startswith("CNO:"):
                could_not_observe.append(finding[4:].strip())
            else:
                observed_bad.append(finding)

    population = assess(root)
    if population.verdict is Verdict.FAIL:
        observed_bad.extend(population.observed_bad)
    elif population.verdict is Verdict.CANNOT_OBSERVE:
        could_not_observe.extend(population.could_not_observe)

    if observed_bad:
        state = "FAIL"
    elif could_not_observe:
        state = "CNO"
    else:
        state = "PASS"

    print(f"HD-15 derived-source provenance contract: {state}")
    print(
        f"HD-15 derived-source population: {population.verdict.value} "
        f"(records={len(population.records_checked)}, "
        f"marked-files={len(population.marked_files)}, "
        f"tracked-universe={population.universe_files}, "
        f"verified-bindings={population.verified_bindings})"
    )
    if population.verdict is Verdict.NOT_APPLICABLE:
        print(
            "HD-15 population note: the universe was enumerated and holds no derived source, "
            "so there is nothing to certify. NOT_APPLICABLE is a could-not-observe result and "
            "is not a pass; it does not state that any derived source complies."
        )

    for finding in observed_bad:
        print(f"- observed-bad: {finding}")
    for finding in could_not_observe:
        print(f"- could-not-observe: {finding}")

    if state != "PASS":
        return 1

    print("contract: template is schema-shaped and is refused as a real record")
    print(
        "watched-red: missing commit/tree, branch-name and tag-name identity, missing "
        f"{REQUIRED_CAVEAT}, over-reaching derived and input ranges"
    )
    print(
        "watched-red: tampered input content/tree/commit/path/slice, tampered destination and "
        "license bytes, unchanged base blob, non-ancestor base, placeholder custody"
    )
    print(
        "watched-red: untracked/external/symlink immutable input fails; committed bytes remain "
        "authoritative; unusable retained input is CNO; absence is NOT_APPLICABLE, not a pass"
    )
    print("watched-red: a violation alongside an incomplete universe still reports FAIL")
    print("migration: none authorised, none performed; this validator creates no import path")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
