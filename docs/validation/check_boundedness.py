#!/usr/bin/env python3
"""BOUND-1 canonical boundedness validator.

Answers the governing review question mechanically, for every declared growth
surface in this repository:

    What grows, who owns the bound, what happens at +1,
    and how will CI know if that protection disappears?

Three things make that answer non-vacuous:

1.  **Bidirectional coverage.** Every ``BOUNDEDNESS-OWNER`` marker in source
    resolves to exactly one registry entry, and every registry entry resolves
    to an existing marker in its declared owner file. A registry that can
    silently omit a new growing surface would not be a bound at all.
2.  **Probes, not prose.** An ``EXPLICIT_BOUND`` names its value AND a probe
    that re-reads that value out of the owner's source with ``ast``. Removing a
    limit, renaming it, or raising it without declaring the boundedness delta
    all go red here rather than being believed.
3.  **Live boundaries.** Each dynamic bound is exercised at ``limit - 1``,
    ``limit`` and ``limit + 1`` against the real enforcement owner, and each
    watched-red control is watched going red against a mutated copy before the
    real check is trusted.

Output is machine-readable PASS / FAIL / CNO with FAIL > CNO > PASS precedence.
Absence — an unreadable registry, a missing owner file, a probe that cannot be
resolved — is could-not-observe, and could-not-observe is never a pass.
"""

from __future__ import annotations

import ast
import io
import json
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

REGISTRY = Path("docs/reference/BOUNDEDNESS_REGISTRY.json")
LAW = Path("docs/development/BOUNDEDNESS_LAW.md")
PROTOCOL = Path("docs/development/INCREMENT_PROTOCOL.md")
INCREMENTS = Path("docs/increments")
CI_MANIFEST = Path("ci/checks.json")
GITIGNORE = Path(".gitignore")
RECOVERY = Path("docs/operations/RECOVERY.md")

OWNER_MARKER = "BOUNDEDNESS-OWNER"
POLICY_MARKER = "BOUNDEDNESS-POLICY"
MARKER_RE = re.compile(rf"{OWNER_MARKER}:\s*([A-Za-z0-9._-]+)")
POLICY_RE = re.compile(rf"{POLICY_MARKER}:\s*([A-Za-z0-9._-]+)")

SCANNED_SUFFIXES = {".py", ".just", ".sh", ".ts", ".yml", ".yaml", ".cmd"}
SKIPPED_DIRS = {
    ".git", ".venv", "node_modules", ".sandbox", ".pytest_cache", ".ruff_cache",
    "__pycache__", "images", "specs",
}
SKIPPED_PREFIXES = ("adws/adw_data/sessions",)

CLASSIFICATIONS = ("EXPLICIT_BOUND", "DERIVED_BOUND", "SAFE_UNBOUNDED")
OVERFLOW_VOCABULARY = {
    "REJECT", "BACKPRESSURE", "BLOCK_WAIT_WITH_TIMEOUT", "DEFER", "EVICT_OLDEST",
    "EVICT_POLICY", "TRUNCATE_WITH_EXPLICIT_STATUS",
    "SPILL_TO_BOUNDED_EXTERNAL_STORE", "CANCEL", "FAIL", "COULD_NOT_OBSERVE",
}
OBSERVATIONS = ("observed-good", "observed-bad", "could-not-observe")
COMMON_FIELDS = (
    "surface_id", "owner", "owner_path", "source_refs", "surface_kind",
    "resource_dimensions", "classification", "policy_identity",
    "admission_or_backpressure", "on_limit_behavior", "retention_or_cleanup",
    "observability", "verification_refs", "status",
)
SAFE_FIELDS = (
    "safety_invariant", "why_no_finite_local_bound_is_required",
    "failure_consequence", "archive_strategy", "falsification_test_or_review",
    "authority",
)
DELTA_KEY = "boundedness_delta"
BOUNDEDNESS_CHECK_ID = "boundedness-registry-validator"

# Justifications the law names as never sufficient on their own.
INSUFFICIENT_JUSTIFICATION = (
    "we do not expect it to get large",
    "the operator can clean it up",
    "the model should stop",
    "storage is cheap",
)


# ─────────────────────────────────────────────────────────────────────────────
# Three-valued result
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Result:
    """FAIL > CNO > PASS. A finding is never allowed to narrow into a pass."""

    failures: list[str]
    cnos: list[str]

    @property
    def status(self) -> str:
        if self.failures:
            return "FAIL"
        if self.cnos:
            return "CNO"
        return "PASS"

    def merge(self, other: "Result") -> "Result":
        return Result(self.failures + other.failures, self.cnos + other.cnos)


def ok() -> Result:
    return Result([], [])


def fail(*messages: str) -> Result:
    return Result(list(messages), [])


def cno(*messages: str) -> Result:
    return Result([], list(messages))


# ─────────────────────────────────────────────────────────────────────────────
# Source probes: read a declared limit back out of its owner
# ─────────────────────────────────────────────────────────────────────────────
class ProbeUnresolved(Exception):
    """The probe could not reach a value. Never a pass, never a mismatch."""


def _module(root: Path, relative: str) -> ast.Module:
    path = root / relative
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise ProbeUnresolved(f"{relative}: {exc}") from exc


_BINARY_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.LShift: lambda a, b: a << b,
}


