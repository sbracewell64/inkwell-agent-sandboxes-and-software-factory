#!/usr/bin/env python3
"""Mapped-surface parity between installable skill-template bytes and live bytes.

This is the parity owner. It is deliberately DISTINCT from
`check_adw_synchronization.py` (HD-02), which validates each surface's internal
CONTRACT SHAPE — imports resolve, every AgentCall names a concrete output type,
exactly one final `run.finish()`, prompt Report fields match their output model.
HD-02 never compares the two surfaces' content against each other and does not
claim to; that is this verifier's job, and the two must not be conflated because
their names sound similar.

The surfaces are NOT a subtree mirror. `install.py` stamps template paths to
DIFFERENT live paths, so a raw relative-path or `diff -rq` comparison reports
correctly-mapped trees as absent. `mapped_surface_contract.json` transcribes the
real mapping from install.py's stamp() calls and assigns every governed path one
typed relation:

  EXACT_MIRROR       mapped content identity required; fails closed
  CONTRACT_ONLY      bodies may differ, a NAMED verifier proves a NAMED property
  TEMPLATE_SCAFFOLD  template copy is a deliberate placeholder; any shared API
                     contract is still enforced by name
  USER_OWNED         stamped once, then owned by the target repo
  LIVE_ONLY          present live by design, never stamped

Three-valued:

  PASS  every governed path resolved to a declared relation and met it, over a
        nonempty comparison set, with the watched-red controls demonstrated.
  FAIL  an EXACT_MIRROR path diverged or lost a counterpart, a declared contract
        property broke, a coupled pair was split, or a governed path diverged
        with no declared relation.
  CNO   the question could not be asked: unreadable contract, missing root,
        vacuous comparison, an intentional-divergence declaration that is
        unreviewable or stale, an unclaimed exclusion, or watched-red controls
        that failed to demonstrate this verifier still fails.

Structured state (matched / intentional-divergence / drift / unresolved) is
printed as a JSON block and can be written with --state, so the mapped-surface
status is observable without reconstructing the install map from prose.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT = Path(__file__).resolve().parent / "mapped_surface_contract.json"

MATCHED = "matched"
INTENTIONAL = "intentional-divergence"
DRIFT = "drift"
UNRESOLVED = "unresolved"


@dataclass
class Findings:
    fail: list[str] = field(default_factory=list)
    cno: list[str] = field(default_factory=list)
    compared: int = 0
    state: dict[str, list[dict]] = field(
        default_factory=lambda: {MATCHED: [], INTENTIONAL: [], DRIFT: [], UNRESOLVED: []})

    def record(self, bucket: str, path: str, **extra) -> None:
        self.state[bucket].append({"path": path, **extra})


@dataclass
class RedControls:
    log: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.problems


def sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def require_divergence_metadata(entry: dict, label: str, relation: object,
                                findings: Findings) -> None:
    if relation not in {"CONTRACT_ONLY", "TEMPLATE_SCAFFOLD", "USER_OWNED", "LIVE_ONLY"}:
        return
    for field_name in ("owner", "rationale", "evidence"):
        value = entry.get(field_name)
        if not isinstance(value, str) or not value.strip():
            findings.cno.append(
                f"{label} intentional divergence has invalid {field_name}: {value!r}")
    if relation not in {"CONTRACT_ONLY", "TEMPLATE_SCAFFOLD"}:
        return
    contract = entry.get("contract")
    if not isinstance(contract, dict) or not contract:
        findings.cno.append(f"{label} contract must be a non-empty object")
        return
    for field_name in ("property", "verifier", "verifier_symbol"):
        value = contract.get(field_name)
        if not isinstance(value, str) or not value.strip():
            findings.cno.append(
                f"{label} contract has invalid {field_name}: {value!r}")
    required = contract.get("required_exports")
    if not isinstance(required, list) or not required or not all(
            isinstance(value, str) and value.strip() for value in required):
        findings.cno.append(
            f"{label} contract required_exports must be a non-empty list of strings")
    verifier = contract.get("verifier")
    if isinstance(verifier, str) and verifier.strip():
        declared_verifier = (ROOT / verifier).resolve()
        actual_verifier = Path(__file__).resolve()
        if not declared_verifier.is_file() or declared_verifier != actual_verifier:
            findings.cno.append(
                f"{label} contract verifier does not resolve to this validator: "
                f"{verifier!r}")
    symbol = contract.get("verifier_symbol")
    if isinstance(symbol, str) and symbol.strip():
        resolved = globals().get(symbol)
        if not callable(resolved) or getattr(resolved, "__module__", None) != __name__:
            findings.cno.append(
                f"{label} contract verifier_symbol is not a callable defined in this "
                f"module: {symbol!r} resolved to {resolved!r}")


def load_contract(path: Path, findings: Findings) -> dict | None:
    """Read the contract, or record precisely why it could not be observed."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.cno.append(f"contract could not be observed: {exc}")
        return None
    if not isinstance(document, dict):
        findings.cno.append("contract must be a JSON object")
        return None
    if document.get("schema_version") != 1:
        findings.cno.append("contract schema_version must be 1")
        return None
    for name in ("surfaces", "overrides", "live_only", "coupled"):
        value = document.get(name, [])
        if not isinstance(value, list):
            findings.cno.append(f"contract collection {name!r} must be a list")
        else:
            document[name] = value
    ignore = document.get("ignore", [])
    if not isinstance(ignore, list) or not all(isinstance(v, str) and v for v in ignore):
        findings.cno.append("contract collection 'ignore' must be a list of strings")
    if findings.cno:
        return None
    if not document["surfaces"]:
        findings.cno.append("contract declares no mapped surfaces")
        return None
    allowed_relations = {
        "EXACT_MIRROR", "CONTRACT_ONLY", "TEMPLATE_SCAFFOLD", "USER_OWNED", "LIVE_ONLY"}
    surface_ids: set[str] = set()
    for index, surface in enumerate(document["surfaces"]):
        if not isinstance(surface, dict):
            findings.cno.append(
                f"surfaces[{index}] must be an object: {surface!r}")
            continue
        for field_name in ("id", "live", "template"):
            value = surface.get(field_name)
            if not isinstance(value, str) or not value:
                findings.cno.append(
                    f"surfaces[{index}] has invalid {field_name}: {value!r}")
        sid = surface.get("id")
        if sid in surface_ids:
            findings.cno.append(f"duplicate surface id: {sid!r}")
        if isinstance(sid, str) and sid:
            surface_ids.add(sid)
        relation = surface.get("default_relation")
        if relation not in allowed_relations:
            findings.cno.append(
                f"surfaces[{index}] has unknown default_relation: {relation!r}")
        require_divergence_metadata(
            surface, f"surfaces[{index}]", relation, findings)
        if not isinstance(surface.get("recursive"), bool):
            findings.cno.append(
                f"surfaces[{index}] has invalid recursive: {surface.get('recursive')!r}")
        excluded = surface.get("exclude_live", [])
        if not isinstance(excluded, list) or not all(
                isinstance(value, str) and value for value in excluded):
            findings.cno.append(
                f"surfaces[{index}] exclude_live must be a list of strings")
    override_keys: set[tuple[object, object]] = set()
    for index, override in enumerate(document["overrides"]):
        if not isinstance(override, dict):
            findings.cno.append(
                f"overrides[{index}] must be an object: {override!r}")
            continue
        for field_name in ("surface", "path", "relation"):
            value = override.get(field_name)
            if not isinstance(value, str) or not value:
                findings.cno.append(
                    f"overrides[{index}] has invalid {field_name}: {value!r}")
        key = (override.get("surface"), override.get("path"))
        if key in override_keys:
            findings.cno.append(
                f"duplicate override key: {key[0]}:{key[1]}")
        override_keys.add(key)
        if override.get("surface") not in surface_ids:
            findings.cno.append(
                f"overrides[{index}] names unknown surface: {override.get('surface')!r}")
        relation = override.get("relation")
        if relation not in allowed_relations:
            findings.cno.append(
                f"overrides[{index}] has unknown relation: {relation!r}")
        require_divergence_metadata(
            override, f"overrides[{index}]", relation, findings)
    live_only_paths: set[object] = set()
    for index, entry in enumerate(document["live_only"]):
        if not isinstance(entry, dict):
            findings.cno.append(
                f"live_only[{index}] must be an object: {entry!r}")
            continue
        entry_path = entry.get("path")
        if entry_path in live_only_paths:
            findings.cno.append(f"duplicate live_only path: {entry_path!r}")
        live_only_paths.add(entry_path)
        if not isinstance(entry_path, str) or not entry_path:
            findings.cno.append(f"live_only entry has invalid path: {entry_path!r}")
        if entry.get("relation") != "LIVE_ONLY":
            findings.cno.append(
                f"live_only {entry_path!r} has invalid relation: "
                f"{entry.get('relation')!r}")
        require_divergence_metadata(
            entry, f"live_only[{index}]", entry.get("relation"), findings)
        presence = entry.get("presence")
        if presence not in {"REQUIRED", "RUNTIME_OPTIONAL"}:
            findings.cno.append(
                f"live_only {entry_path!r} has unknown presence: {presence!r}")
        match = entry.get("match")
        if match not in {"EXACT", "FILE_PREFIX"}:
            findings.cno.append(
                f"live_only {entry_path!r} has unknown match: {match!r}")
        if match == "FILE_PREFIX" and presence != "RUNTIME_OPTIONAL":
            findings.cno.append(
                f"live_only {entry_path!r} FILE_PREFIX requires RUNTIME_OPTIONAL")
    for index, group in enumerate(document["coupled"]):
        if not isinstance(group, dict):
            findings.cno.append(
                f"coupled[{index}] must be an object: {group!r}")
            continue
        surface = group.get("surface")
        if not isinstance(surface, str) or not surface:
            findings.cno.append(
                f"coupled[{index}] has invalid surface: {surface!r}")
        elif surface not in surface_ids:
            findings.cno.append(
                f"coupled[{index}] names unknown surface: {surface!r}")
        members = group.get("members")
        if not isinstance(members, list) or not members or not all(
                isinstance(member, str) and member for member in members):
            findings.cno.append(
                f"coupled[{index}] members must be a non-empty list of strings")
    if findings.cno:
        return None
    return document


