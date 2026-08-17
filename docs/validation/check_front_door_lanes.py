#!/usr/bin/env python3
"""HD-14 front-door lane and exception-contract control.

Every operator front door of this repository must carry exactly one lane
classification drawn from the machine-readable taxonomy, and every taxonomy
entry must state both what its lane is FOR and, decisively, the claims that
cannot be made from it. The defect this closes is a claim, not a crash: direct
steering changes source or decides progression, and an operator later cites
normal SSSF trace and acceptance guarantees that never wrapped that work.

The assertion here is a PROPERTY, not a proxy. A keyword search would pass on a
mention in prose, so nothing below searches for a keyword near a command:

- the front-door set is DISCOVERED from the `just` module/import graph bytes,
  never from a hand-maintained list, and a recipe with no registry entry is an
  unlabelled front door;
- each registry entry's lane is resolved by structural lookup in the taxonomy,
  so a lane value outside the taxonomy has nowhere to resolve;
- each taxonomy entry's cannot-claim statement is read as a structured field and
  must be nonempty, so the negative half cannot be omitted;
- the human-facing documents are parsed as tables and fenced command blocks and
  compared against the registry, so documentation cannot drift from the labels.

Every control is calibrated watched-red on each run against bounded mutations of
the real registry document. A control that stays green against its own defect
proves nothing, so this validator fails when that happens rather than reporting
a pass it did not earn.

Three-valued throughout: an unreadable file, an absent document, an empty
discovery, and an unknown schema version are COULD_NOT_OBSERVE, which is never
a pass.
"""

from __future__ import annotations

import copy
import json
import re
import shutil
import sys
import tempfile
from enum import Enum
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TAXONOMY_PATH = ROOT / "docs/reference/front_door_taxonomy.json"
LANES_DOC_PATH = ROOT / "docs/reference/FRONT_DOOR_LANES.md"
COMMANDS_DOC_PATH = ROOT / "docs/reference/COMMANDS.md"
ROOT_JUSTFILE = ROOT / "justfile"

SCHEMA_VERSION = "sssf.front-door-taxonomy.v1"

REQUIRED_LANES = ("adw", "lifecycle", "steering")
REQUIRED_EXCEPTIONS = ("direct-claude-steering", "host-orchestrator", "pi-child")

# The three carriers the HD-14 audit named. Discovery that loses any of them has
# stopped describing this repository, whatever else it found.
NAMED_CARRIERS = ("just local cc", "just sbx orch cc", "just sbx run agent")

DISCOVERY_KINDS = ("just-graph", "documented")


class Observation(Enum):
    OBSERVED_GOOD = "observed-good"
    OBSERVED_BAD = "observed-bad"
    COULD_NOT_OBSERVE = "could-not-observe"


class DiscoveryError(Exception):
    """The just graph could not be read as a whole — could-not-observe."""


# ── front-door discovery from the just graph bytes ──────────────────────────

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
ASSIGNMENT = re.compile(r"^(export\s+)?[A-Za-z_][A-Za-z0-9_-]*\s*:=")
MOD_WITH_PATH = re.compile(r"^mod\s+(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s+'(?P<path>[^']+)'\s*$")
MOD_BARE = re.compile(r"^mod\s+(?P<name>[A-Za-z_][A-Za-z0-9_-]*)\s*$")
IMPORT = re.compile(r"^import\s+'(?P<path>[^']+)'\s*$")
ALIAS = re.compile(r"^alias\s+")
RECIPE = re.compile(r"^@?(?P<name>[A-Za-z_][A-Za-z0-9_-]*)(?P<params>[^:]*):")


def _mask_quoted(line: str) -> str:
    """Blank out quoted spans so a colon or `:=` inside a default value cannot
    be mistaken for recipe or assignment syntax."""
    return QUOTED.sub(lambda match: "\x00" * len(match.group(0)), line)


def _resolve_bare_module(directory: Path, name: str) -> Path:
    candidates = [directory / f"{name}.just", directory / name / "mod.just", directory / name / "justfile"]
    present = [candidate for candidate in candidates if candidate.is_file()]
    if len(present) != 1:
        raise DiscoveryError(
            f"bare `mod {name}` in {directory} resolved to {len(present)} files; expected exactly one"
        )
    return present[0]