def _literal(node: ast.AST, where: str) -> Any:
    """Resolve a constant bound, including the arithmetic these owners write.

    `4 * 1024 * 1024` and `1 << 20` are how a byte ceiling is spelled where a
    human has to read it, so the probe evaluates that closed set of operators
    over constants rather than demanding the value be flattened for its benefit.
    Anything else is unresolved, which is could-not-observe, not a pass.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_literal(node.operand, where)
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _literal(node.left, where)
        right = _literal(node.right, where)
        try:
            return _BINARY_OPS[type(node.op)](left, right)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ProbeUnresolved(f"{where}: bound arithmetic failed: {exc}") from exc
    try:
        return ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError) as exc:
        raise ProbeUnresolved(f"{where}: not a literal bound: {exc}") from exc


def probe_module_constant(root: Path, probe: dict[str, Any]) -> Any:
    tree = _module(root, probe["path"])
    name = probe["name"]
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if name in targets:
                return _literal(node.value, f"{probe['path']}::{name}")
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name and node.value is not None:
                return _literal(node.value, f"{probe['path']}::{name}")
    raise ProbeUnresolved(f"{probe['path']}: no module constant named {name}")


def probe_class_field_default(root: Path, probe: dict[str, Any]) -> Any:
    tree = _module(root, probe["path"])
    wanted_class, wanted_field = probe["class"], probe["field"]
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != wanted_class:
            continue
        for item in node.body:
            target = None
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                target = item.target.id
            elif isinstance(item, ast.Assign):
                names = [t.id for t in item.targets if isinstance(t, ast.Name)]
                target = names[0] if names else None
            if target == wanted_field:
                if getattr(item, "value", None) is None:
                    raise ProbeUnresolved(
                        f"{probe['path']}::{wanted_class}.{wanted_field} has no default"
                    )
                return _literal(item.value, f"{wanted_class}.{wanted_field}")
        raise ProbeUnresolved(
            f"{probe['path']}: {wanted_class} has no field {wanted_field}"
        )
    raise ProbeUnresolved(f"{probe['path']}: no class named {wanted_class}")


def probe_regex(root: Path, probe: dict[str, Any]) -> Any:
    path = root / probe["path"]
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ProbeUnresolved(f"{probe['path']}: {exc}") from exc
    matches = re.findall(probe["pattern"], text)
    if not matches:
        raise ProbeUnresolved(f"{probe['path']}: pattern matched nothing")
    if len(matches) > 1:
        raise ProbeUnresolved(f"{probe['path']}: pattern matched {len(matches)} sites")
    raw = matches[0]
    try:
        return int(raw)
    except ValueError:
        try:
            return float(raw)
        except ValueError:
            return raw


PROBES: dict[str, Callable[[Path, dict[str, Any]], Any]] = {
    "module_constant": probe_module_constant,
    "class_field_default": probe_class_field_default,
    "regex": probe_regex,
}


def symbol_present(root: Path, relative: str, symbol: str) -> bool:
    try:
        text = (root / relative).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return False
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])", text) is not None


# ─────────────────────────────────────────────────────────────────────────────
# Marker discovery
# ─────────────────────────────────────────────────────────────────────────────
def scan_markers(root: Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    owners: dict[str, list[str]] = {}
    policies: dict[str, list[str]] = {}
    for current, directories, files in os.walk(root):
        directories[:] = [d for d in directories if d not in SKIPPED_DIRS]
        for name in files:
            path = Path(current) / name
            if path.suffix not in SCANNED_SUFFIXES:
                continue
            relative = path.relative_to(root).as_posix()
            if relative.startswith(SKIPPED_PREFIXES) or relative == str(REGISTRY):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            for surface_id in MARKER_RE.findall(text):
                owners.setdefault(surface_id, []).append(relative)
            for policy_id in POLICY_RE.findall(text):
                policies.setdefault(policy_id, []).append(relative)
    return owners, policies


# ─────────────────────────────────────────────────────────────────────────────
# Registry structure
# ─────────────────────────────────────────────────────────────────────────────
def load_registry(root: Path) -> tuple[dict[str, Any] | None, Result]:
    path = root / REGISTRY
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        return None, cno(f"registry unreadable: {exc}")
    except json.JSONDecodeError as exc:
        return None, fail(f"registry is not valid JSON: {exc}")
    if not isinstance(document, dict) or not isinstance(document.get("surfaces"), list):
        return None, fail("registry must be an object carrying a surfaces array")
    if not document["surfaces"]:
        return None, fail("registry declares zero surfaces")
    return document, ok()


def entry_errors(entry: Any, root: Path) -> Result:
    if not isinstance(entry, dict):
        return fail("a registry entry is not an object")
    sid = entry.get("surface_id")
    if not isinstance(sid, str) or not sid:
        return fail("a registry entry has no surface_id")

    result = ok()
    for name in COMMON_FIELDS:
        value = entry.get(name)
        if value in (None, "", [], {}):
            result = result.merge(fail(f"{sid}: missing required field {name}"))

    classification = entry.get("classification")
    if classification not in CLASSIFICATIONS:
        # A missing or unknown classification is non-compliant by the law, and
        # nothing downstream may treat it as one of the three contracts.
        return result.merge(fail(f"{sid}: classification is missing or unknown"))

    status = entry.get("status")
    if status not in OBSERVATIONS:
        result = result.merge(fail(f"{sid}: status must be one of {OBSERVATIONS}"))
    elif status == "could-not-observe":
        result = result.merge(cno(f"{sid}: surface status is could-not-observe"))
    elif status == "observed-bad":
        result = result.merge(fail(f"{sid}: surface status is observed-bad"))

    behaviours = entry.get("on_limit_behavior")
    if not isinstance(behaviours, list) or not behaviours:
        result = result.merge(fail(f"{sid}: no deterministic behaviour at the boundary"))
    else:
        for behaviour in behaviours:
            if behaviour not in OVERFLOW_VOCABULARY:
                result = result.merge(
                    fail(f"{sid}: unsupported overflow behaviour {behaviour!r}")
                )

    if classification == "EXPLICIT_BOUND":
        result = result.merge(explicit_bound_errors(entry, root))
    elif classification == "DERIVED_BOUND":
        derivation = entry.get("derivation")
        if not isinstance(derivation, dict):
            result = result.merge(fail(f"{sid}: derived bound has no derivation"))
        else:
            parents = derivation.get("parent_surface_ids")
            if not isinstance(parents, list) or not parents:
                result = result.merge(
                    fail(f"{sid}: derived bound names no authoritative parent")
                )
            if not str(derivation.get("expression") or "").strip():
                result = result.merge(fail(f"{sid}: derivation is not recorded"))
    else:
        result = result.merge(safe_unbounded_errors(entry))

    return result


def explicit_bound_errors(entry: dict[str, Any], root: Path) -> Result:
    sid = entry["surface_id"]
    limit = entry.get("limit")
    if not isinstance(limit, dict):
        return fail(f"{sid}: explicit bound carries no limit")
    if not str(limit.get("unit") or "").strip():
        return fail(f"{sid}: explicit bound has no unit")

    probe = limit.get("probe")
    caller_supplied = bool(limit.get("caller_supplied"))
    value = limit.get("value")

    if probe is None and not caller_supplied:
        return fail(
            f"{sid}: explicit bound is neither probed in source nor declared "
            f"caller-supplied, so nothing connects it to its owner"
        )

    result = ok()
    if caller_supplied:
        reference = limit.get("enforcement_ref")
        if not isinstance(reference, str) or not reference:
            result = result.merge(
                fail(f"{sid}: caller-supplied bound names no enforcement reference")
            )
        elif not symbol_present(root, entry["owner_path"], reference):
            result = result.merge(
                fail(
                    f"{sid}: enforcement reference {reference!r} is not present in "
                    f"{entry['owner_path']}"
                )
            )

    if probe is not None:
        if not isinstance(probe, dict) or probe.get("kind") not in PROBES:
            return result.merge(fail(f"{sid}: probe kind is missing or unsupported"))
        try:
            observed = PROBES[probe["kind"]](root, probe)
        except ProbeUnresolved as exc:
            return result.merge(cno(f"{sid}: limit could not be read from source: {exc}"))
        if isinstance(observed, bool) or not isinstance(observed, (int, float)):
            return result.merge(fail(f"{sid}: probed bound {observed!r} is not numeric"))
        if observed == 0 and not str(limit.get("zero_meaning") or "").strip():
            return result.merge(fail(f"{sid}: a zero bound needs an explicit meaning"))
        if observed < 0:
            return result.merge(fail(f"{sid}: probed bound is negative"))
        if value != observed:
            result = result.merge(
                fail(
                    f"{sid}: registry records {value!r} but the owner enforces "
                    f"{observed!r}; declare the boundedness delta"
                )
            )
    elif value is not None and not isinstance(value, (int, float)):
        result = result.merge(fail(f"{sid}: declared limit value is not numeric"))
    return result


def safe_unbounded_errors(entry: dict[str, Any]) -> Result:
    sid = entry["surface_id"]
    result = ok()
    for name in SAFE_FIELDS:
        text = entry.get(name)
        if not isinstance(text, str) or len(text.strip()) < 40:
            result = result.merge(
                fail(f"{sid}: SAFE_UNBOUNDED needs a concrete {name}")
            )
            continue
        normalized = " ".join(text.lower().split())
        for excuse in INSUFFICIENT_JUSTIFICATION:
            if excuse not in normalized:
                continue
            # The law refuses these as justifications, not as words. A field
            # that argues AROUND one still says something; a field that is one
            # of them plus padding says nothing, however long it is.
            remainder = normalized.replace(excuse, " ").strip(" .,;:-")
            if len(remainder) < 25:
                result = result.merge(
                    fail(f"{sid}: {name} is one of the excuses the law refuses")
                )
    return result


def coverage_errors(document: dict[str, Any], root: Path) -> Result:
    result = ok()
    surfaces = [s for s in document["surfaces"] if isinstance(s, dict)]
    ids = [s.get("surface_id") for s in surfaces]

    seen: set[str] = set()
    for sid in ids:
        if sid in seen:
            result = result.merge(fail(f"duplicate surface id: {sid}"))
        seen.add(sid)

    owners: dict[str, str] = {}
    for surface in surfaces:
        owner = surface.get("owner")
        sid = surface.get("surface_id")
        if isinstance(owner, str) and owner in owners:
            result = result.merge(
                fail(f"competing owners: {owners[owner]} and {sid} both own {owner}")
            )
        elif isinstance(owner, str):
            owners[owner] = str(sid)

    markers, policies = scan_markers(root)

    for surface_id, paths in markers.items():
        if surface_id not in seen:
            result = result.merge(
                fail(f"source marker without a registry entry: {surface_id} in {paths[0]}")
            )
        if len(paths) > 1:
            result = result.merge(
                fail(f"duplicate source marker for {surface_id}: {sorted(paths)}")
            )

    for surface in surfaces:
        sid = str(surface.get("surface_id"))
        owner_path = surface.get("owner_path")
        if not isinstance(owner_path, str):
            continue
        if not (root / owner_path).exists():
            result = result.merge(
                fail(f"{sid}: owner source {owner_path} does not exist")
            )
            continue
        declared = markers.get(sid)
        if not declared:
            result = result.merge(
                fail(f"registry entry without a source marker: {sid}")
            )
        elif owner_path not in declared:
            result = result.merge(
                fail(f"{sid}: marker lives in {declared} but the owner is {owner_path}")
            )
        for reference in surface.get("source_refs") or []:
            if not (root / str(reference)).exists():
                result = result.merge(fail(f"{sid}: source ref {reference} is missing"))

    referenced_policies = {
        str(s.get("policy_identity")) for s in surfaces
    }
    for policy_id, paths in policies.items():
        if policy_id not in referenced_policies:
            result = result.merge(
                fail(f"policy declaration nothing references: {policy_id} in {paths[0]}")
            )
        if len(paths) > 1:
            result = result.merge(
                fail(f"duplicate policy declaration for {policy_id}: {sorted(paths)}")
            )

    by_id = {str(s.get("surface_id")): s for s in surfaces}
    for surface in surfaces:
        if surface.get("classification") != "DERIVED_BOUND":
            continue
        sid = str(surface.get("surface_id"))
        derivation = surface.get("derivation") or {}
        for parent in derivation.get("parent_surface_ids") or []:
            if parent == sid:
                result = result.merge(fail(f"{sid}: derivation cites itself"))
            elif parent not in by_id:
                result = result.merge(
                    fail(f"{sid}: derivation cites unknown parent {parent}")
                )
            elif by_id[parent].get("classification") == "SAFE_UNBOUNDED":
                result = result.merge(
                    fail(f"{sid}: derived from an unbounded parent {parent}")
                )
    return result


def justification_anchor_errors(document: dict[str, Any], root: Path) -> Result:
    """A SAFE_UNBOUNDED entry whose oversight path vanished is not justified."""
    result = ok()
    try:
        recovery = (root / RECOVERY).read_text(encoding="utf-8").lower()
    except (OSError, UnicodeError) as exc:
        return cno(f"recovery runbook unreadable: {exc}")
    try:
        ignored = (root / GITIGNORE).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return cno(f"gitignore unreadable: {exc}")

    needs_reclaim = [
        s for s in document["surfaces"]
        if isinstance(s, dict) and s.get("classification") == "SAFE_UNBOUNDED"
        and "recovery.md" in str(s.get("archive_strategy", "")).lower()
    ]
    if needs_reclaim and "reclaiming the trace journal" not in recovery:
        result = result.merge(
            fail(
                "the reclaim procedure named by a SAFE_UNBOUNDED justification is "
                "missing from docs/operations/RECOVERY.md"
            )
        )
    # Only an ACTIVE rule ignores anything; a commented-out rule reads exactly
    # like a live one to a naive substring search.
    active = [
        line.strip() for line in ignored.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for path in ("sssf.db", "adws/adw_data/sessions/", ".sandbox/"):
        if not any(path in rule for rule in active):
            result = result.merge(
                fail(f"a SAFE_UNBOUNDED journal path stopped being gitignored: {path}")
            )
    if not symbol_present(root, "sandbox_mount/host/run_record.py", "raise"):
        result = result.merge(
            fail("run_record.list_runs no longer raises on an unreadable record")
        )
    return result


def protocol_errors(root: Path) -> Result:
    """The increment protocol must REQUIRE a boundedness delta, and every
    increment must carry one naming only surfaces the registry knows."""
    result = ok()
    try:
        protocol = (root / PROTOCOL).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return cno(f"increment protocol unreadable: {exc}")
    if DELTA_KEY not in protocol:
        return fail("the increment protocol does not require a boundedness delta")

    document, load = load_registry(root)
    if document is None:
        return result.merge(load)
    known = {str(s.get("surface_id")) for s in document["surfaces"] if isinstance(s, dict)}

    directory = root / INCREMENTS
    if not directory.is_dir():
        return result.merge(cno("increment directory is missing"))
    documents = sorted(directory.glob("*.md"))
    if not documents:
        return result.merge(cno("increment directory holds no increments"))

    for path in documents:
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            result = result.merge(cno(f"{relative}: unreadable ({exc})"))
            continue
        block = declared_delta_block(text)
        if block is None:
            result = result.merge(fail(f"{relative}: declares no {DELTA_KEY}"))
            continue
        head = block.split(DELTA_KEY, 1)[1]
        if re.match(r"\s*:\s*none", head):
            if "boundedness_reason" not in head:
                result = result.merge(
                    fail(f"{relative}: {DELTA_KEY}: none without a reason")
                )
            continue
        cited = set(re.findall(r"sssf\.[A-Za-z0-9._-]+", head))
        if not cited:
            result = result.merge(
                fail(f"{relative}: {DELTA_KEY} names neither surfaces nor none")
            )
        for surface_id in sorted(cited - known):
            result = result.merge(
                fail(f"{relative}: {DELTA_KEY} cites unknown surface {surface_id}")
            )
    return result


def declared_delta_block(text: str) -> str | None:
    """Return the fenced block that declares the delta, or None.

    A declaration only counts inside a fenced block, which is the form
    docs/development/INCREMENT_PROTOCOL.md requires. Prose that merely names
    the key — a spec quoting `boundedness_delta: none`, a review note
    discussing one — is a mention, not a declaration, and an increment whose
    only occurrence is prose has not declared anything.
    """
    fences = re.findall(r"^```[^\n]*\n(.*?)^```", text, re.S | re.M)
    for block in fences:
        if re.search(rf"^\s*{re.escape(DELTA_KEY)}\s*:", block, re.M):
            return block
    return None


def ci_registration_errors(root: Path) -> Result:
    try:
        manifest = json.loads((root / CI_MANIFEST).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        return cno(f"CI manifest unreadable: {exc}")
    except json.JSONDecodeError as exc:
        return fail(f"CI manifest is not valid JSON: {exc}")
    for check in manifest.get("checks") or []:
        if isinstance(check, dict) and check.get("id") == BOUNDEDNESS_CHECK_ID:
            command = [str(part) for part in check.get("command") or []]
            if any("check_boundedness.py" in part for part in command):
                return ok()
            return fail("the registered boundedness check does not run this validator")
    return fail("required CI does not run the boundedness validator")


def law_errors(root: Path) -> Result:
    try:
        law = (root / LAW).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return cno(f"boundedness law unreadable: {exc}")
    required = (
        "EXPLICIT_BOUND", "DERIVED_BOUND", "SAFE_UNBOUNDED",
        "Missing classification is non-compliant",
    )
    missing = [fragment for fragment in required if fragment not in law]
    if missing:
        return fail(f"the governing law no longer states: {missing}")
    return ok()


def registry_errors(root: Path = ROOT) -> Result:
    document, load = load_registry(root)
    if document is None:
        return load
    result = load
    for entry in document["surfaces"]:
        result = result.merge(entry_errors(entry, root))
    result = result.merge(coverage_errors(document, root))
    result = result.merge(justification_anchor_errors(document, root))
    return result


def static_errors(root: Path = ROOT) -> Result:
    return (
        registry_errors(root)
        .merge(protocol_errors(root))
        .merge(ci_registration_errors(root))
        .merge(law_errors(root))
    )


# ─────────────────────────────────────────────────────────────────────────────
# Live boundary proof: limit - 1, limit, limit + 1 against the real owners
# ─────────────────────────────────────────────────────────────────────────────
from adws.adw_modules import permissions  # noqa: E402
from adws.adw_modules.sandbox_provider import (  # noqa: E402
    EffectNotAuthorized,
    InMemoryDestroyAuthorizationStateStore,
    JsonFileAuthorizationStateStore,
    ResourceBounds,
)
from adws.adw_modules.subprocess_supervisor import (  # noqa: E402
    AttemptBudget,
    BoundedJournalWriter,
    BoundedStreamCapture,
    ChildDeadline,
    SupervisorRequest,
    _validate,
)
from tools import ci_gate  # noqa: E402
from tools import evidence_manifest  # noqa: E402
from tools import windows_host  # noqa: E402

sys.path.insert(0, str(ROOT / "docs" / "validation"))
import check_planning_foundation  # noqa: E402


class _Run:
    """The three attributes `permissions` reads. Nothing spawns."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root


