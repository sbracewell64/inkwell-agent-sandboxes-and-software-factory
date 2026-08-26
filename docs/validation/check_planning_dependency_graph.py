#!/usr/bin/env python3
"""Canonical validator for the typed planning dependency graph.

`docs/development/ROADMAP.md` declares that its typed dependency edges govern
when prose ordering and the machine representation disagree. That declaration
makes the graph a load-bearing planning authority surface, and a declaration
nothing enforces is not an authority. This control is the enforcement half.

It reads the single `planning-dependency-graph/v1` block out of the roadmap and
proves the properties the rest of the planning owner actually consumes:

- the schema generation is recognized, so a stale or unknown graph fails closed;
- node, predicate and status-axis identities are unique;
- every edge endpoint, owner reference, register reference, predicate target and
  status-axis blocker resolves to something that exists;
- only the declared edge-kind vocabulary is used;
- predicate authority classes and status-axis values come from the declared
  vocabularies, and each observed status value is one the axis actually allows;
- registration never promotes lifecycle state: any node claiming `ACTIVE` or
  `PROVEN` must be one of the states already observed before this graph existed,
  and every node whose owning section declares a planning state must agree
  with it;
- the `SEQUENCED` universe is closed (the totality invariant): every `SEQUENCED`
  node is either an edge endpoint or carries a valid independence disposition in
  `independent_nodes` — one that names a declared node, gives a reason, and is
  not claimed for a node that has a hard prerequisite. A `SEQUENCED` node with
  neither leaves prose as its sole owner, which the lifecycle owner's
  durable-location rule forbids;
- Docker-first sequencing, the WAYFINDER-0/1 hard pre-DSH chain, and the Poker
  School nonserializing relation survive intact, and no hard prerequisite is
  quietly weakened into a soft or nonserializing one;
- the graph stays discoverable through `docs/manifest.yaml`;
- controls #31 and #32 appear only inside the one authorized pending-dependency
  predicate.

The gate ships no pyyaml, so the block is read by a deliberately small
indentation parser that accepts one explicit YAML subset and raises on anything
else. Fail-closed is the point: an unparseable, ambiguous or unfamiliar
construct is a red result, never a skipped check.

Every property above is paired with a watched-red control that plants the exact
defect in a copy of the real sources and requires this validator to go red on
it. The unmodified sources are asserted green in the same run, so the control
set can never pass vacuously.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

ROADMAP = "docs/development/ROADMAP.md"
MANIFEST = "docs/manifest.yaml"
REGISTER = "docs/development/FUTURE_CANDIDATES.md"
LIFECYCLE = "docs/development/PLANNING_LIFECYCLE.md"
BOUND1 = "docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md"
SELF = "docs/validation/check_planning_dependency_graph.py"

SOURCE_FILES = (ROADMAP, MANIFEST, REGISTER, LIFECYCLE, BOUND1)

SCHEMA = "planning-dependency-graph/v1"
GRAPH_HEADING = "## Machine-readable dependency graph"
GRAPH_ANCHOR = "machine-readable-dependency-graph"

ALLOWED_EDGE_KINDS = {
    "HARD_PREREQUISITE",
    "NONSERIALIZING_COMMISSIONING",
    "SOFT_UNLOCK",
    "REOPENS_ON_DEFECT",
    "CONSTRAINS_DESIGN",
}

# `docs/development/PLANNING_LIFECYCLE.md` owns these names.
LIFECYCLE_STATES = {
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
}

# A registration must never advance an item. Only items already in one of these
# states before the graph existed may carry a promoted state inside it.
PROMOTED_STATES = {"ACTIVE", "PROVEN", "QUALIFIED", "ACCEPTED", "COMMISSIONED"}
PREEXISTING_PROMOTED = {"LAUNCH-1": "ACTIVE", "SBX-0": "ACTIVE", "FUT-003": "ACTIVE"}

AUTHORITY_CLASSES = {"SELF_HANDLE", "CAPTAIN_REQUIRED", "BROWSER_SOL", "EXTERNAL_DEPENDENCY"}

# Recorded exactly as ruled; an axis that drifts from its authorized vocabulary
# is a defect even if every value is individually plausible.
REQUIRED_STATUS_AXES = {
    "POKER_SCHOOL_PHASE_A": ["PASS", "INCOMPLETE", "BLOCKED"],
    "WAYFINDER_TECHNICAL_GATE": ["PASS", "FAIL", "CNO"],
    "WAYFINDER_PRODUCT_COMMISSIONING": ["PASS", "INCOMPLETE", "BLOCKED", "FAIL", "CNO"],
}

# Docker-first sequencing, the hard pre-DSH Wayfinder chain, and the Agent
# Lightning containment prerequisites. Each must be present AND hard.
REQUIRED_HARD_EDGES = [
    ("SBX-0", "SBX-1"),
    ("SBX-1", "SBX-2"),
    ("BOUND-1", "SBX-2"),
    ("SBX-2", "SBX-3"),
    ("SBX-3", "SBX-4"),
    ("SBX-4", "SBX-5"),
    ("SBX-5", "SBX-6"),
    ("SBX-6", "SBX-7"),
    ("SBX-7", "SBX-8"),
    ("SBX-8", "BASELINE-PR"),
    ("BASELINE-PR", "POST-DOCKER-BASELINE"),
    ("POST-DOCKER-BASELINE", "WAYFINDER-0"),
    ("WAYFINDER-0", "WAYFINDER-1"),
    ("WAYFINDER-1", "DSH-0A"),
    ("WAYFINDER-1", "WAYFINDER-POC-1"),
    ("SBX-3", "AL-1"),
    ("SBX-4", "AL-1"),
    ("SBX-5", "AL-1"),
    ("SBX-6", "AL-1"),
    ("BOUND-1", "AL-1"),
    ("DSH-0A", "DSH-0B"),
    ("DSH-0B", "DSH-1"),
]

REQUIRED_NONSERIALIZING_EDGE = ("WAYFINDER-POC-1", "WAYFINDER_PRODUCT_COMMISSIONING")
POKER_SCHOOL_PREDICATE = "POKER-SCHOOL-SOURCE-CUSTODY-v1"
POKER_SCHOOL_MUST_NOT_GATE = ("WAYFINDER-0", "WAYFINDER-1", "DSH-0A")
AGENT_LIGHTNING_NODE = "AL-1"
AGENT_LIGHTNING_NOT_PREDECESSOR_OF = ("SBX-7", "SBX-8", "BASELINE-PR", "WAYFINDER-0", "DSH-0A")

PENDING_ONLY_PREDICATE = "SDLC-L3-RUNTIME-GATE-v1"
PENDING_ONLY_PATTERN = re.compile(r"#3[12]\b|\bHQC\b|\bEIL\b")

FUT_ID = re.compile(r"\bFUT-\d{3}\b")
PLANNING_STATE_DECLARATION = re.compile(r"Planning state[^`]{0,40}`([A-Z_]+)`")


# --------------------------------------------------------------------------
# A deliberately small YAML subset. Anything outside it raises.
# --------------------------------------------------------------------------


class GraphSyntaxError(Exception):
    """The block used a construct this validator refuses to guess about."""


KEY = re.compile(r"^([A-Za-z0-9_./#-]+):(?:\s+(.*))?$")
BLOCK_SCALAR_HEADERS = {">", ">-", "|", "|-"}


class _Reader:
    def __init__(self, text: str) -> None:
        self.entries: list[tuple[int, str, int]] = []
        for number, raw in enumerate(text.splitlines(), 1):
            if "\t" in raw:
                raise GraphSyntaxError(f"line {number}: tab indentation is not accepted")
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            self.entries.append((indent, raw.strip(), number))
        self.index = 0

    def at_end(self) -> bool:
        return self.index >= len(self.entries)

    def peek(self) -> tuple[int, str, int]:
        return self.entries[self.index]

    def raw_lines(self, text: str) -> list[str]:
        return text.splitlines()


def _scalar(raw: str, number: int) -> str:
    value = raw.strip()
    if not value:
        raise GraphSyntaxError(f"line {number}: empty scalar")
    if value[0] in "\"'":
        quote = value[0]
        if len(value) < 2 or value[-1] != quote:
            raise GraphSyntaxError(f"line {number}: unterminated quoted scalar")
        inner = value[1:-1]
        if quote in inner or "\\" in inner:
            raise GraphSyntaxError(f"line {number}: unsupported escape in quoted scalar")
        return inner
    if value.startswith("{") or value.endswith("}"):
        raise GraphSyntaxError(f"line {number}: flow mappings are not accepted")
    if " #" in value:
        raise GraphSyntaxError(f"line {number}: inline comments are not accepted")
    return value


def _flow_sequence(raw: str, number: int) -> list[str]:
    inner = raw.strip()[1:-1].strip()
    if not inner:
        raise GraphSyntaxError(f"line {number}: empty flow sequence")
    items = []
    for piece in inner.split(","):
        item = piece.strip()
        if not item:
            raise GraphSyntaxError(f"line {number}: empty flow-sequence item")
        if item[0] in "\"'[{" or item[-1] in "]}":
            raise GraphSyntaxError(
                f"line {number}: only plain scalars are accepted inside a flow sequence"
            )
        items.append(item)
    return items


def _block_scalar(lines: list[str], start: int, owner_indent: int, header: str) -> tuple[str, int]:
    collected: list[str] = []
    index = start
    while index < len(lines):
        raw = lines[index]
        if not raw.strip():
            collected.append("")
            index += 1
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        if indent <= owner_indent:
            break
        collected.append(raw.strip())
        index += 1
    if not collected:
        raise GraphSyntaxError(f"line {start}: block scalar has no body")
    joiner = "\n" if header.startswith("|") else " "
    return joiner.join(part for part in collected if part or joiner == "\n").strip(), index


def parse(text: str) -> dict:
    """Parse the accepted subset into plain dicts, lists and strings."""
    lines = text.splitlines()
    for number, raw in enumerate(lines, 1):
        if "\t" in raw:
            raise GraphSyntaxError(f"line {number}: tab indentation is not accepted")

    def line_indent(index: int) -> int:
        raw = lines[index]
        return len(raw) - len(raw.lstrip(" "))

    def next_content(index: int) -> int:
        while index < len(lines) and not lines[index].strip():
            index += 1
        return index

    def parse_value(rest: str | None, index: int, owner_indent: int):
        """Return (value, next_index). `index` is the line after the key line."""
        if rest is not None and rest.strip():
            body = rest.strip()
            if body in BLOCK_SCALAR_HEADERS:
                return _block_scalar(lines, index, owner_indent, body)
            if body[0] not in "\"'" and body.startswith("[") and body.endswith("]"):
                return _flow_sequence(body, index), index
            return _scalar(body, index), index
        following = next_content(index)
        if following >= len(lines):
            raise GraphSyntaxError(f"line {index}: key has no value")
        if line_indent(following) <= owner_indent:
            raise GraphSyntaxError(f"line {following + 1}: key has no value")
        return parse_block(following, line_indent(following))

    def parse_block(index: int, indent: int):
        index = next_content(index)
        if index >= len(lines):
            raise GraphSyntaxError("unexpected end of block")
        if lines[index].strip().startswith("- "):
            return parse_sequence(index, indent)
        return parse_mapping(index, indent)

    def parse_mapping(index: int, indent: int):
        result: dict[str, object] = {}
        while True:
            index = next_content(index)
            if index >= len(lines):
                break
            current = line_indent(index)
            if current < indent:
                break
            if current > indent:
                raise GraphSyntaxError(f"line {index + 1}: unexpected indentation")
            body = lines[index].strip()
            if body.startswith("- "):
                break
            match = KEY.match(body)
            if not match:
                raise GraphSyntaxError(f"line {index + 1}: not a key: {body!r}")
            key, rest = match.group(1), match.group(2)
            if key in result:
                raise GraphSyntaxError(f"line {index + 1}: duplicate key {key!r}")
            value, index = parse_value(rest, index + 1, indent)
            result[key] = value
        return result, index

    def parse_sequence(index: int, indent: int):
        items: list[object] = []
        while True:
            index = next_content(index)
            if index >= len(lines):
                break
            current = line_indent(index)
            if current != indent:
                if current < indent:
                    break
                raise GraphSyntaxError(f"line {index + 1}: unexpected indentation")
            body = lines[index].strip()
            if not body.startswith("- "):
                break
            rest = body[2:]
            content_indent = indent + 2
            match = KEY.match(rest)
            if match:
                item: dict[str, object] = {}
                key, inline = match.group(1), match.group(2)
                value, index = parse_value(inline, index + 1, content_indent)
                item[key] = value
                more, index = parse_mapping(index, content_indent)
                for key, value in more.items():
                    if key in item:
                        raise GraphSyntaxError(f"line {index}: duplicate key {key!r}")
                    item[key] = value
                items.append(item)
            else:
                if rest.strip() in BLOCK_SCALAR_HEADERS:
                    value, index = _block_scalar(lines, index + 1, indent, rest.strip())
                else:
                    value, index = _scalar(rest, index + 1), index + 1
                items.append(value)
        return items, index

    value, index = parse_block(0, 0)
    index = next_content(index)
    if index < len(lines):
        raise GraphSyntaxError(f"line {index + 1}: trailing content after the document")
    if not isinstance(value, dict):
        raise GraphSyntaxError("the graph must be a mapping")
    return value


# --------------------------------------------------------------------------
# Markdown helpers
# --------------------------------------------------------------------------


def slug(heading: str) -> str:
    return re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-")


def headings(text: str) -> list[tuple[int, str, int]]:
    """(level, slug, line index) for every heading outside a fenced block."""
    found = []
    fenced = False
    for index, raw in enumerate(text.splitlines()):
        if raw.startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = re.match(r"^(#{1,6})\s+(.*?)\s*$", raw)
        if match:
            found.append((len(match.group(1)), slug(match.group(2)), index))
    return found


def section_text(text: str, anchor: str) -> str | None:
    lines = text.splitlines()
    found = headings(text)
    for position, (level, name, index) in enumerate(found):
        if name != anchor:
            continue
        end = len(lines)
        for deeper_level, _, deeper_index in found[position + 1:]:
            if deeper_level <= level:
                end = deeper_index
                break
        return "\n".join(lines[index:end])
    return None


def graph_block(roadmap: str) -> str | None:
    """The one fenced graph block under the declared heading, or None."""
    section = section_text(roadmap, GRAPH_ANCHOR)
    if section is None:
        return None
    blocks = re.findall(r"^```yaml\n(.*?)\n```$", section, re.S | re.M)
    if len(blocks) != 1:
        return None
    return blocks[0]


def manifest_planning(manifest: str) -> dict:
    """Parse only the `planning:` block, so unrelated manifest bytes cannot
    fail this control closed for the wrong reason."""
    lines = manifest.splitlines()
    collected: list[str] = []
    inside = False
    for raw in lines:
        if not inside:
            if raw.rstrip() == "planning:":
                inside = True
            continue
        if raw.strip() and not raw.startswith(" "):
            break
        collected.append(raw[2:] if raw.startswith("  ") else raw)
    if not collected:
        raise GraphSyntaxError("docs/manifest.yaml declares no planning block")
    return parse("\n".join(collected))


# --------------------------------------------------------------------------
# The properties
# --------------------------------------------------------------------------


def walk(value, path=("graph",)):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from walk(item, path + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, path + (str(index),))
    else:
        yield ".".join(path), str(value)


def evaluate(sources: dict[str, str]) -> list[str]:
    """Every observed defect in these exact source bytes."""
    errors: list[str] = []

    for name in SOURCE_FILES:
        if name not in sources:
            return [f"could-not-observe: required source {name} is missing"]

    roadmap = sources[ROADMAP]
    block = graph_block(roadmap)
    if block is None:
        return [
            "could-not-observe: exactly one fenced graph block under "
            f"'{GRAPH_HEADING}' is required in {ROADMAP}"
        ]
    declarations = roadmap.count(f"schema: {SCHEMA.rsplit('/', 1)[0]}")
    if declarations != 1:
        errors.append(
            f"{declarations} planning-dependency-graph declarations in {ROADMAP}; "
            "exactly one owner is allowed"
        )

    try:
        graph = parse(block)
    except GraphSyntaxError as error:
        return [f"graph does not parse, failing closed: {error}"]

    # --- schema generation recognition -----------------------------------
    schema = graph.get("schema")
    if schema != SCHEMA:
        return [f"unsupported graph schema {schema!r}; this validator knows {SCHEMA!r}"]

    for required in ("owner", "edge_kinds", "nodes", "edges", "status_axes", "predicates"):
        if required not in graph:
            errors.append(f"graph is missing required section {required!r}")
    if errors:
        return errors

    if graph["owner"] != ROADMAP:
        errors.append(f"graph owner {graph['owner']!r} is not {ROADMAP}")

    nodes = graph["nodes"]
    edges = graph["edges"]
    axes = graph["status_axes"]
    predicates = graph["predicates"]

    # --- non-vacuity ------------------------------------------------------
    if not isinstance(nodes, list) or not nodes:
        return ["could-not-observe: the graph declares no nodes"]
    if not isinstance(edges, list) or not edges:
        return ["could-not-observe: the graph declares no edges"]
    if not isinstance(predicates, dict) or not predicates:
        return ["could-not-observe: the graph declares no predicates"]

    # --- unique identities ------------------------------------------------
    node_ids: list[str] = []
    for entry in nodes:
        if not isinstance(entry, dict) or "id" not in entry:
            errors.append(f"node entry without an id: {entry!r}")
            continue
        node_ids.append(str(entry["id"]))
    duplicates = sorted({name for name in node_ids if node_ids.count(name) > 1})
    if duplicates:
        errors.append(f"duplicate node identities: {duplicates}")
    ids = set(node_ids)

    axis_names = set(axes) if isinstance(axes, dict) else set()
    overlap = ids & axis_names
    if overlap:
        errors.append(f"names used as both a node and a status axis: {sorted(overlap)}")
    overlap = ids & set(predicates)
    if overlap:
        errors.append(f"names used as both a node and a predicate: {sorted(overlap)}")

    register_futs = set(FUT_ID.findall(sources[REGISTER]))

    def resolves(name: str) -> bool:
        return name in ids or name in axis_names or name in register_futs

    # --- edge vocabulary and endpoints ------------------------------------
    declared_kinds = graph["edge_kinds"]
    if not isinstance(declared_kinds, dict) or not declared_kinds:
        errors.append("edge_kinds declares no vocabulary")
        declared_kinds = {}
    unknown = sorted(set(declared_kinds) - ALLOWED_EDGE_KINDS)
    if unknown:
        errors.append(f"edge_kinds declares kinds outside the allowed vocabulary: {unknown}")

    observed: dict[tuple[str, str], set[str]] = {}
    for entry in edges:
        if not isinstance(entry, dict):
            errors.append(f"edge entry is not a mapping: {entry!r}")
            continue
        missing = [key for key in ("from", "to", "kind") if key not in entry]
        if missing:
            errors.append(f"edge {entry!r} is missing {missing}")
            continue
        source, target, kind = str(entry["from"]), str(entry["to"]), str(entry["kind"])
        if kind not in ALLOWED_EDGE_KINDS:
            errors.append(f"edge {source} -> {target} uses unknown kind {kind!r}")
        elif kind not in declared_kinds:
            errors.append(f"edge {source} -> {target} uses undeclared kind {kind!r}")
        if not resolves(source):
            errors.append(f"edge endpoint does not resolve: {source!r} (in {source} -> {target})")
        if not resolves(target):
            errors.append(f"edge endpoint does not resolve: {target!r} (in {source} -> {target})")
        observed.setdefault((source, target), set()).add(kind)

    # --- owner and register references ------------------------------------
    checked_references = 0
    for entry in nodes:
        if not isinstance(entry, dict):
            continue
        name = entry.get("id", "<unnamed>")
        for key in ("owner", "register_entry"):
            reference = entry.get(key)
            if not reference:
                continue
            checked_references += 1
            path, _, anchor = str(reference).partition("#")
            if path not in sources:
                errors.append(f"node {name}: {key} names a file outside this control: {path}")
                continue
            if anchor and section_text(sources[path], anchor) is None:
                errors.append(f"node {name}: {key} anchor does not resolve: {reference}")
        for neighbour in entry.get("not_a_predecessor_of", []) or []:
            if not resolves(str(neighbour)):
                errors.append(f"node {name}: not_a_predecessor_of {neighbour!r} does not resolve")
    if checked_references == 0:
        errors.append("could-not-observe: no node declares an owner reference")

    # --- lifecycle states and promotion ------------------------------------
    cross_checked = 0
    for entry in nodes:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("id", "<unnamed>"))
        state = entry.get("planning_state")
        if state is None:
            errors.append(f"node {name} declares no planning_state")
            continue
        state = str(state)
        if state not in LIFECYCLE_STATES:
            errors.append(f"node {name}: planning_state {state!r} is not a lifecycle state")
            continue
        if state in PROMOTED_STATES and PREEXISTING_PROMOTED.get(name) != state:
            errors.append(
                f"node {name} is registered as {state}; registration must not promote "
                "lifecycle state"
            )
        reference = entry.get("owner")
        if not reference:
            continue
        path, _, anchor = str(reference).partition("#")
        if path not in sources:
            continue
        text = section_text(sources[path], anchor) if anchor else sources[path]
        if text is None:
            continue
        declared = PLANNING_STATE_DECLARATION.search(text)
        if not declared:
            continue
        cross_checked += 1
        if declared.group(1) != state:
            errors.append(
                f"node {name}: graph says {state}, its owning section says "
                f"{declared.group(1)}"
            )
    if cross_checked < 6:
        errors.append(
            "could-not-observe: only "
            f"{cross_checked} node states were cross-checked against their owning section"
        )

    # --- SEQUENCED-universe totality ---------------------------------------
    # `PLANNING_LIFECYCLE.md` makes a typed edge part of the durable location of
    # a SEQUENCED item. A SEQUENCED node that is in no edge and carries no
    # independence disposition leaves prose as its sole owner, which is the exact
    # situation that rule exists to eliminate.
    independent = graph.get("independent_nodes", [])
    if not isinstance(independent, list):
        errors.append("independent_nodes is not a list")
        independent = []
    independent_ids: set[str] = set()
    hard_targets = {
        target for (_, target), kinds in observed.items() if "HARD_PREREQUISITE" in kinds
    }
    for entry in independent:
        if not isinstance(entry, dict) or "id" not in entry:
            errors.append(f"independent_nodes entry without an id: {entry!r}")
            continue
        name = str(entry["id"])
        if name not in ids:
            errors.append(f"independent_nodes names {name!r}, which is not a declared node")
            continue
        if not str(entry.get("why", "")).strip():
            errors.append(f"independent_nodes entry {name} declares no reason")
            continue
        if name in hard_targets:
            errors.append(
                f"independent_nodes declares {name} independent while it is the target of a "
                "hard prerequisite"
            )
            continue
        independent_ids.add(name)

    edged = {name for pair in observed for name in pair}
    sequenced = [
        str(entry["id"])
        for entry in nodes
        if isinstance(entry, dict)
        and "id" in entry
        and str(entry.get("planning_state")) == "SEQUENCED"
    ]
    if not sequenced:
        errors.append("could-not-observe: the graph declares no SEQUENCED node")
    for name in sequenced:
        if name not in edged and name not in independent_ids:
            errors.append(
                f"node {name} is SEQUENCED but participates in no typed edge and carries no "
                "valid independence disposition"
            )

    # --- status axes -------------------------------------------------------
    if not isinstance(axes, dict):
        errors.append("status_axes is not a mapping")
        axes = {}
    for name, expected in REQUIRED_STATUS_AXES.items():
        if name not in axes:
            errors.append(f"status axis {name} is missing")
            continue
        axis = axes[name]
        if not isinstance(axis, dict):
            errors.append(f"status axis {name} is not a mapping")
            continue
        values = axis.get("values")
        if list(values or []) != expected:
            errors.append(f"status axis {name} declares {values!r}, authorized is {expected}")
        observed_value = axis.get("observed_at_registration")
        if observed_value is None:
            errors.append(f"status axis {name} records no observed value")
        elif str(observed_value) not in (values or []):
            errors.append(
                f"status axis {name} observed {observed_value!r}, which is not one of its "
                f"declared values {values!r}"
            )
        elif str(observed_value) == "PASS":
            errors.append(
                f"status axis {name} is registered PASS; a registration cannot establish a "
                "commissioning verdict"
            )
        blocker = axis.get("blocker")
        if blocker and str(blocker) not in predicates:
            errors.append(f"status axis {name}: blocker {blocker!r} is not a declared predicate")
    for name in axes:
        if name not in REQUIRED_STATUS_AXES:
            errors.append(f"status axis {name} is outside the authorized axis set")

    # --- predicates --------------------------------------------------------
    for name, predicate in predicates.items():
        if not isinstance(predicate, dict):
            errors.append(f"predicate {name} is not a mapping")
            continue
        authority = predicate.get("class")
        if str(authority) not in AUTHORITY_CLASSES:
            errors.append(f"predicate {name}: class {authority!r} is not an authority class")
        requirement_keys = [
            key for key in ("requires_all", "pass_requires_all", "axes") if key in predicate
        ]
        if len(requirement_keys) != 1:
            errors.append(
                f"predicate {name} must declare exactly one of requires_all / "
                f"pass_requires_all / axes, found {requirement_keys}"
            )
            continue
        entries = predicate[requirement_keys[0]]
        if not isinstance(entries, list) or not entries:
            errors.append(f"predicate {name}: {requirement_keys[0]} is empty")
            continue
        seen: list[str] = []
        for item in entries:
            if not isinstance(item, dict) or "id" not in item or "axis" not in item:
                errors.append(f"predicate {name}: malformed requirement entry {item!r}")
                continue
            seen.append(str(item["id"]))
        repeated = sorted({value for value in seen if seen.count(value) > 1})
        if repeated:
            errors.append(f"predicate {name}: duplicate requirement ids {repeated}")
        target = predicate.get("projects")
        if target and str(target) not in axes:
            errors.append(f"predicate {name}: projects {target!r}, which is not a status axis")
        for key in ("gates", "does_not_gate", "dependency_cone"):
            for referenced in predicate.get(key, []) or []:
                if not resolves(str(referenced)):
                    errors.append(f"predicate {name}: {key} {referenced!r} does not resolve")

    # --- hard-vs-soft semantics -------------------------------------------
    for pair in REQUIRED_HARD_EDGES:
        kinds = observed.get(pair)
        if not kinds:
            errors.append(f"required hard edge is missing: {pair[0]} -> {pair[1]}")
        elif "HARD_PREREQUISITE" not in kinds:
            errors.append(
                f"hard prerequisite weakened: {pair[0]} -> {pair[1]} is {sorted(kinds)}"
            )
    kinds = observed.get(REQUIRED_NONSERIALIZING_EDGE)
    if not kinds:
        errors.append(
            "the Poker School commissioning edge is missing: "
            f"{REQUIRED_NONSERIALIZING_EDGE[0]} -> {REQUIRED_NONSERIALIZING_EDGE[1]}"
        )
    elif kinds != {"NONSERIALIZING_COMMISSIONING"}:
        errors.append(
            f"the Poker School commissioning edge is {sorted(kinds)}, not "
            "NONSERIALIZING_COMMISSIONING"
        )
    for (source, target), kinds in observed.items():
        if source == REQUIRED_NONSERIALIZING_EDGE[0] and target.startswith("DSH-"):
            illegal = kinds - {"REOPENS_ON_DEFECT"}
            if illegal:
                errors.append(
                    f"Poker School serializes DSH: {source} -> {target} is {sorted(illegal)}"
                )
        if source == AGENT_LIGHTNING_NODE and target in AGENT_LIGHTNING_NOT_PREDECESSOR_OF:
            errors.append(f"{AGENT_LIGHTNING_NODE} is declared a predecessor of {target}")

    poker = predicates.get(POKER_SCHOOL_PREDICATE)
    if not isinstance(poker, dict):
        errors.append(f"predicate {POKER_SCHOOL_PREDICATE} is missing")
    else:
        exempt = {str(value) for value in poker.get("does_not_gate", []) or []}
        missing = [name for name in POKER_SCHOOL_MUST_NOT_GATE if name not in exempt]
        if missing:
            errors.append(
                f"{POKER_SCHOOL_PREDICATE} no longer exempts {missing}; the Captain/source "
                "blocker would serialize them"
            )
    lightning = next(
        (entry for entry in nodes if isinstance(entry, dict) and entry.get("id") == AGENT_LIGHTNING_NODE),
        None,
    )
    if lightning is None:
        errors.append(f"node {AGENT_LIGHTNING_NODE} is missing")
    else:
        declared = {str(value) for value in lightning.get("not_a_predecessor_of", []) or []}
        missing = [name for name in AGENT_LIGHTNING_NOT_PREDECESSOR_OF if name not in declared]
        if missing:
            errors.append(f"node {AGENT_LIGHTNING_NODE} no longer excludes {missing}")

    # --- pending-dependency containment ------------------------------------
    for path, value in walk(graph):
        if not PENDING_ONLY_PATTERN.search(value):
            continue
        if not path.startswith(f"graph.predicates.{PENDING_ONLY_PREDICATE}"):
            errors.append(
                f"control #31/#32 semantics appear outside the authorized pending-dependency "
                f"predicate at {path}"
            )

    # --- discoverability through the manifest ------------------------------
    try:
        planning = manifest_planning(sources[MANIFEST])
    except GraphSyntaxError as error:
        errors.append(f"manifest planning block does not parse: {error}")
    else:
        pointer = planning.get("dependency_graph")
        if not isinstance(pointer, dict):
            errors.append("docs/manifest.yaml declares no planning.dependency_graph pointer")
        else:
            if pointer.get("schema") != SCHEMA:
                errors.append(
                    f"manifest pointer schema {pointer.get('schema')!r} does not match {SCHEMA!r}"
                )
            location = str(pointer.get("location", ""))
            path, _, anchor = location.partition("#")
            if path not in sources:
                errors.append(f"manifest pointer names an unknown file: {location}")
            elif anchor != GRAPH_ANCHOR or section_text(sources[path], anchor) is None:
                errors.append(f"manifest pointer does not resolve to the graph: {location}")
            if pointer.get("validator") != SELF:
                errors.append(
                    f"manifest names validator {pointer.get('validator')!r}; this graph's "
                    f"enforcement owner is {SELF}"
                )
        if planning.get("roadmap") != ROADMAP:
            errors.append(
                f"manifest planning.roadmap {planning.get('roadmap')!r} is not the graph owner"
            )
    if GRAPH_ANCHOR not in sources[LIFECYCLE]:
        errors.append(
            f"{LIFECYCLE} no longer points at the dependency graph it defers dependency "
            "representation to"
        )

    return errors


# --------------------------------------------------------------------------
# Watched-red controls
# --------------------------------------------------------------------------


def read_sources(root: Path) -> dict[str, str]:
    return {name: (root / name).read_text(encoding="utf-8") for name in SOURCE_FILES}


def _replace(sources: dict[str, str], name: str, old: str, new: str) -> dict[str, str]:
    text = sources[name]
    if old not in text:
        raise AssertionError(f"control fixture no longer applies: {old!r} absent from {name}")
    mutated = dict(sources)
    mutated[name] = text.replace(old, new, 1)
    return mutated


SBX_3_NODE = (
    "  - id: SBX-3\n"
    '    owner: "docs/development/ROADMAP.md#sbx-3--minimal-deterministic-lifecycle"\n'
    "    planning_state: SEQUENCED\n"
)
SBX_1_NODE = (
    "  - id: SBX-1\n"
    '    owner: "docs/development/ROADMAP.md#sbx-1--sandboxprovider--lifecycle-state-contract"\n'
    "    planning_state: SEQUENCED\n"
)
SDLC_L1_NODE = (
    "  - id: SDLC-L1\n"
    '    owner: "docs/development/ROADMAP.md#sdlc-l1--authorization-gate-hooks"\n'
    "    planning_state: SEQUENCED\n"
)


def controls(sources: dict[str, str]) -> list[tuple[str, dict[str, str], str]]:
    """One planted defect per property, with the error it must produce.

    Each fixture is chosen so the planted defect is the *only* thing that goes
    wrong. A control that goes red for an unrelated reason proves nothing about
    the property it is named after, so the expected fragment is asserted too.
    """
    return [
        (
            "duplicate node identity",
            _replace(sources, ROADMAP, SBX_3_NODE, SBX_3_NODE + SBX_3_NODE),
            "duplicate node identities",
        ),
        (
            "dangling edge endpoint",
            _replace(
                sources,
                ROADMAP,
                "  - from: DSH-1\n    to: FUT-007\n",
                "  - from: DSH-1\n    to: FUT-999\n",
            ),
            "edge endpoint does not resolve",
        ),
        (
            "unknown edge kind",
            _replace(
                sources,
                ROADMAP,
                "  - from: BOUND-1\n    to: SDLC-L1\n    kind: CONSTRAINS_DESIGN\n",
                "  - from: BOUND-1\n    to: SDLC-L1\n    kind: MOSTLY_REQUIRED\n",
            ),
            "uses unknown kind",
        ),
        (
            "malformed status-axis value",
            _replace(
                sources,
                ROADMAP,
                "    observed_at_registration: CNO\n",
                "    observed_at_registration: MAYBE\n",
            ),
            "which is not one of its declared values",
        ),
        (
            "status axis drifted from its authorized vocabulary",
            _replace(
                sources,
                ROADMAP,
                "    values: [PASS, FAIL, CNO]",
                "    values: [PASS, CNO, FAIL]",
            ),
            "authorized is",
        ),
        (
            "a status axis is registered PASS",
            _replace(
                sources,
                ROADMAP,
                "    values: [PASS, INCOMPLETE, BLOCKED]\n    observed_at_registration: BLOCKED\n",
                "    values: [PASS, INCOMPLETE, BLOCKED]\n    observed_at_registration: PASS\n",
            ),
            "is registered PASS",
        ),
        (
            "malformed predicate authority class",
            _replace(sources, ROADMAP, "    class: CAPTAIN_REQUIRED\n", "    class: PROBABLY_FINE\n"),
            "is not an authority class",
        ),
        (
            "registration silently promotes lifecycle state",
            _replace(
                sources,
                ROADMAP,
                SDLC_L1_NODE,
                SDLC_L1_NODE.replace("planning_state: SEQUENCED", "planning_state: ACTIVE"),
            ),
            "registration must not promote",
        ),
        (
            "graph state drifts from the owning section",
            _replace(
                sources,
                ROADMAP,
                SBX_1_NODE,
                SBX_1_NODE.replace("planning_state: SEQUENCED", "planning_state: CANDIDATE"),
            ),
            "its owning section says",
        ),
        (
            "broken hard-gate edge",
            _replace(
                sources,
                ROADMAP,
                "  - from: SBX-4\n    to: SBX-5\n    kind: HARD_PREREQUISITE\n",
                "",
            ),
            "required hard edge is missing",
        ),
        (
            "hard prerequisite weakened into a nonserializing relation",
            _replace(
                sources,
                ROADMAP,
                "  - from: WAYFINDER-1\n    to: DSH-0A\n    kind: HARD_PREREQUISITE\n",
                "  - from: WAYFINDER-1\n    to: DSH-0A\n    kind: NONSERIALIZING_COMMISSIONING\n",
            ),
            "hard prerequisite weakened",
        ),
        (
            "Poker School serialized into the DSH cone",
            _replace(
                sources,
                ROADMAP,
                "  - from: WAYFINDER-POC-1\n    to: DSH-0A\n    kind: REOPENS_ON_DEFECT\n",
                "  - from: WAYFINDER-POC-1\n    to: DSH-0A\n    kind: HARD_PREREQUISITE\n",
            ),
            "Poker School serializes DSH",
        ),
        (
            "Captain/source blocker no longer exempts DSH",
            _replace(
                sources,
                ROADMAP,
                "      - DSH-0A\n      - DSH-0B\n      - DSH-1\n",
                "      - DSH-0B\n      - DSH-1\n",
            ),
            "no longer exempts",
        ),
        (
            "owner reference no longer resolves",
            _replace(
                sources,
                ROADMAP,
                'owner: "docs/development/ROADMAP.md#al-1--agent-lightning-gated-sandbox-optimization-poc"',
                'owner: "docs/development/ROADMAP.md#al-1--renamed-away"',
            ),
            "anchor does not resolve",
        ),
        (
            "manifest pointer no longer resolves",
            _replace(
                sources,
                MANIFEST,
                "location: docs/development/ROADMAP.md#machine-readable-dependency-graph",
                "location: docs/development/ROADMAP.md#not-a-heading",
            ),
            "manifest pointer does not resolve",
        ),
        (
            "stale graph schema generation",
            _replace(
                sources,
                ROADMAP,
                f"schema: {SCHEMA}\nowner:",
                "schema: planning-dependency-graph/v0\nowner:",
            ),
            "unsupported graph schema",
        ),
        (
            "unauthorized #31/#32 semantics folded into the graph",
            _replace(
                sources,
                ROADMAP,
                "  - id: CB-1\n",
                "  - id: CB-1\n    note: >\n      adopts the #31 HQC completeness architecture\n",
            ),
            "outside the authorized pending-dependency",
        ),
        (
            "malformed graph fails closed instead of being skipped",
            _replace(sources, ROADMAP, "  - from: SBX-0\n", "  - {from: SBX-0}\n"),
            "failing closed",
        ),
        (
            "the graph block itself disappears",
            _replace(sources, ROADMAP, GRAPH_HEADING, "## Dependency notes"),
            "could-not-observe",
        ),
        (
            # The exact F4 defect: dropping this edge leaves the FUT-001 umbrella
            # SEQUENCED, edge-less and unjustified, with prose as its sole owner.
            "a SEQUENCED node has neither a typed edge nor an independence disposition",
            _replace(
                sources,
                ROADMAP,
                "  - from: WAYFINDER-1\n    to: FUT-001\n    kind: HARD_PREREQUISITE\n    why: >\n",
                "  - from: WAYFINDER-1\n    to: WAYFINDER-POC-1\n    kind: SOFT_UNLOCK\n    why: >\n",
            ),
            "is SEQUENCED but participates in no typed edge",
        ),
        (
            "an independence disposition contradicts a hard prerequisite",
            _replace(
                sources,
                ROADMAP,
                "independent_nodes:\n",
                'independent_nodes:\n  - id: SBX-8\n    why: "planted contradiction"\n',
            ),
            "independent while it is the target of a hard prerequisite",
        ),
        (
            "the manifest stops naming this validator as the enforcement owner",
            _replace(
                sources,
                MANIFEST,
                f"validator: {SELF}",
                "validator: docs/validation/check_something_else.py",
            ),
            "enforcement owner is",
        ),
        (
            "the lifecycle owner stops pointing at the graph",
            _replace(sources, LIFECYCLE, GRAPH_ANCHOR, "some-other-section"),
            "no longer points at the dependency graph",
        ),
    ]


def main() -> int:
    root = ROOT
    for name in SOURCE_FILES:
        if not (root / name).is_file():
            print(f"FAIL: could-not-observe: {name} is missing")
            return 1
    sources = read_sources(root)

    # Positive non-vacuity case first: the real graph must be green, or the
    # controls below would only prove that a broken checker rejects everything.
    errors = evaluate(sources)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    executed = controls(sources)
    failures: list[str] = []
    for label, mutated, expected in executed:
        observed = evaluate(mutated)
        if not observed:
            failures.append(f"watched-red control did not go red: {label}")
        elif not any(expected in error for error in observed):
            # Red for an unrelated reason proves nothing about this property.
            failures.append(
                f"watched-red control went red for the wrong reason: {label} "
                f"(expected {expected!r}, observed {observed!r})"
            )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    graph = parse(graph_block(sources[ROADMAP]))
    print(
        f"planning-dependency-graph: PASS "
        f"(schema {graph['schema']}, {len(graph['nodes'])} nodes, "
        f"{len(graph['edges'])} edges, {len(graph['predicates'])} predicates, "
        f"{len(graph['status_axes'])} status axes)"
    )
    print("watched-red: " + ", ".join(label for label, _, _ in executed))
    print(f"watched-red controls executed: {len(executed)}")
    print("provider-calls: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