def _scan(
    path: Path,
    prefix: str,
    root: Path,
    found: dict[str, dict[str, object]],
    visiting: set[Path],
) -> None:
    resolved = path.resolve()
    if resolved in visiting:
        raise DiscoveryError(f"cycle in the just graph at {path}")
    if not path.is_file():
        raise DiscoveryError(f"just graph references a missing file: {path}")
    visiting.add(resolved)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise DiscoveryError(f"unreadable just file {path}: {error}") from error

    relative = resolved.relative_to(root).as_posix()
    for number, raw in enumerate(text.splitlines(), 1):
        if not raw or raw[0] in " \t":
            continue  # recipe bodies and blank lines
        line = raw.rstrip()
        if line.startswith("#") or line.startswith("[") or line.startswith("set "):
            continue

        # `mod` and `import` carry a quoted path, so they are matched on the
        # unmasked line; masking exists only to keep a quoted default value from
        # being read as recipe or assignment syntax.
        module = MOD_WITH_PATH.match(line)
        if module:
            _scan(
                path.parent / module.group("path"),
                f"{prefix} {module.group('name')}",
                root,
                found,
                visiting,
            )
            continue
        module = MOD_BARE.match(line)
        if module:
            target = _resolve_bare_module(path.parent, module.group("name"))
            _scan(target, f"{prefix} {module.group('name')}", root, found, visiting)
            continue
        imported = IMPORT.match(line)
        if imported:
            # An import shares the importing module's namespace, so the
            # invocation prefix does not change.
            _scan(path.parent / imported.group("path"), prefix, root, found, visiting)
            continue

        masked = _mask_quoted(line)
        if ASSIGNMENT.match(masked) or ALIAS.match(masked):
            continue

        recipe = RECIPE.match(masked)
        if recipe:
            invocation = f"{prefix} {recipe.group('name')}"
            if invocation in found:
                raise DiscoveryError(f"duplicate front door {invocation!r} at {relative}:{number}")
            found[invocation] = {"source": relative, "recipe": recipe.group("name"), "line": number}
            continue

        # Anything the grammar above does not cover is a construct this
        # discovery has never been calibrated against. Refuse rather than skip:
        # a silently skipped line is exactly how a front door goes unlabelled.
        raise DiscoveryError(f"unclassified just syntax at {relative}:{number}: {line!r}")
    visiting.discard(resolved)


def discover_front_doors(
    root_justfile: Path = ROOT_JUSTFILE,
    root: Path | None = None,
) -> dict[str, dict[str, object]]:
    found: dict[str, dict[str, object]] = {}
    _scan(root_justfile, "just", root or ROOT, found, set())
    if not found:
        raise DiscoveryError("the just graph yielded no front doors at all")
    return found


# ── taxonomy loading ────────────────────────────────────────────────────────


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    keys = [key for key, _ in pairs]
    duplicates = {key for key in keys if keys.count(key) > 1}
    if duplicates:
        raise ValueError(f"duplicate JSON keys: {sorted(duplicates)}")
    return dict(pairs)


def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict[str, object]:
    raw = path.read_text(encoding="utf-8")
    return json.loads(raw, object_pairs_hook=_reject_duplicate_keys)


# ── the structural property ─────────────────────────────────────────────────


def _nonempty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _nonempty_statement_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_text(item) for item in value)