def bounded_stream_capture_boundary() -> Result:
    """limit - 1 retains, limit retains exactly, limit + 1 truncates loudly."""
    result = ok()
    capture = BoundedStreamCapture(8)
    capture.feed(b"1234567")
    if capture.truncated or len(capture.data) != 7:
        result = result.merge(fail("bounded capture: limit - 1 did not retain whole"))
    capture = BoundedStreamCapture(8)
    capture.feed(b"12345678")
    if capture.truncated or len(capture.data) != 8:
        result = result.merge(fail("bounded capture: limit did not retain exactly"))
    capture = BoundedStreamCapture(8)
    capture.feed(b"123456789")
    status = capture.status()
    if not capture.truncated:
        result = result.merge(fail("bounded capture: limit + 1 did not overflow"))
    if len(capture.data) != 8:
        result = result.merge(fail("bounded capture: limit + 1 retained past the limit"))
    if status["bytes_seen"] != 9 or status["retained_bytes"] != 8:
        result = result.merge(
            fail("bounded capture: overflow status did not carry both counts")
        )
    if status["on_limit_behavior"] != "TRUNCATE_WITH_EXPLICIT_STATUS":
        result = result.merge(fail("bounded capture: boundary behaviour is undeclared"))
    for invalid in (0, -1, True, "8"):
        try:
            BoundedStreamCapture(invalid)  # type: ignore[arg-type]
        except ValueError:
            continue
        result = result.merge(
            fail(f"bounded capture: accepted an invalid ceiling {invalid!r}")
        )
    return result