def ignored(rel: str, patterns: list[str]) -> bool:
    parts = Path(rel).parts
    return any(
        parts[-1].endswith(token) if token.startswith(".") else token in parts
        for token in patterns
    )


def enumerate_side(base: Path, recursive: bool, ignore: list[str]) -> dict[str, Path] | None:
    """Relative path -> file for one side of a mapping, or None if unobservable."""
    if recursive:
        if not base.is_dir():
            return None
        return {
            str(p.relative_to(base)).replace("\\", "/"): p
            for p in sorted(base.rglob("*"))
            if p.is_file() and not ignored(str(p.relative_to(base)), ignore)
        }
    # A single-file surface maps one path to one path; "" is its only member.
    return {"": base} if base.is_file() else {}


def top_level_names(path: Path) -> set[str] | None:
    """Module-level def/class/assignment names, or None if it will not parse."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return None
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def check_contract_exports(override: dict, live: Path | None, template: Path | None,
                           label: str, findings: Findings) -> None:
    """Enforce the NAMED property that permits a body divergence.

    A relation that lets two files differ is only as good as the property it
    still guarantees. The exports are named in the contract rather than inferred,
    because a filename or a validator's name is not proof that anything holds.
    """
    contract = override.get("contract") or {}
    required = contract.get("required_exports") or []
    if not required:
        findings.cno.append(
            f"{label}: relation {override.get('relation')} permits body divergence but "
            "names no property to enforce; an unfalsifiable escape is refused")
        return
    for side, path in (("live", live), ("template", template)):
        if path is None:
            findings.fail.append(f"{label}: {side} side missing, so its declared "
                                 f"contract property cannot hold")
            continue
        names = top_level_names(path)
        if names is None:
            findings.cno.append(f"{label}: {side} side could not be parsed to check "
                                f"required exports {sorted(required)}")
            continue
        missing = [name for name in required if name not in names]
        if missing:
            findings.fail.append(
                f"{label}: {side} side breaks its declared contract property — "
                f"missing export(s) {missing}\n"
                f"    required: {sorted(required)}\n"
                f"    declared by: {contract.get('verifier_symbol', '?')} in "
                f"{contract.get('verifier', '?')}")


def check_exclusions(document: dict, root: Path, findings: Findings) -> None:
    """Every excluded live prefix must be claimed elsewhere, or it is an escape."""
    ignore = document.get("ignore", [])
    surface_claims = {s["live"] for s in document["surfaces"]}
    live_only_claims = document.get("live_only", [])
    for surface in document["surfaces"]:
        live_root = surface["live"]
        for prefix in surface.get("exclude_live", []) or []:
            full = f"{live_root}/{prefix}"
            excluded_root = root / full
            if not excluded_root.exists():
                findings.cno.append(
                    f"{surface['id']}: excluded prefix not observed: {full}")
                continue
            descendants = [path for path in excluded_root.rglob("*")
                           if path.is_file()
                           and not ignored(str(path.relative_to(root)), ignore)]
            for path in descendants:
                rel = str(path.relative_to(root)).replace("\\", "/")
                claimed_by_surface = any(
                    claim != live_root
                    and (rel == claim or rel.startswith(claim + "/"))
                    for claim in surface_claims)
                claimed_live_only = any(
                    rel == entry["path"]
                    or rel.startswith(entry["path"] + "/")
                    or (entry["match"] == "FILE_PREFIX"
                        and rel.startswith(entry["path"]))
                    for entry in live_only_claims)
                if not claimed_by_surface and not claimed_live_only:
                    findings.fail.append(
                        f"{rel}: UNDECLARED GOVERNED PATH under excluded prefix {full}")
                    findings.record(DRIFT, rel, kind="undeclared_excluded_descendant")


def check_coupled(document: dict, root: Path, findings: Findings) -> None:
    """A coupled group stamps together or not at all."""
    by_id = {s["id"]: s for s in document["surfaces"]}
    for group in document.get("coupled", []) or []:
        surface = by_id.get(group.get("surface"))
        if surface is None:
            findings.cno.append(f"coupled group names unknown surface "
                                f"{group.get('surface')!r}")
            continue
        for side in ("template", "live"):
            base = root / surface[side]
            present = [m for m in group["members"] if (base / m).is_file()]
            absent = [m for m in group["members"] if not (base / m).is_file()]
            if present and absent:
                findings.fail.append(
                    f"{surface['id']}: coupled group split on the {side} surface — "
                    f"present {present}, absent {absent}\n"
                    f"    {group.get('rationale', '')}")


def validate(root: Path, contract_path: Path) -> Findings:
    findings = Findings()
    document = load_contract(contract_path, findings)
    if document is None:
        return findings

    ignore = document.get("ignore", [])
    overrides = {(o["surface"], o["path"]): o for o in document.get("overrides", [])}
    used_overrides: set[tuple[str, str]] = set()

    for surface in document["surfaces"]:
        sid = surface.get("id")
        if not sid or not surface.get("live") or not surface.get("template"):
            findings.cno.append(f"surface entry missing id/live/template: {surface!r}")
            continue
        recursive = bool(surface.get("recursive", False))
        live_root, template_root = root / surface["live"], root / surface["template"]
        live = enumerate_side(live_root, recursive, ignore)
        template = enumerate_side(template_root, recursive, ignore)
        if live is None:
            findings.cno.append(f"{sid}: live root not observed: {surface['live']}")
        if template is None:
            findings.cno.append(f"{sid}: template root not observed: {surface['template']}")
        if live is None or template is None:
            continue

        excluded = surface.get("exclude_live", []) or []
        live = {rel: p for rel, p in live.items()
                if not any(rel == x or rel.startswith(x + "/") for x in excluded)}

        if not live and not template:
            findings.cno.append(f"{sid}: zero files observed on either side")
            continue

        relation = surface.get("default_relation", "EXACT_MIRROR")
        for rel in sorted(set(live) | set(template)):
            label = f"{sid}:{rel}" if rel else sid
            override = overrides.get((sid, rel))
            if override is not None:
                used_overrides.add((sid, rel))
            effective = override["relation"] if override else relation
            live_path, template_path = live.get(rel), template.get(rel)

            if effective in ("USER_OWNED", "LIVE_ONLY"):
                # Declared as diverging by design. Recorded, never compared.
                findings.record(INTENTIONAL, label, relation=effective,
                                owner=(override or surface).get("owner", "unspecified"))
                continue

            if effective in ("CONTRACT_ONLY", "TEMPLATE_SCAFFOLD"):
                findings.compared += 1
                check_contract_exports(override or {}, live_path, template_path,
                                       label, findings)
                findings.record(INTENTIONAL, label, relation=effective,
                                owner=(override or surface).get("owner", "unspecified"))
                continue

            if effective != "EXACT_MIRROR":
                findings.cno.append(f"{label}: unknown relation {effective!r}")
                findings.record(UNRESOLVED, label, reason=f"unknown relation {effective}")
                continue

            if live_path is None or template_path is None:
                side = "template" if live_path is not None else "live"
                findings.fail.append(
                    f"{label}: EXACT_MIRROR counterpart ABSENT from the {side} surface\n"
                    f"    live     {surface['live']}/{rel}"
                    f"{' (missing)' if live_path is None else ''}\n"
                    f"    template {surface['template']}/{rel}"
                    f"{' (missing)' if template_path is None else ''}")
                findings.record(DRIFT, label, kind=f"missing_{side}")
                continue

            left, right = sha256(live_path), sha256(template_path)
            if left is None or right is None:
                findings.cno.append(f"{label}: could not be read on both surfaces")
                findings.record(UNRESOLVED, label, reason="unreadable")
                continue
            findings.compared += 1
            if left == right:
                findings.record(MATCHED, label, relation="EXACT_MIRROR")
            else:
                findings.fail.append(
                    f"{label}: EXACT_MIRROR content DIFFERS\n"
                    f"    live     {surface['live']}/{rel} sha256={left[:16]}\n"
                    f"    template {surface['template']}/{rel} sha256={right[:16]}")
                findings.record(DRIFT, label, kind="content")

    for key in sorted(set(overrides) - used_overrides):
        findings.cno.append(
            f"{key[0]}:{key[1]} declares an intentional divergence but was never "
            "reached; a stale declaration silently widens what may diverge")

    for entry in document.get("live_only", []):
        target = root / entry["path"]
        if target.exists():
            findings.record(INTENTIONAL, entry["path"], relation="LIVE_ONLY",
                            owner=entry.get("owner", "unspecified"))
        elif entry["presence"] == "REQUIRED":
            findings.fail.append(
                f"{entry['path']}: declared LIVE_ONLY path ABSENT from live surface")
            findings.record(UNRESOLVED, entry["path"], reason="declared_present_but_absent")

    check_exclusions(document, root, findings)
    check_coupled(document, root, findings)

    if not findings.compared and not findings.cno:
        findings.cno.append("zero governed paths compared; a vacuous run is not a pass")
    return findings


# ── Watched-red calibration ───────────────────────────────────────────────────
# Every control named by ruling 5308853615. `expect` is "red" when the mutation
# must produce a NEW finding naming `names`, and "clean" when the point of the
# control is that this verifier must NOT fail — a parity checker that fails on
# intentional divergence is as wrong as one that misses drift.
CONTROLS = (
    ("non-isomorphic-mapping-resolves", None, None, "clean", "prompt-engineering"),
    ("exact-mirror-content-drift",
     "adws/adw_modules/console.py", "edit", "red", "console.py"),
    ("required-template-counterpart-missing",
     ".claude/skills/sssf/templates/adws/adw_modules/tracer.py", "remove", "red", "tracer.py"),
    ("undeclared-live-only-addition",
     "adws/adw_modules/zz_undeclared.py", "add", "red", "zz_undeclared.py"),
    ("undeclared-excluded-prefix-addition",
     "adws/adw_data/zz_undeclared.json", "add", "red", "zz_undeclared.json"),
    ("malformed-contract-entry",
     None, "malformed_contract", "cno", "overrides[1]"),
    ("missing-divergence-metadata",
     None, "missing_metadata", "cno", "overrides[0] intentional divergence has invalid evidence"),
    ("fictitious-declared-verifier",
     None, "bad_verifier_path", "cno", "verifier does not resolve to this validator"),
    ("noncallable-declared-verifier-symbol",
     None, "noncallable_verifier_symbol", "cno", "'json' resolved to"),
    ("imported-declared-verifier-symbol",
     None, "imported_verifier_symbol", "cno", "'Path' resolved to"),
    ("coupled-adapter-without-supervisor",
     ".claude/skills/sssf/templates/adws/adw_modules/subprocess_supervisor.py",
     "remove", "red", "coupled group split"),
    ("scaffold-body-divergence-stays-green", None, None, "clean", "quality.py"),
    ("scaffold-broken-shared-api-turns-red",
     ".claude/skills/sssf/templates/adws/adw_modules/quality.py", "drop_export", "red",
     "run_inkwell_quality"),
    ("prompt-mechanism-drift",
     ".claude/skills/sssf/templates/prompt_engineering/scout/system.md", "truncate", "red",
     "scout/system.md"),
    ("user-owned-roster-stays-classified", None, None, "clean", "roster-config"),
)


def materialize(document: dict, root: Path, temp: Path) -> None:
    """Copy every mapped surface into a disposable root, mapping preserved."""
    wanted: list[str] = []
    for surface in document["surfaces"]:
        wanted.extend([surface["live"], surface["template"]])
    wanted.extend(entry["path"] for entry in document.get("live_only", []))
    for rel in wanted:
        source, destination = root / rel, temp / rel
        if destination.exists() or not source.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)


def apply_mutation(path: Path, kind: str) -> None:
    if kind == "edit":
        path.write_text(path.read_text(encoding="utf-8") + "\n# mutated\n", encoding="utf-8")
    elif kind == "add":
        path.write_text("# undeclared live-only addition\n", encoding="utf-8")
    elif kind == "remove":
        path.unlink()
    elif kind == "truncate":
        # Drop the mapped prompt notice while leaving the file present, which is
        # exactly how a mechanism can land without the prompt that describes it.
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        path.write_text("".join(lines[:-1]), encoding="utf-8")
    elif kind == "drop_export":
        # Break the shared API contract without touching the placeholder bodies.
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("def run_inkwell_quality(", "def _removed_api("),
                        encoding="utf-8")


def surface_by_id(document: dict, sid: str) -> dict:
    return next(s for s in document["surfaces"] if s["id"] == sid)


def clean_precondition(name: str, root: Path, document: dict) -> tuple[bool, str]:
    """Confirm the condition a 'clean' control tolerates is actually present.

    Without this a clean control degenerates: if `quality.py` were flattened, a
    control asserting "a differing scaffold body does not turn red" would keep
    passing while no longer testing anything.
    """
    if name == "non-isomorphic-mapping-resolves":
        surface = surface_by_id(document, "prompt-engineering")
        # The mapping is only interesting because the two roots do NOT share a
        # relative path; a subtree diff would call these files absent.
        isomorphic = surface["template"].endswith(surface["live"])
        live_files = list((root / surface["live"]).rglob("*.md"))
        if isomorphic or not live_files:
            return False, ("mapping is isomorphic or empty, so it cannot demonstrate "
                           "non-isomorphic resolution")
        return True, (f"{len(live_files)} file(s) map {surface['template']} -> "
                      f"{surface['live']} and resolve without being called absent")

    if name == "scaffold-body-divergence-stays-green":
        surface = surface_by_id(document, "adw-tree")
        live = root / surface["live"] / "adw_modules/quality.py"
        template = root / surface["template"] / "adw_modules/quality.py"
        if not (live.is_file() and template.is_file()):
            return False, "quality.py missing on one surface"
        if sha256(live) == sha256(template):
            return False, ("quality.py bodies are identical, so this control no longer "
                           "demonstrates that a differing scaffold body stays green")
        return True, "quality.py bodies differ and are classified TEMPLATE_SCAFFOLD, not drift"

    if name == "user-owned-roster-stays-classified":
        surface = surface_by_id(document, "roster-config")
        live, template = root / surface["live"], root / surface["template"]
        if not (live.is_file() and template.is_file()):
            return False, "roster config missing on one surface"
        if sha256(live) == sha256(template):
            return False, ("roster configs are identical, so this control no longer "
                           "demonstrates that user-owned divergence is tolerated")
        return True, "user-owned roster differs and stays classified rather than copied or failed"

    return False, f"no precondition defined for clean control {name}"


def red_controls(root: Path, contract_path: Path) -> RedControls:
    """Prove this verifier still fails, and still stays green where it must.

    Going red is not evidence on its own — a checker can be stuck red, or red for
    an unrelated reason. A "red" control must introduce a finding NAMING its own
    target that the unmutated baseline did not already contain. A "clean" control
    asserts the opposite obligation: intentional divergence must not be reported
    as drift.
    """
    control = RedControls()
    probe = Findings()
    document = load_contract(contract_path, probe)
    if document is None:
        control.problems.extend(probe.cno)
        return control

    base = validate(root, contract_path)
    baseline = {line.split("\n", 1)[0] for line in base.fail}
    baseline_cno = set(base.cno)

    for name, target, kind, expect, names in CONTROLS:
        if expect == "clean":
            # Assert against the unmutated tree: the named thing is classified,
            # not failed. A clean control is only meaningful if the condition it
            # tolerates is actually PRESENT, so each names the precondition it
            # must first observe — otherwise flattening the very divergence this
            # control protects would leave it silently passing.
            classified = [entry for bucket in (MATCHED, INTENTIONAL)
                          for entry in base.state[bucket] if names in entry["path"]]
            failed = [line for line in base.fail if names in line]
            precondition, detail = clean_precondition(name, root, document)
            if not precondition:
                control.problems.append(f"{name}: precondition absent — {detail}")
            elif failed:
                control.problems.append(
                    f"{name}: {names} must not be reported as drift, but is: {failed[0]}")
            elif not classified:
                control.problems.append(
                    f"{name}: {names} is not classified at all; an unclassified "
                    "governed path is not a pass")
            else:
                control.log.append(f"watched-clean {name}: {detail}")
            continue

        with tempfile.TemporaryDirectory(prefix="sssf-parity-red-") as directory:
            temp = Path(directory)
            if kind == "malformed_contract":
                if not all(isinstance(entry, dict)
                           for entry in document["overrides"]):
                    control.problems.append(
                        f"{name}: precondition absent — overrides already malformed")
                    continue
                mutated = json.loads(json.dumps(document))
                mutated["overrides"].append("not-an-object")
                probe_contract = temp / "malformed-contract.json"
                probe_contract.write_text(json.dumps(mutated), encoding="utf-8")
                result = validate(root, probe_contract)
                introduced = [line for line in result.cno
                              if line not in baseline_cno and names in line]
                if not introduced:
                    control.problems.append(
                        f"{name}: malformed entry did not yield CNO naming {names}")
                else:
                    control.log.append(f"watched-red {name}: CNO naming {names}")
                continue
            if kind == "missing_metadata":
                evidence = document["overrides"][0].get("evidence")
                if not isinstance(evidence, str) or not evidence.strip():
                    control.problems.append(
                        f"{name}: precondition absent — overrides[0] evidence missing")
                    continue
                mutated = json.loads(json.dumps(document))
                del mutated["overrides"][0]["evidence"]
                probe_contract = temp / "missing-metadata-contract.json"
                probe_contract.write_text(json.dumps(mutated), encoding="utf-8")
                result = validate(root, probe_contract)
                introduced = [line for line in result.cno
                              if line not in baseline_cno and names in line]
                if not introduced:
                    control.problems.append(
                        f"{name}: stripped field did not yield CNO naming {names}")
                else:
                    control.log.append(f"watched-red {name}: CNO naming {names}")
                continue
            if kind in {"bad_verifier_path", "noncallable_verifier_symbol",
                        "imported_verifier_symbol"}:
                contract = document["overrides"][0].get("contract")
                if not isinstance(contract, dict):
                    control.problems.append(
                        f"{name}: precondition absent — overrides[0] contract missing")
                    continue
                mutated = json.loads(json.dumps(document))
                probe_value = {
                    "bad_verifier_path": ("verifier", "docs/validation/not-a-verifier.py"),
                    "noncallable_verifier_symbol": ("verifier_symbol", "json"),
                    "imported_verifier_symbol": ("verifier_symbol", "Path"),
                }[kind]
                field_name, value = probe_value
                if contract.get(field_name) == value:
                    control.problems.append(
                        f"{name}: precondition absent — {field_name} already equals {value!r}")
                    continue
                mutated["overrides"][0]["contract"][field_name] = value
                probe_contract = temp / f"{kind}-contract.json"
                probe_contract.write_text(json.dumps(mutated), encoding="utf-8")
                result = validate(root, probe_contract)
                introduced = [line for line in result.cno
                              if line not in baseline_cno and names in line]
                if not introduced:
                    control.problems.append(
                        f"{name}: invalid declaration did not yield CNO naming {names}")
                else:
                    control.log.append(f"watched-red {name}: CNO naming {names}")
                continue
            materialize(document, root, temp)
            path = temp / target
            if kind == "add" and path.exists():
                control.problems.append(
                    f"{name}: precondition absent — target already exists: {target}")
                continue
            try:
                apply_mutation(path, kind)
            except OSError as exc:
                control.problems.append(f"{name}: mutation could not be applied: {exc}")
                continue
            result = validate(temp, contract_path)
            headline = {line.split("\n", 1)[0] for line in result.fail}
            introduced = [line for line in headline
                          if line not in baseline and names in line]
            if not result.fail:
                control.problems.append(f"{name}: mutation did not turn the verifier red")
            elif not introduced:
                control.problems.append(
                    f"{name}: verifier went red but not naming {names}; red for the "
                    "wrong reason is not calibration")
            else:
                control.log.append(f"watched-red {name}: FAIL naming {names}")

    if len(control.log) != len(CONTROLS) and not control.problems:
        control.problems.append(
            f"expected {len(CONTROLS)} controls, observed {len(control.log)}")
    return control


def structured_state(findings: Findings, verdict: str, contract_path: Path,
                     control: RedControls | None) -> dict:
    """Machine-readable mapped-surface status, bound to exact verifier bytes."""
    return {
        "schema_version": 1,
        "claim": "mapped-surface-parity",
        "verdict": verdict,
        "bound_to": {
            "verifier": "docs/validation/check_mapped_surface_parity.py",
            "verifier_sha256": sha256(Path(__file__).resolve()),
            "contract": str(contract_path.name),
            "contract_sha256": sha256(contract_path),
        },
        "counts": {bucket: len(entries) for bucket, entries in findings.state.items()},
        "compared": findings.compared,
        "paths": findings.state,
        "red_controls": {
            "required": len(CONTROLS),
            "demonstrated": len(control.log) if control else 0,
            "problems": control.problems if control else ["not run"],
        },
    }


def report(findings: Findings, contract_path: Path, control: RedControls | None,
           state_path: Path | None) -> int:
    if control is not None and not control.passed:
        verdict = "CNO"
    elif findings.cno:
        verdict = "CNO"
    elif findings.fail:
        verdict = "FAIL"
    else:
        verdict = "PASS"

    print(f"mapped-surface parity: {verdict}")
    if control is not None and not control.passed:
        for line in control.problems:
            print(f"- watched-red control: {line}")
    if verdict in ("CNO", "FAIL"):
        for line in findings.cno:
            print(f"- {line}")
        for line in findings.fail:
            print(f"- {line}")
    else:
        counts = {b: len(e) for b, e in findings.state.items()}
        print(f"- matched: {counts[MATCHED]}")
        print(f"- intentional divergence: {counts[INTENTIONAL]}")
        print(f"- drift: {counts[DRIFT]}")
        print(f"- unresolved: {counts[UNRESOLVED]}")
        print(f"- governed paths compared: {findings.compared}")
        for entry in findings.state[INTENTIONAL]:
            print(f"    {entry['relation']:18} {entry['path']}")
    if control is not None:
        for line in control.log:
            print(f"- {line}")

    state = structured_state(findings, verdict, contract_path, control)
    if state_path is not None:
        state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n",
                              encoding="utf-8")
    print("structured_state:")
    print(json.dumps(state, indent=2, sort_keys=True))
    return 0 if verdict == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--state", type=Path, default=None,
                        help="also write the structured state to this path")
    parser.add_argument("--skip-red-controls", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root, contract_path = args.root.resolve(), args.contract.resolve()
    # Calibration runs on every invocation, so this verifier cannot report PASS
    # without having just demonstrated it still fails where it must.
    control = None if args.skip_red_controls else red_controls(root, contract_path)
    return report(validate(root, contract_path), contract_path, control, args.state)


if __name__ == "__main__":
    sys.exit(main())