def validate_taxonomy(
    document: object,
    discovered: dict[str, dict[str, object]],
) -> list[str]:
    """Return every way `document` fails to be a complete lane taxonomy for
    `discovered`. An empty list means the property holds.

    This is the single function every watched-red control mutates against, so
    the controls calibrate the same code the real check runs.
    """
    issues: list[str] = []
    if not isinstance(document, dict):
        return ["taxonomy: document is not a JSON object"]
    if document.get("schema_version") != SCHEMA_VERSION:
        return [f"taxonomy: unknown schema_version {document.get('schema_version')!r}"]

    lanes = document.get("lanes")
    if not isinstance(lanes, dict):
        return ["taxonomy: `lanes` is not an object"]
    if tuple(sorted(lanes)) != tuple(sorted(REQUIRED_LANES)):
        issues.append(f"taxonomy: lanes must be exactly {sorted(REQUIRED_LANES)}, got {sorted(lanes)}")

    for lane_id, lane in sorted(lanes.items()):
        if not isinstance(lane, dict):
            issues.append(f"lane {lane_id}: entry is not an object")
            continue
        if not _nonempty_text(lane.get("allowed_purpose")):
            issues.append(f"lane {lane_id}: allowed_purpose is missing or empty")
        # The negative half is not optional. A taxonomy that says only what a
        # lane IS leaves exactly the gap that produced this defect.
        if not _nonempty_statement_list(lane.get("cannot_claim")):
            issues.append(f"lane {lane_id}: cannot_claim statement is missing or empty")
        for flag in ("may_claim_adw_acceptance", "may_claim_workflow_success"):
            if not isinstance(lane.get(flag), bool):
                issues.append(f"lane {lane_id}: {flag} must be a boolean")
        if lane_id != "adw":
            if lane.get("may_claim_adw_acceptance") is not False:
                issues.append(f"lane {lane_id}: a non-ADW lane must not claim ADW acceptance")
            if lane.get("may_claim_workflow_success") is not False:
                issues.append(f"lane {lane_id}: a non-ADW lane must not claim SSSF workflow success")

    exceptions = document.get("exceptions")
    if not isinstance(exceptions, dict):
        return issues + ["taxonomy: `exceptions` is not an object"]
    for required in REQUIRED_EXCEPTIONS:
        if required not in exceptions:
            issues.append(f"taxonomy: required exception {required!r} is absent")

    for exception_id, exception in sorted(exceptions.items()):
        if not isinstance(exception, dict):
            issues.append(f"exception {exception_id}: entry is not an object")
            continue
        lane_id = exception.get("lane")
        if lane_id not in lanes:
            issues.append(f"exception {exception_id}: lane {lane_id!r} is outside the taxonomy")
        if not _nonempty_text(exception.get("allowed_purpose")):
            issues.append(f"exception {exception_id}: allowed_purpose is missing or empty")
        if not _nonempty_statement_list(exception.get("cannot_claim")):
            issues.append(f"exception {exception_id}: cannot_claim statement is missing or empty")
        for flag in ("may_claim_adw_acceptance", "may_claim_workflow_success"):
            if not isinstance(exception.get(flag), bool):
                issues.append(f"exception {exception_id}: {flag} must be a boolean")
        if lane_id != "adw":
            if exception.get("may_claim_adw_acceptance") is not False:
                issues.append(
                    f"exception {exception_id}: a {lane_id} exception must not claim ADW acceptance"
                )
            if exception.get("may_claim_workflow_success") is not False:
                issues.append(
                    f"exception {exception_id}: a {lane_id} exception must not claim SSSF workflow success"
                )

    front_doors = document.get("front_doors")
    if not isinstance(front_doors, list) or not front_doors:
        return issues + ["taxonomy: `front_doors` is missing or empty"]

    registered: dict[str, dict[str, object]] = {}
    for index, entry in enumerate(front_doors):
        if not isinstance(entry, dict):
            issues.append(f"front_doors[{index}]: entry is not an object")
            continue
        invocation = entry.get("invocation")
        if not _nonempty_text(invocation):
            issues.append(f"front_doors[{index}]: invocation is missing or empty")
            continue
        assert isinstance(invocation, str)
        if invocation in registered:
            issues.append(f"front door {invocation!r}: registered more than once")
            continue
        registered[invocation] = entry

    for invocation, entry in sorted(registered.items()):
        discovery = entry.get("discovery")
        if discovery not in DISCOVERY_KINDS:
            issues.append(f"front door {invocation!r}: discovery {discovery!r} is outside {list(DISCOVERY_KINDS)}")
        lane_id = entry.get("lane")
        if lane_id not in lanes:
            issues.append(f"front door {invocation!r}: lane {lane_id!r} is outside the taxonomy")
        claimed_exceptions = entry.get("exceptions")
        if not isinstance(claimed_exceptions, list):
            issues.append(f"front door {invocation!r}: exceptions must be a list")
            claimed_exceptions = []
        for claimed in claimed_exceptions:
            if claimed not in exceptions:
                issues.append(f"front door {invocation!r}: exception {claimed!r} is outside the taxonomy")
                continue
            declared_lane = exceptions[claimed].get("lane")
            if declared_lane != lane_id:
                issues.append(
                    f"front door {invocation!r}: exception {claimed!r} belongs to lane "
                    f"{declared_lane!r}, not {lane_id!r}"
                )
        if not _nonempty_text(entry.get("summary")):
            issues.append(f"front door {invocation!r}: summary is missing or empty")
        source = entry.get("source")
        if not _nonempty_text(source):
            issues.append(f"front door {invocation!r}: source is missing or empty")
        elif discovery == "documented":
            # A just recipe's source is reconciled against discovery below. A
            # documented command has no graph to check it against, so its source
            # must at least be a file that exists.
            assert isinstance(source, str)
            if not (ROOT / source).is_file():
                issues.append(f"front door {invocation!r}: source {source!r} is not a file")

        acceptance = entry.get("deterministic_acceptance")
        if not isinstance(acceptance, bool):
            issues.append(f"front door {invocation!r}: deterministic_acceptance must be a boolean")
            continue
        success = entry.get("may_claim_workflow_success")
        if not isinstance(success, bool):
            issues.append(f"front door {invocation!r}: may_claim_workflow_success must be a boolean")
            continue
        # The exact acceptance rule: ONLY ADW plus deterministic acceptance may
        # claim SSSF workflow success.
        entitled = lane_id == "adw" and acceptance
        if success != entitled:
            issues.append(
                f"front door {invocation!r}: may_claim_workflow_success is {success}, but lane "
                f"{lane_id!r} with deterministic_acceptance={acceptance} entitles it to {entitled}"
            )

    graph_entries = {
        invocation: entry
        for invocation, entry in registered.items()
        if entry.get("discovery") == "just-graph"
    }
    for invocation in sorted(discovered):
        if invocation not in registered:
            issues.append(f"front door {invocation!r}: UNLABELLED — no entry in the lane taxonomy")
            continue
        if registered[invocation].get("discovery") != "just-graph":
            issues.append(
                f"front door {invocation!r}: discovered in the just graph but registered as "
                f"{registered[invocation].get('discovery')!r}"
            )
            continue
        expected_source = discovered[invocation]["source"]
        if registered[invocation].get("source") != expected_source:
            issues.append(
                f"front door {invocation!r}: registered source "
                f"{registered[invocation].get('source')!r} is not the discovered {expected_source!r}"
            )
    for invocation in sorted(graph_entries):
        if invocation not in discovered:
            issues.append(f"front door {invocation!r}: registered as a just recipe that does not exist")

    return issues