def bounded_journal_boundary() -> Result:
    """The journal stops at its ceiling and SAYS it stopped."""
    result = ok()
    line = "x" * 9 + "\n"  # ten bytes
    for limit, admits, label in ((11, True, "limit - 1"), (10, True, "limit")):
        handle = io.StringIO()
        journal = BoundedJournalWriter(handle, limit)
        if journal.append(line) is not admits:
            result = result.merge(fail(f"bounded journal: {label} was not admitted"))
        if journal.truncated:
            result = result.merge(fail(f"bounded journal: {label} truncated early"))
        if BoundedJournalWriter.TRUNCATION_TYPE in handle.getvalue():
            result = result.merge(
                fail(f"bounded journal: {label} wrote a truncation record")
            )
    handle = io.StringIO()
    journal = BoundedJournalWriter(handle, 9)
    if journal.append(line):
        result = result.merge(fail("bounded journal: limit + 1 was admitted"))
    written = handle.getvalue()
    if BoundedJournalWriter.TRUNCATION_TYPE not in written:
        result = result.merge(
            fail("bounded journal: limit + 1 stopped silently, with no terminal record")
        )
    if not journal.truncated or journal.seen != 10:
        result = result.merge(fail("bounded journal: status lost the bytes it refused"))
    if journal.append(line):
        result = result.merge(fail("bounded journal: kept admitting after the ceiling"))
    if written.count(BoundedJournalWriter.TRUNCATION_TYPE) != 1:
        result = result.merge(fail("bounded journal: repeated its terminal record"))
    for invalid in (0, -1, True):
        try:
            BoundedJournalWriter(io.StringIO(), invalid)  # type: ignore[arg-type]
        except ValueError:
            continue
        result = result.merge(fail(f"bounded journal: accepted ceiling {invalid!r}"))
    return result


def child_deadline_boundary() -> Result:
    """A deadline that fires cancels a real child and says so."""
    result = ok()
    for invalid in (0, -1.0, True):
        try:
            ChildDeadline(invalid)  # type: ignore[arg-type]
        except ValueError:
            continue
        result = result.merge(fail(f"child deadline: accepted {invalid!r} seconds"))

    import subprocess

    # Under the deadline: the child finishes on its own and is never cancelled.
    quick = subprocess.Popen([sys.executable, "-c", "pass"])
    deadline = ChildDeadline(30.0).arm(quick)
    quick.wait()
    deadline.cancel()
    if deadline.expired.is_set():
        result = result.merge(fail("child deadline: fired against a child that finished"))

    # Past the deadline: the child is stopped rather than left running.
    slow = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    expired = ChildDeadline(0.2).arm(slow)
    returncode = slow.wait()
    expired.cancel()
    if not expired.expired.is_set():
        result = result.merge(fail("child deadline: did not record its own expiry"))
    if returncode == 0:
        result = result.merge(fail("child deadline: the overrunning child exited clean"))
    if expired.status()["on_limit_behavior"] != "CANCEL":
        result = result.merge(fail("child deadline: boundary behaviour is undeclared"))
    return result


def attempt_budget_boundary() -> Result:
    result = ok()
    budget = AttemptBudget(3)
    claims = [budget.claim() for _ in range(3)]
    if claims != [1, 2, 3]:
        result = result.merge(fail(f"attempt budget: limit claims were {claims}"))
    if budget.claim() is not None:
        result = result.merge(fail("attempt budget: limit + 1 was granted"))
    if budget.used != 3:
        result = result.merge(fail("attempt budget: spent attempts were uncharged"))
    overrun = AttemptBudget(2)
    if overrun.charge_observed_native_attempts(3):
        result = result.merge(fail("attempt budget: an over-budget child reported clean"))
    if overrun.used != 3:
        result = result.merge(
            fail("attempt budget: over-budget attempts were erased to make it pass")
        )
    for invalid in (0, -1, True, 2.0):
        try:
            AttemptBudget(invalid)  # type: ignore[arg-type]
        except ValueError:
            continue
        result = result.merge(fail(f"attempt budget: accepted a total of {invalid!r}"))
    return result


def supervisor_required_ceiling_controls() -> Result:
    """A launch without a positive wall clock or output ceiling is refused."""
    result = ok()
    base = dict(
        argv=[sys.executable, "-c", "pass"],
        cwd=str(ROOT),
        environment={},
        environment_allowlist=frozenset(),
    )
    if _validate(SupervisorRequest(timeout_seconds=1.0, **base)) is not None:
        result = result.merge(fail("supervisor: a bounded request was refused"))
    for label, request in (
        ("zero wall clock", SupervisorRequest(timeout_seconds=0.0, **base)),
        ("negative wall clock", SupervisorRequest(timeout_seconds=-1.0, **base)),
        ("zero stdout ceiling",
         SupervisorRequest(timeout_seconds=1.0, max_stdout_bytes=0, **base)),
        ("zero stderr ceiling",
         SupervisorRequest(timeout_seconds=1.0, max_stderr_bytes=0, **base)),
    ):
        if _validate(request) is None:
            result = result.merge(fail(f"supervisor: accepted a launch with a {label}"))
    return result


def preserve_capture_boundary() -> Result:
    """The permission capture stops at its aggregate ceiling and names what it left."""
    result = ok()
    with tempfile.TemporaryDirectory(prefix="sssf-bound-preserve-") as raw:
        repo = Path(raw)
        for index in range(4):
            (repo / f"f{index}.txt").write_bytes(b"a" * 100)
        (repo / "big.txt").write_bytes(b"b" * 4096)
        run = _Run(repo)
        tree = {f"f{index}.txt": "1,0" for index in range(4)}
        tree["big.txt"] = "1,0"

        original_file, original_total = (
            permissions.PRESERVE_MAX_BYTES, permissions.PRESERVE_TOTAL_MAX_BYTES
        )
        try:
            permissions.PRESERVE_MAX_BYTES = 1000
            for total, expected_kept, label in (
                (299, 2, "limit - 1"), (300, 3, "limit"), (301, 3, "limit + 1"),
            ):
                permissions.PRESERVE_TOTAL_MAX_BYTES = total
                kept, declined = permissions.preserve(run, tree)
                if len(kept) != expected_kept:
                    result = result.merge(
                        fail(
                            f"preserve: {label} kept {len(kept)} paths, expected "
                            f"{expected_kept}"
                        )
                    )
                if "big.txt" not in declined:
                    result = result.merge(
                        fail(f"preserve: {label} did not name the oversized path")
                    )
                if sorted(set(kept) | set(declined)) != sorted(tree):
                    result = result.merge(
                        fail(f"preserve: {label} lost a path from the accounting")
                    )
            permissions.PRESERVE_TOTAL_MAX_BYTES = 10 ** 9
            kept, declined = permissions.preserve(run, tree)
            if declined != ["big.txt"] or len(kept) != 4:
                result = result.merge(
                    fail("preserve: the per-file ceiling stopped being enforced")
                )
        finally:
            permissions.PRESERVE_MAX_BYTES = original_file
            permissions.PRESERVE_TOTAL_MAX_BYTES = original_total
    return result


def recovered_allowance_boundary() -> Result:
    """RECOVERED_LIMIT recovered writes are forgiven; one more is not."""
    if permissions.RECOVERED_LIMIT != 3:
        return fail("recovered allowance: the registry-bound ceiling moved")
    outcomes_at_limit = {f"p{i}": "deleted" for i in range(permissions.RECOVERED_LIMIT)}
    outcomes_past = {f"p{i}": "deleted" for i in range(permissions.RECOVERED_LIMIT + 1)}
    forgiving = lambda outcomes: (  # noqa: E731 - mirrors enforce()'s own test
        not [p for p, o in outcomes.items() if o not in permissions.RECOVERED]
        and len(outcomes) <= permissions.RECOVERED_LIMIT
    )
    result = ok()
    if not forgiving(outcomes_at_limit):
        result = result.merge(fail("recovered allowance: the limit case was not forgiven"))
    if forgiving(outcomes_past):
        result = result.merge(fail("recovered allowance: limit + 1 was forgiven"))
    unrecoverable = {"p0": "REVERTED-BY-AGENT (uncommitted work lost, cannot restore)"}
    if forgiving(unrecoverable):
        result = result.merge(
            fail("recovered allowance: an unrecoverable write was forgiven")
        )
    return result


def phase_error_boundary() -> Result:
    """A clipped failure message must say that it was clipped."""
    source = (ROOT / "adws" / "adw_modules" / "runner.py").read_text(encoding="utf-8")
    namespace: dict[str, Any] = {}
    body = source[source.index("PHASE_ERROR_MAX_CHARS"): source.index("class PhaseHandle")]
    exec(compile(body, "<runner-bound>", "exec"), namespace)  # noqa: S102
    limit = namespace["PHASE_ERROR_MAX_CHARS"]
    bounded = namespace["_bounded_error"]
    result = ok()
    for length, label in ((limit - 1, "limit - 1"), (limit, "limit")):
        text = "e" * length
        if bounded(text) != text:
            result = result.merge(fail(f"phase error: {label} was altered"))
    overrun = bounded("e" * (limit + 1))
    if len(overrun) > limit:
        result = result.merge(fail("phase error: limit + 1 exceeded the ceiling"))
    if "truncated" not in overrun or str(limit + 1) not in overrun:
        result = result.merge(
            fail("phase error: limit + 1 was clipped without saying so")
        )
    return result


def in_memory_store_boundary() -> Result:
    """The lifecycle stores refuse rather than growing without end."""
    result = ok()
    store = InMemoryDestroyAuthorizationStateStore()
    ceiling = store.MAX_AUTHORIZATIONS
    digest = "a" * 64
    try:
        store.MAX_AUTHORIZATIONS = 3  # type: ignore[misc]
        for index in range(3):
            store.record_issuance(f"auth-{index}", digest)
        if len(store._state) != 3:
            result = result.merge(fail("authorization store: the limit case was refused"))
        try:
            store.record_issuance("auth-3", digest)
        except ValueError:
            pass
        else:
            result = result.merge(fail("authorization store: limit + 1 was admitted"))
        store.record_issuance("auth-1", digest)  # idempotent, already present
    finally:
        store.MAX_AUTHORIZATIONS = ceiling  # type: ignore[misc]
    return result


def resource_bounds_controls() -> Result:
    """Zero is never an implicit unlimited value on a provider ceiling."""
    result = ok()
    if ResourceBounds().network_bytes != 0:
        result = result.merge(fail("resource bounds: the network denial default moved"))
    for name in ("cpu_millis", "memory_bytes", "pids", "disk_bytes"):
        for invalid in (0, -1):
            try:
                ResourceBounds(**{name: invalid})
            except ValueError:
                continue
            result = result.merge(
                fail(f"resource bounds: accepted {name}={invalid} as unlimited")
            )
    for invalid in (0, -1.0):
        try:
            ResourceBounds(wall_seconds=invalid)
        except ValueError:
            continue
        result = result.merge(fail(f"resource bounds: accepted wall_seconds={invalid}"))
    try:
        ResourceBounds(network_bytes=-1)
    except ValueError:
        pass
    else:
        result = result.merge(fail("resource bounds: accepted a negative network budget"))
    return result


def ci_gate_output_boundary() -> Result:
    """A check that prints past the ceiling is clipped, and the evidence says so."""
    result = ok()
    limit = ci_gate.CHECK_MAX_OUTPUT_BYTES
    for size, truncated, label in (
        (limit - 1, False, "limit - 1"), (limit, False, "limit"),
        (limit + 1, True, "limit + 1"),
    ):
        capture = ci_gate._BoundedOutput(limit)
        capture.feed(b"z" * size)
        if capture.truncated is not truncated:
            result = result.merge(
                fail(f"ci gate output: {label} truncation was {capture.truncated}")
            )
        if capture.seen != size:
            result = result.merge(fail(f"ci gate output: {label} lost the seen count"))
    capture = ci_gate._BoundedOutput(16)
    capture.feed(b"y" * 40)
    rendered = capture.text()
    if "[bounded]" not in rendered or "40 bytes seen" not in rendered:
        result = result.merge(
            fail("ci gate output: a clipped log did not state that it was clipped")
        )
    for invalid in (0, -1, True):
        try:
            ci_gate._BoundedOutput(invalid)  # type: ignore[arg-type]
        except ValueError:
            continue
        result = result.merge(fail(f"ci gate output: accepted ceiling {invalid!r}"))
    if not 1 <= ci_gate.TIMEOUT_MIN_SECONDS <= ci_gate.TIMEOUT_MAX_SECONDS:
        result = result.merge(fail("ci gate: the timeout range is not a range"))
    return result


def evidence_ceiling_boundary() -> Result:
    """Oversized artifacts and over-deep paths are REFUSED, never digested short."""
    result = ok()
    byte_limit = evidence_manifest.MAX_ARTIFACT_BYTES
    depth_limit = evidence_manifest.MAX_ARTIFACT_PATH_DEPTH
    if byte_limit < 1 or depth_limit < 1:
        return fail("evidence ceilings: a ceiling is not positive")

    original = byte_limit
    with tempfile.TemporaryDirectory(prefix="sssf-bound-evidence-") as raw:
        root = Path(raw)
        for size, expect_refusal, label in (
            (7, False, "limit - 1"), (8, False, "limit"), (9, True, "limit + 1"),
        ):
            target = root / f"a{size}.bin"
            target.write_bytes(b"q" * size)
            evidence_manifest.MAX_ARTIFACT_BYTES = 8
            try:
                refused = False
                try:
                    evidence_manifest._read_frozen_artifact(root, target.name)
                except evidence_manifest.ArtifactRefusal as refusal:
                    refused = True
                    if "read ceiling" not in str(refusal):
                        result = result.merge(
                            fail(f"evidence ceilings: {label} refused for another reason")
                        )
                if refused is not expect_refusal:
                    result = result.merge(
                        fail(f"evidence ceilings: {label} refusal was {refused}")
                    )
            finally:
                evidence_manifest.MAX_ARTIFACT_BYTES = original

        deep = "/".join(["d"] * (depth_limit + 1)) + "/leaf.txt"
        try:
            evidence_manifest._read_frozen_artifact(root, deep)
        except evidence_manifest.ArtifactRefusal as refusal:
            if "depth" not in str(refusal):
                result = result.merge(
                    fail("evidence ceilings: an over-deep path refused for another reason")
                )
        else:
            result = result.merge(fail("evidence ceilings: an over-deep path was accepted"))
    return result