# ── documentation surfaces ──────────────────────────────────────────────────

TABLE_ROW = re.compile(r"^\|\s*`(?P<invocation>[^`]+)`\s*\|(?P<rest>.*)\|\s*$")
FENCE = re.compile(r"^```")
HEADING = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.*?)\s*$")
CONTRACT_HEADING = re.compile(r"^`(?P<identifier>[^`]+)`(?:\s+—.*)?$")


def _normalise_prose(text: str) -> str:
    """Compare statements ignoring markdown code formatting and line wrapping.

    The document may render `just sbx run agent` as code and wrap a statement
    across lines; neither changes what the statement says. Nothing else is
    normalised, so a reworded statement still fails.
    """
    return " ".join(text.replace("`", "").split())


def _contract_sections(text: str) -> tuple[dict[tuple[str, str], str], list[str]]:
    sections: dict[tuple[str, str], list[str]] = {}
    issues: list[str] = []
    group: str | None = None
    active: tuple[str, str] | None = None

    for line in text.splitlines():
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group("marks"))
            title = heading.group("title")
            if level == 2:
                group = {"Lanes": "lane", "Exceptions": "exception"}.get(title)
            if level <= 3:
                active = None
            contract = CONTRACT_HEADING.match(title) if level == 3 and group else None
            if contract:
                key = (group, contract.group("identifier"))
                if key in sections:
                    issues.append(
                        f"FRONT_DOOR_LANES.md: duplicate {group} section `{key[1]}`"
                    )
                else:
                    sections[key] = []
                    active = key
            continue
        if active is not None:
            sections[active].append(line)

    return {key: "\n".join(lines) for key, lines in sections.items()}, issues


def check_lanes_document(document: dict[str, object], text: str) -> list[str]:
    """Every registered front door must appear in the lane document's table with
    its registered lane, and every lane and exception must have a section that
    carries its cannot-claim statement word for word."""
    issues: list[str] = []
    sections, section_issues = _contract_sections(text)
    issues.extend(section_issues)
    rows: dict[str, str] = {}
    for line in text.splitlines():
        match = TABLE_ROW.match(line.rstrip())
        if not match:
            continue
        cells = [cell.strip() for cell in match.group("rest").split("|")]
        rows[match.group("invocation").strip()] = cells[0] if cells else ""

    front_doors = document.get("front_doors")
    assert isinstance(front_doors, list)
    for entry in front_doors:
        assert isinstance(entry, dict)
        invocation = entry["invocation"]
        if invocation not in rows:
            issues.append(f"FRONT_DOOR_LANES.md: front door `{invocation}` has no labelled table row")
            continue
        declared = rows[invocation].strip("` ")
        if declared != entry["lane"]:
            issues.append(
                f"FRONT_DOOR_LANES.md: `{invocation}` is documented as lane {declared!r} but "
                f"registered as {entry['lane']!r}"
            )

    lanes = document.get("lanes")
    exceptions = document.get("exceptions")
    assert isinstance(lanes, dict) and isinstance(exceptions, dict)
    for group, label in ((lanes, "lane"), (exceptions, "exception")):
        for identifier, definition in sorted(group.items()):
            assert isinstance(definition, dict)
            section = sections.get((label, identifier))
            if section is None:
                issues.append(f"FRONT_DOOR_LANES.md: missing {label} section `{identifier}`")
                continue
            prose = _normalise_prose(section)
            for statement in definition["cannot_claim"]:
                if _normalise_prose(statement) not in prose:
                    issues.append(
                        f"FRONT_DOOR_LANES.md: {label} `{identifier}` is missing its cannot-claim "
                        f"statement: {statement}"
                    )
    return issues


def _fenced_command_lines(text: str) -> list[str]:
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        if inside and line.strip():
            lines.append(line.strip())
    return lines


def check_commands_document(document: dict[str, object], text: str) -> list[str]:
    """Every command the command reference shows an operator must resolve to a
    registered front door, and the reference must state that front door's lane
    where the operator meets it."""
    issues: list[str] = []
    front_doors = document.get("front_doors")
    assert isinstance(front_doors, list)
    registry = {entry["invocation"]: entry for entry in front_doors}  # type: ignore[index]

    # The reference must carry the lane at the point of contact, as a structural
    # row, not a keyword in prose.
    rows: dict[str, str] = {}
    for line in text.splitlines():
        match = TABLE_ROW.match(line.rstrip())
        if not match:
            continue
        cells = [cell.strip() for cell in match.group("rest").split("|")]
        rows[match.group("invocation").strip()] = cells[0] if cells else ""

    shown = {invocation for invocation in rows if invocation in registry}
    for command in _fenced_command_lines(text):
        tokens = command.split()
        resolved = None
        for size in range(len(tokens), 0, -1):
            candidate = " ".join(tokens[:size])
            if candidate in registry:
                resolved = candidate
                break
        if resolved is None:
            # A command shown in a code block that resolves to nothing is a
            # front door the reference presents without a label.
            issues.append(f"COMMANDS.md: `{command}` resolves to no registered front door")
            continue
        shown.add(resolved)

    documented = {entry["invocation"] for entry in front_doors if entry.get("discovery") == "documented"}  # type: ignore[index]
    for invocation in sorted(documented - shown):
        issues.append(
            f"COMMANDS.md: `{invocation}` is registered as a documented command but the reference "
            "does not show it"
        )

    for invocation in sorted(shown):
        if invocation not in rows:
            issues.append(f"COMMANDS.md: `{invocation}` is shown without a labelled lane row")
            continue
        declared = rows[invocation].strip("` ")
        if declared != registry[invocation]["lane"]:
            issues.append(
                f"COMMANDS.md: `{invocation}` is labelled {declared!r} but registered as "
                f"{registry[invocation]['lane']!r}"
            )
    return issues