def durable_authority_store_boundary() -> Result:
    """The store that actually gates live effects refuses past its ceiling.

    The in-memory sibling has always REJECTed; this is the durable one, whose
    file is re-read whole on every verify. The limit case must still be
    admitted, and the limit + 1 case must be a positively observed refusal
    rather than an eviction, because evicting a spent authorization restores
    its identity to "never seen".
    """
    result = ok()
    digest = "a" * 64
    # Both identities are SHA-256 digests in this store, so the fixture uses
    # real ones rather than readable names the owner would rightly refuse.
    identity = [f"{index:064x}" for index in range(4)]
    with tempfile.TemporaryDirectory() as directory:
        store = JsonFileAuthorizationStateStore(Path(directory) / "authority.json")
        store.MAX_AUTHORIZATIONS = 3  # instance ceiling; the class default stands
        for index in range(2):
            store.record_issuance(identity[index], digest)
        if not store.verifies(identity[1], digest):
            result = result.merge(fail("durable authority: limit - 1 was refused"))
        store.record_issuance(identity[2], digest)
        if not store.verifies(identity[2], digest):
            result = result.merge(fail("durable authority: the limit case was refused"))
        try:
            store.record_issuance(identity[3], digest)
        except EffectNotAuthorized as exc:
            if "full" not in str(exc):
                result = result.merge(
                    fail("durable authority: the refusal did not name the ceiling")
                )
        else:
            result = result.merge(fail("durable authority: limit + 1 was admitted"))
        # A full store must not have quietly dropped anyone to make room.
        for index in range(3):
            if not store.verifies(identity[index], digest):
                result = result.merge(
                    fail(f"durable authority: entry {index} was evicted at the ceiling")
                )
        # An identity already recorded stays usable at the ceiling, so a live
        # effect is never orphaned by a store that filled up behind it.
        store.record_issuance(identity[1], digest)
        if not store.compare_and_swap_reserved(identity[1], digest):
            result = result.merge(
                fail("durable authority: a recorded identity could not proceed when full")
            )
    return result


def _stub_git(directory: Path, body: str) -> dict[str, str]:
    """A PATH holding one fake `git`, so the real read meets a real child."""
    (directory / "stub.py").write_text(body, encoding="utf-8")
    if os.name == "nt":
        launcher = directory / "git.bat"
        launcher.write_text(
            f'@echo off\r\n"{sys.executable}" "{directory / "stub.py"}" %*\r\n',
            encoding="utf-8",
        )
    else:
        launcher = directory / "git"
        launcher.write_text(
            f'#!/bin/sh\nexec "{sys.executable}" "{directory / "stub.py"}" "$@"\n',
            encoding="utf-8",
        )
        launcher.chmod(0o755)
    environment = dict(os.environ)
    environment["PATH"] = str(directory) + os.pathsep + environment.get("PATH", "")
    return environment


def planning_git_read_boundary() -> Result:
    """A git read that overruns its bytes or its deadline answers nothing.

    Truncating would be worse than refusing here: the planning validator turns
    these bytes into authority identities, and a prefix of a ref list is
    indistinguishable from a complete shorter one.
    """
    result = ok()
    module = check_planning_foundation
    limit, deadline = module.GIT_OUTPUT_MAX_BYTES, module.GIT_OUTPUT_TIMEOUT_SECONDS
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        return fail("planning git read: the byte ceiling is not a positive integer")
    if not isinstance(deadline, float) or deadline <= 0:
        return fail("planning git read: the deadline is not a positive number")

    original_environment = dict(os.environ)
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        try:
            module.GIT_OUTPUT_MAX_BYTES = 64
            body = (
                "import os, sys\n"
                "sys.stdout.buffer.write(b'z' * int(os.environ['STUB_BYTES']))\n"
            )
            environment = _stub_git(root, body)
            os.environ.clear()
            os.environ.update(environment)
            for size, expected, label in (
                (63, "z" * 63, "limit - 1"),
                (64, "z" * 64, "limit"),
                (65, None, "limit + 1"),
            ):
                os.environ["STUB_BYTES"] = str(size)
                observed = module._git_output(root, "rev-parse", "HEAD")
                if observed != expected:
                    detail = (
                        "returned a truncated value"
                        if expected is None
                        else "answered nothing for an in-bound read"
                    )
                    result = result.merge(
                        fail(f"planning git read: {label} {detail}")
                    )
        finally:
            module.GIT_OUTPUT_MAX_BYTES = limit
            os.environ.clear()
            os.environ.update(original_environment)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        try:
            module.GIT_OUTPUT_TIMEOUT_SECONDS = 0.4
            environment = _stub_git(root, "import time\ntime.sleep(120)\n")
            os.environ.clear()
            os.environ.update(environment)
            started = time.monotonic()
            observed = module._git_output(root, "rev-parse", "HEAD")
            elapsed = time.monotonic() - started
            if observed is not None:
                result = result.merge(
                    fail("planning git read: an overrunning read still answered")
                )
            if elapsed > 30:
                result = result.merge(
                    fail(f"planning git read: the deadline did not fire ({elapsed:.1f}s)")
                )
        finally:
            module.GIT_OUTPUT_TIMEOUT_SECONDS = deadline
            os.environ.clear()
            os.environ.update(original_environment)
    return result


def windows_host_child_output_boundary() -> Result:
    """A doctor child that prints past the ceiling is clipped, and says so."""
    result = ok()
    ceiling = windows_host.CHILD_MAX_OUTPUT_BYTES
    if not isinstance(ceiling, int) or isinstance(ceiling, bool) or ceiling < 1:
        return fail("windows host child output: the ceiling is not a positive integer")
    try:
        windows_host.CHILD_MAX_OUTPUT_BYTES = 64
        for size, truncated, label in (
            (63, False, "limit - 1"), (64, False, "limit"), (65, True, "limit + 1"),
        ):
            observation = windows_host.run(
                [
                    sys.executable,
                    "-c",
                    f"import sys; sys.stdout.write('z' * {size})",
                ]
            )
            if observation.returncode != 0:
                result = result.merge(
                    fail(f"windows host child output: {label} child did not run")
                )
                continue
            clipped = "[bounded]" in observation.stdout
            if clipped is not truncated:
                result = result.merge(
                    fail(f"windows host child output: {label} clipping was {clipped}")
                )
            if truncated and f"{size} bytes seen" not in observation.stdout:
                result = result.merge(
                    fail(
                        "windows host child output: a clipped log did not state "
                        "how much it never kept"
                    )
                )
    finally:
        windows_host.CHILD_MAX_OUTPUT_BYTES = ceiling
    return result


BOUNDARY_CONTROLS: tuple[tuple[str, Callable[[], Result]], ...] = (
    ("bounded_stream_capture_boundary", bounded_stream_capture_boundary),
    ("bounded_journal_boundary", bounded_journal_boundary),
    ("child_deadline_boundary", child_deadline_boundary),
    ("attempt_budget_boundary", attempt_budget_boundary),
    ("supervisor_required_ceiling_controls", supervisor_required_ceiling_controls),
    ("preserve_capture_boundary", preserve_capture_boundary),
    ("recovered_allowance_boundary", recovered_allowance_boundary),
    ("phase_error_boundary", phase_error_boundary),
    ("in_memory_store_boundary", in_memory_store_boundary),
    ("resource_bounds_controls", resource_bounds_controls),
    ("ci_gate_output_boundary", ci_gate_output_boundary),
    ("evidence_ceiling_boundary", evidence_ceiling_boundary),
    ("durable_authority_store_boundary", durable_authority_store_boundary),
    ("planning_git_read_boundary", planning_git_read_boundary),
    ("windows_host_child_output_boundary", windows_host_child_output_boundary),
)


def boundary_errors() -> Result:
    result = ok()
    for name, control in BOUNDARY_CONTROLS:
        try:
            result = result.merge(control())
        except Exception as exc:  # a control that cannot run is CNO, not a pass
            result = result.merge(cno(f"{name} could not be observed: {exc!r}"))
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Watched red: each protection is watched going red on its own account
# ─────────────────────────────────────────────────────────────────────────────
COPIED_ROOTS = (
    "docs/reference/BOUNDEDNESS_REGISTRY.json",
    "docs/development/BOUNDEDNESS_LAW.md",
    "docs/development/INCREMENT_PROTOCOL.md",
    "docs/operations/RECOVERY.md",
    "ci/checks.json",
    ".gitignore",
)