# ── watched-red controls ────────────────────────────────────────────────────


def _first_entry(document: dict[str, object], predicate) -> dict[str, object] | None:
    front_doors = document.get("front_doors")
    assert isinstance(front_doors, list)
    for entry in front_doors:
        if isinstance(entry, dict) and predicate(entry):
            return entry
    return None


def _remove_one_front_door(document: dict[str, object]) -> str | None:
    """Delete the entry for a real, discovered front door — the audit's named
    control: an UNLABELLED front door must fail the docs lint."""
    front_doors = document["front_doors"]
    assert isinstance(front_doors, list)
    for index, entry in enumerate(front_doors):
        if isinstance(entry, dict) and entry.get("invocation") in NAMED_CARRIERS:
            del front_doors[index]
            return str(entry["invocation"])
    return None


def _lane_outside_taxonomy(document: dict[str, object]) -> str | None:
    entry = _first_entry(document, lambda item: item.get("discovery") == "just-graph")
    if entry is None:
        return None
    entry["lane"] = "workflow-success"
    return str(entry["invocation"])


def _drop_cannot_claim(document: dict[str, object]) -> str | None:
    exceptions = document["exceptions"]
    assert isinstance(exceptions, dict)
    for identifier in REQUIRED_EXCEPTIONS:
        if identifier in exceptions:
            exceptions[identifier]["cannot_claim"] = []
            return identifier
    return None


def _steering_claims_adw_acceptance(document: dict[str, object]) -> str | None:
    exceptions = document["exceptions"]
    assert isinstance(exceptions, dict)
    for identifier in ("direct-claude-steering", "host-orchestrator"):
        if identifier in exceptions:
            exceptions[identifier]["may_claim_adw_acceptance"] = True
            return identifier
    return None


def _steering_claims_workflow_success(document: dict[str, object]) -> str | None:
    entry = _first_entry(document, lambda item: item.get("lane") == "steering")
    if entry is None:
        return None
    entry["may_claim_workflow_success"] = True
    return str(entry["invocation"])


def _adw_without_acceptance_claims_success(document: dict[str, object]) -> str | None:
    entry = _first_entry(
        document,
        lambda item: item.get("lane") == "adw" and item.get("deterministic_acceptance") is False,
    )
    if entry is None:
        return None
    entry["may_claim_workflow_success"] = True
    return str(entry["invocation"])


MUTATIONS = (
    ("unlabelled-front-door", _remove_one_front_door),
    ("lane-value-outside-taxonomy", _lane_outside_taxonomy),
    ("taxonomy-entry-without-cannot-claim", _drop_cannot_claim),
    ("steering-exception-claims-adw-acceptance", _steering_claims_adw_acceptance),
    ("steering-front-door-claims-workflow-success", _steering_claims_workflow_success),
    ("adw-without-acceptance-claims-workflow-success", _adw_without_acceptance_claims_success),
)


def watched_red_controls(
    document: dict[str, object],
    discovered: dict[str, dict[str, object]],
) -> tuple[list[str], list[str]]:
    """Run each bounded defect against the real registry. Returns
    (failures, observed-red control lines)."""
    failures: list[str] = []
    observed: list[str] = []
    for name, mutate in MUTATIONS:
        mutated = copy.deepcopy(document)
        target = mutate(mutated)
        if target is None:
            failures.append(f"control {name}: the real registry offered no site to mutate")
            continue
        issues = validate_taxonomy(mutated, discovered)
        if not issues:
            failures.append(f"control {name}: stayed green against its own defect, so it proves nothing")
            continue
        observed.append(f"{name} (at {target}): red, {len(issues)} issue(s) — {issues[0]}")
    return failures, observed