def build_fixture_root(root: Path, destination: Path) -> None:
    """Copy exactly what the static checks read: the registry, the documents
    that anchor it, and every owner file it points at."""
    for relative in COPIED_ROOTS:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    (destination / "docs" / "increments").mkdir(parents=True, exist_ok=True)
    for path in (root / INCREMENTS).glob("*.md"):
        shutil.copy2(path, destination / "docs" / "increments" / path.name)
    document = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    for surface in document["surfaces"]:
        for relative in {surface["owner_path"], *surface.get("source_refs", [])}:
            target = destination / relative
            if target.exists():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, target)
    # The policy declarations live with the primitives; the marker sweep must
    # be able to find them in the fixture too.
    for relative in ("adws/adw_modules/subprocess_supervisor.py", "tools/ci_gate.py",
                     "sandbox_mount/host/run_record.py"):
        target = destination / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, target)


def read_fixture_registry(root: Path) -> dict[str, Any]:
    return json.loads((root / REGISTRY).read_text(encoding="utf-8"))


def write_fixture_registry(root: Path, document: dict[str, Any]) -> None:
    (root / REGISTRY).write_text(
        json.dumps(document, indent=2) + "\n", encoding="utf-8"
    )


def entry_of(document: dict[str, Any], surface_id: str) -> dict[str, Any]:
    for surface in document["surfaces"]:
        if surface["surface_id"] == surface_id:
            return surface
    raise KeyError(surface_id)


def first_of(document: dict[str, Any], classification: str) -> dict[str, Any]:
    for surface in document["surfaces"]:
        if surface["classification"] == classification:
            return surface
    raise KeyError(classification)


def mutate_source(root: Path, relative: str, old: str, new: str) -> None:
    path = root / relative
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"{relative}: expected exactly one {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# Each control names ONE property. A generic "the document changed" failure is
# explicitly not accepted as evidence for any of them.
def watched_red_controls() -> list[tuple[str, Callable[[Path], None], str]]:
    def removed_limit(root: Path) -> None:
        mutate_source(root, "adws/adw_modules/permissions.py",
                      "PRESERVE_TOTAL_MAX_BYTES = 64 << 20",
                      "PRESERVE_TOTAL_UNBOUNDED = 64 << 20")

    def raised_limit_without_delta(root: Path) -> None:
        mutate_source(root, "adws/adw_modules/permissions.py",
                      "PRESERVE_TOTAL_MAX_BYTES = 64 << 20",
                      "PRESERVE_TOTAL_MAX_BYTES = 640 << 20")

    def removed_retry_ceiling(root: Path) -> None:
        mutate_source(root, "adws/adw_modules/agents.py",
                      "JSON_FIX_ATTEMPTS = 2", "JSON_FIX_ATTEMPTS_DISABLED = 2")

    def removed_child_ceiling(root: Path) -> None:
        mutate_source(root, "adws/adw_modules/agent_pi.py",
                      "PI_TURN_MAX_SECONDS = 3600.0",
                      "PI_TURN_MAX_SECONDS_UNUSED = 3600.0")

    def disabled_retention(root: Path) -> None:
        text = (root / RECOVERY).read_text(encoding="utf-8")
        (root / RECOVERY).write_text(
            text.replace("## Reclaiming the trace journal", "## Removed"),
            encoding="utf-8",
        )

    def marker_without_entry(root: Path) -> None:
        path = root / "tools" / "obs_query.py"
        # Built rather than written out, so this validator's own source never
        # carries a literal marker the repository-wide sweep would then find.
        injected = f"\n# {OWNER_MARKER}: sssf.obs_query.invented_surface\n"
        path.write_text(path.read_text(encoding="utf-8") + injected, encoding="utf-8")

    def entry_without_owner(root: Path) -> None:
        document = read_fixture_registry(root)
        entry = entry_of(document, "sssf.console.line_length")
        entry["owner_path"] = "adws/adw_modules/console_renamed.py"
        write_fixture_registry(root, document)

    def entry_without_marker(root: Path) -> None:
        mutate_source(root, "adws/adw_modules/console.py",
                      f"# {OWNER_MARKER}: sssf.console.line_length\n", "")

    def duplicate_surface(root: Path) -> None:
        document = read_fixture_registry(root)
        document["surfaces"].append(dict(entry_of(document, "sssf.console.line_length")))
        write_fixture_registry(root, document)

    def duplicate_owner(root: Path) -> None:
        document = read_fixture_registry(root)
        clone = dict(entry_of(document, "sssf.console.line_length"))
        clone["surface_id"] = "sssf.console.line_length_clone"
        document["surfaces"].append(clone)
        write_fixture_registry(root, document)

    def missing_overflow(root: Path) -> None:
        document = read_fixture_registry(root)
        entry_of(document, "sssf.console.line_length")["on_limit_behavior"] = []
        write_fixture_registry(root, document)

    def missing_classification(root: Path) -> None:
        document = read_fixture_registry(root)
        del entry_of(document, "sssf.console.line_length")["classification"]
        write_fixture_registry(root, document)

    def invalid_safe_unbounded(root: Path) -> None:
        document = read_fixture_registry(root)
        first_of(document, "SAFE_UNBOUNDED")["safety_invariant"] = "storage is cheap"
        write_fixture_registry(root, document)

    def excuse_safe_unbounded(root: Path) -> None:
        document = read_fixture_registry(root)
        entry = first_of(document, "SAFE_UNBOUNDED")
        entry["why_no_finite_local_bound_is_required"] = (
            "The operator can clean it up......................................"
        )
        write_fixture_registry(root, document)

    def cno_narrowed_to_pass(root: Path) -> None:
        document = read_fixture_registry(root)
        entry_of(document, "sssf.console.line_length")["status"] = "could-not-observe"
        write_fixture_registry(root, document)

    def orphan_derivation(root: Path) -> None:
        document = read_fixture_registry(root)
        derived_entry = first_of(document, "DERIVED_BOUND")
        derived_entry["derivation"]["parent_surface_ids"] = ["sssf.no.such.parent"]
        write_fixture_registry(root, document)

    def unrecorded_derivation(root: Path) -> None:
        document = read_fixture_registry(root)
        first_of(document, "DERIVED_BOUND")["derivation"]["expression"] = "   "
        write_fixture_registry(root, document)

    def increment_without_delta(root: Path) -> None:
        target = next((root / INCREMENTS).glob("*.md"))
        target.write_text(
            target.read_text(encoding="utf-8").replace(DELTA_KEY, "coverage_note"),
            encoding="utf-8",
        )

    def protocol_without_delta(root: Path) -> None:
        path = root / PROTOCOL
        path.write_text(
            path.read_text(encoding="utf-8").replace(DELTA_KEY, "coverage_note"),
            encoding="utf-8",
        )

    def ci_deregistration(root: Path) -> None:
        path = root / CI_MANIFEST
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["checks"] = [
            check for check in manifest["checks"]
            if check.get("id") != BOUNDEDNESS_CHECK_ID
        ]
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def law_weakened(root: Path) -> None:
        path = root / LAW
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "Missing classification is non-compliant", "Classification is optional"
            ),
            encoding="utf-8",
        )

    def unignored_journal(root: Path) -> None:
        path = root / GITIGNORE
        path.write_text(
            path.read_text(encoding="utf-8").replace("sssf.db*", "# sssf.db*"),
            encoding="utf-8",
        )

    def zero_bound_without_meaning(root: Path) -> None:
        mutate_source(root, "adws/adw_modules/console.py", "MAX_LINE = 160",
                      "MAX_LINE = 0")

    def removed_durable_authority_ceiling(root: Path) -> None:
        # Anchored on the comment above it, because the in-memory sibling
        # carries a field of the same name and the same value.
        mutate_source(
            root, "adws/adw_modules/sandbox_provider.py",
            "    # docs/operations/RECOVERY.md.\n    MAX_AUTHORIZATIONS = 4096",
            "    # docs/operations/RECOVERY.md.\n    MAX_AUTHORIZATIONS_UNUSED = 4096",
        )

    def removed_planning_git_ceiling(root: Path) -> None:
        mutate_source(
            root, "docs/validation/check_planning_foundation.py",
            "GIT_OUTPUT_MAX_BYTES = ", "GIT_OUTPUT_MAX_BYTES_UNUSED = ",
        )

    def removed_planning_git_deadline(root: Path) -> None:
        mutate_source(
            root, "docs/validation/check_planning_foundation.py",
            "GIT_OUTPUT_TIMEOUT_SECONDS = ", "GIT_OUTPUT_TIMEOUT_SECONDS_UNUSED = ",
        )

    def removed_doctor_output_ceiling(root: Path) -> None:
        mutate_source(
            root, "tools/windows_host.py",
            "CHILD_MAX_OUTPUT_BYTES = ", "CHILD_MAX_OUTPUT_BYTES_UNUSED = ",
        )

    def delta_declared_only_in_prose(root: Path) -> None:
        # The protocol's form is a fenced block. Prose that merely names the
        # key is a mention, and an increment whose fences are gone has stopped
        # declaring anything even though the words are still there.
        path = root / INCREMENTS / "B1-001_AGENT_DOC_DISCOVERY.md"
        text = path.read_text(encoding="utf-8")
        head, _, tail = text.partition("```text\n" + DELTA_KEY)
        path.write_text(
            head + DELTA_KEY + tail.replace("```", "", 1), encoding="utf-8"
        )

    # Each row carries the fragment the finding MUST contain. A control that
    # goes red for some other reason has not proved the property it names, so a
    # generic "something changed" failure cannot stand in for any of these.
    return [
        ("removed limit", removed_limit,
         "sssf.permissions.preserve_total_bytes: limit could not be read"),
        ("limit raised without a declared delta", raised_limit_without_delta,
         "declare the boundedness delta"),
        ("removed retry ceiling", removed_retry_ceiling,
         "sssf.agents.json_fix_attempts: limit could not be read"),
        ("removed child wall-clock ceiling", removed_child_ceiling,
         "sssf.agent_pi.turn_wall_clock: limit could not be read"),
        ("disabled retention procedure", disabled_retention,
         "reclaim procedure named by a SAFE_UNBOUNDED justification is"),
        ("source marker without a registry entry", marker_without_entry,
         "source marker without a registry entry: sssf.obs_query.invented_surface"),
        ("registry entry without an existing owner source", entry_without_owner,
         "owner source adws/adw_modules/console_renamed.py does not exist"),
        ("registry entry without a source marker", entry_without_marker,
         "registry entry without a source marker: sssf.console.line_length"),
        ("duplicate surface identity", duplicate_surface,
         "duplicate surface id: sssf.console.line_length"),
        ("duplicate owner", duplicate_owner,
         "competing owners"),
        ("missing overflow behaviour", missing_overflow,
         "no deterministic behaviour at the boundary"),
        ("missing classification", missing_classification,
         "classification is missing or unknown"),
        ("invalid SAFE_UNBOUNDED justification", invalid_safe_unbounded,
         "SAFE_UNBOUNDED needs a concrete safety_invariant"),
        ("SAFE_UNBOUNDED resting on a refused excuse", excuse_safe_unbounded,
         "why_no_finite_local_bound_is_required is one of the excuses the law refuses"),
        ("CNO narrowed to PASS", cno_narrowed_to_pass,
         "sssf.console.line_length: surface status is could-not-observe"),
        ("derived bound with an orphaned parent", orphan_derivation,
         "derivation cites unknown parent sssf.no.such.parent"),
        ("derived bound with no recorded derivation", unrecorded_derivation,
         "derivation is not recorded"),
        ("increment without a boundedness delta", increment_without_delta,
         f"declares no {DELTA_KEY}"),
        ("protocol no longer requiring a delta", protocol_without_delta,
         "increment protocol does not require a boundedness delta"),
        ("boundedness validator removed from required CI", ci_deregistration,
         "required CI does not run the boundedness validator"),
        ("governing law weakened", law_weakened,
         "the governing law no longer states"),
        ("journal path no longer gitignored", unignored_journal,
         "SAFE_UNBOUNDED journal path stopped being gitignored: sssf.db"),
        ("zero bound with no declared meaning", zero_bound_without_meaning,
         "a zero bound needs an explicit meaning"),
        ("removed durable effect-authority ceiling", removed_durable_authority_ceiling,
         "sssf.sandbox.effect_authority_state_store: limit could not be read"),
        ("removed planning git byte ceiling", removed_planning_git_ceiling,
         "sssf.planning.git_output_capture: limit could not be read"),
        ("removed planning git deadline", removed_planning_git_deadline,
         "sssf.planning.git_wall_clock: limit could not be read"),
        ("removed doctor child output ceiling", removed_doctor_output_ceiling,
         "sssf.windows_host.child_output_capture: limit could not be read"),
        ("boundedness delta declared only in prose", delta_declared_only_in_prose,
         f"B1-001_AGENT_DOC_DISCOVERY.md: declares no {DELTA_KEY}"),
    ]