def discovery_is_real_control() -> list[str]:
    """Prove discovery reads the just bytes rather than a memorised list: copy
    the graph, add a recipe, and require the copy to yield exactly one more
    front door than the original."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="sssf-hd14-discovery-") as directory:
        temp = Path(directory)
        shutil.copy2(ROOT_JUSTFILE, temp / "justfile")
        shutil.copytree(ROOT / "just", temp / "just")

        baseline = set(discover_front_doors(temp / "justfile", temp))
        target = temp / "just" / "local.just"
        target.write_text(
            target.read_text(encoding="utf-8")
            + "\n\n# synthetic control recipe\nhd14-discovery-control:\n    @echo control\n",
            encoding="utf-8",
        )
        widened = set(discover_front_doors(temp / "justfile", temp))
        added = widened - baseline
        if added != {"just local hd14-discovery-control"}:
            failures.append(
                "control discovery-reads-the-bytes: adding a recipe did not surface exactly that "
                f"recipe; saw {sorted(added)}"
            )
    return failures


# ── entry point ─────────────────────────────────────────────────────────────


def main() -> int:
    could_not_observe: list[str] = []
    failures: list[str] = []

    try:
        discovered = discover_front_doors()
    except DiscoveryError as error:
        print("HD-14 front-door lane taxonomy: COULD-NOT-OBSERVE")
        print(f"- front-door discovery: {error}")
        return 1

    missing_carriers = [carrier for carrier in NAMED_CARRIERS if carrier not in discovered]
    if missing_carriers:
        print("HD-14 front-door lane taxonomy: COULD-NOT-OBSERVE")
        print(f"- discovery lost the audit's named carriers: {missing_carriers}")
        return 1

    if not TAXONOMY_PATH.is_file():
        could_not_observe.append(f"the lane taxonomy is absent: {TAXONOMY_PATH.relative_to(ROOT)}")
    if not LANES_DOC_PATH.is_file():
        could_not_observe.append(f"the lane document is absent: {LANES_DOC_PATH.relative_to(ROOT)}")
    if not COMMANDS_DOC_PATH.is_file():
        could_not_observe.append(f"the command reference is absent: {COMMANDS_DOC_PATH.relative_to(ROOT)}")
    if could_not_observe:
        print("HD-14 front-door lane taxonomy: COULD-NOT-OBSERVE")
        print(f"- {len(discovered)} front doors were discovered and none of them can be shown labelled")
        for reason in could_not_observe:
            print(f"- {reason}")
        for invocation in sorted(discovered):
            print(f"- UNLABELLED front door: {invocation}")
        return 1

    try:
        document = load_taxonomy()
    except (OSError, ValueError) as error:
        print("HD-14 front-door lane taxonomy: COULD-NOT-OBSERVE")
        print(f"- the lane taxonomy could not be read: {error}")
        return 1

    failures.extend(validate_taxonomy(document, discovered))

    if not failures:
        failures.extend(
            check_lanes_document(document, LANES_DOC_PATH.read_text(encoding="utf-8"))
        )
        failures.extend(
            check_commands_document(document, COMMANDS_DOC_PATH.read_text(encoding="utf-8"))
        )

    control_failures, observed_red = watched_red_controls(document, discovered)
    failures.extend(control_failures)
    failures.extend(discovery_is_real_control())

    if failures:
        print("HD-14 front-door lane taxonomy: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("HD-14 front-door lane taxonomy: PASS")
    print(f"discovered {len(discovered)} just front doors from the module/import graph bytes")
    print(f"every discovered front door carries a lane drawn from {list(REQUIRED_LANES)}")
    print(f"every taxonomy entry states its cannot-claim half; exceptions: {list(REQUIRED_EXCEPTIONS)}")
    print("only ADW plus deterministic acceptance is entitled to claim SSSF workflow success")
    for line in observed_red:
        print(f"watched-red control {line}")
    print("watched-red control discovery-reads-the-bytes: red on a synthetic recipe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