def watched_red_errors() -> Result:
    result = ok()
    with tempfile.TemporaryDirectory(prefix="sssf-bound-red-") as raw:
        base = Path(raw) / "base"
        base.mkdir()
        try:
            build_fixture_root(ROOT, base)
        except (OSError, KeyError, json.JSONDecodeError) as exc:
            return cno(f"watched-red fixture could not be built: {exc!r}")

        # The fixture must be green BEFORE any mutation, or every control below
        # would be red for a reason that has nothing to do with what it names.
        baseline = static_errors(base)
        if baseline.status != "PASS":
            return cno(
                "watched-red baseline fixture is not clean: "
                f"{baseline.status} {(baseline.failures + baseline.cnos)[:3]}"
            )

        for index, (label, mutate, expected) in enumerate(watched_red_controls()):
            case = Path(raw) / f"case-{index:02d}"
            shutil.copytree(base, case)
            try:
                mutate(case)
            except Exception as exc:
                result = result.merge(
                    cno(f"watched-red {label!r} could not be applied: {exc!r}")
                )
                continue
            observed = static_errors(case)
            if observed.status == "PASS":
                result = result.merge(fail(f"watched-red stayed green: {label}"))
                continue
            findings = observed.failures + observed.cnos
            if not any(expected in finding for finding in findings):
                result = result.merge(
                    fail(
                        f"watched-red {label!r} went red for another reason; "
                        f"expected a finding containing {expected!r}, observed "
                        f"{findings[:3]}"
                    )
                )
    return result


# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    result = static_errors(ROOT)
    if result.status != "FAIL":
        result = result.merge(boundary_errors())
    if result.status != "FAIL":
        result = result.merge(watched_red_errors())

    document, _ = load_registry(ROOT)
    surfaces = document["surfaces"] if document else []
    counts = {name: 0 for name in CLASSIFICATIONS}
    for surface in surfaces:
        classification = surface.get("classification")
        if classification in counts:
            counts[classification] += 1

    status = result.status
    print(f"BOUND-1 boundedness registry and enforcement: {status}")
    for message in result.failures:
        print(f"- FAIL {message}")
    for message in result.cnos:
        print(f"- CNO {message}")
    if status != "PASS":
        print("precedence: FAIL > CNO > PASS; a could-not-observe is never a pass")
        return 1 if status == "FAIL" else 2

    print(
        f"{len(surfaces)} governed growth surfaces: "
        f"{counts['EXPLICIT_BOUND']} explicit, {counts['DERIVED_BOUND']} derived, "
        f"{counts['SAFE_UNBOUNDED']} justified safe-unbounded"
    )
    print("coverage: source marker <-> registry entry is bidirectional and singular")
    print("bounds: every explicit limit is re-read from its owner's source by probe")
    print(
        f"boundary: limit-1/limit/limit+1 exercised across "
        f"{len(BOUNDARY_CONTROLS)} real enforcement owners"
    )
    print(
        f"watched-red: {len(watched_red_controls())} property-specific controls, "
        f"each watched going red against a clean baseline fixture"
    )
    print("increment protocol: every increment declares a boundedness delta")
    print("provider-calls: 0 (no network, provider, model, or browser side effect)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
