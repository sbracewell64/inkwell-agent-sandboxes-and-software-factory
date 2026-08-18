"""Validate the append-only SSSF planning-event producer contract.

This is an offline validator. CI intentionally checks out only the exact head at
fetch-depth 1, so historical source commits are not assumed locally available.
Each record therefore binds its historical authority with two immutable axes:
`source_commit` plus the exact Git blob id for every `authoritative_ref`.
FirstMate independently re-observes those commit/path/blob bindings before it
accepts an event.

Exit codes:
  0 PASS
  1 FAIL
  2 COULD_NOT_OBSERVE
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[2]
FEED = ROOT / "docs" / "development" / "PLANNING_EVENTS.jsonl"
SCHEMA = "sssf-planning-event/v1"

STATES = frozenset(
    (
        "EXPLORE", "PRESERVE", "CANDIDATE", "DECIDED", "SEQUENCED",
        "ACTIVE", "PROVEN", "DEFERRED", "REJECTED", "SUPERSEDED",
    )
)
LEGAL_EDGES: dict[str, frozenset[str]] = {
    "EXPLORE": frozenset(("PRESERVE", "CANDIDATE", "DEFERRED", "REJECTED")),
    "PRESERVE": frozenset(("CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "CANDIDATE": frozenset(("DECIDED", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "DECIDED": frozenset(("SEQUENCED", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "SEQUENCED": frozenset(("ACTIVE", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "ACTIVE": frozenset(("PROVEN", "DEFERRED", "SUPERSEDED")),
    "PROVEN": frozenset(("SUPERSEDED",)),
    "DEFERRED": frozenset(("CANDIDATE", "DECIDED", "SEQUENCED", "REJECTED", "SUPERSEDED")),
    "REJECTED": frozenset(),
    "SUPERSEDED": frozenset(),
}

EVENT_ID_RE = re.compile(r"^plan-[0-9]{8}-[0-9]{4}$")
ITEM_ID_RE = re.compile(r"^FUT-[0-9]{3}$")
OID_RE = re.compile(r"^[0-9a-f]{40}$")
INCREMENT_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

SNAPSHOT_FIELDS = (
    "schema", "event_id", "kind", "source_commit", "states",
    "authoritative_refs", "authoritative_blobs", "actionability",
)
TRANSITION_FIELDS = (
    "schema", "event_id", "kind", "item_id", "from", "to", "source_commit",
    "authoritative_refs", "authoritative_blobs", "actionability",
)
ACTIVE_FIELDS = (*TRANSITION_FIELDS, "increment_id")


def safe_ref(value: object) -> bool:
    if not isinstance(value, str) or not value or not PATH_RE.fullmatch(value):
        return False
    if value.startswith("/") or not value.startswith("docs/") or "//" in value:
        return False
    return all(part not in ("", ".", "..") for part in PurePosixPath(value).parts)


def validate_source_witness(record: dict[str, object], label: str) -> list[str]:
    errors: list[str] = []
    source_commit = record.get("source_commit")
    if not isinstance(source_commit, str) or not OID_RE.fullmatch(source_commit):
        errors.append(f"{label}: source_commit must be a full lowercase 40-hex Git object id")

    refs = record.get("authoritative_refs")
    blobs = record.get("authoritative_blobs")
    if not isinstance(refs, list) or not refs:
        errors.append(f"{label}: authoritative_refs must be a nonempty list")
        return errors
    if refs != sorted(refs):
        errors.append(f"{label}: authoritative_refs must be sorted")
    if len(refs) != len(set(ref for ref in refs if isinstance(ref, str))):
        errors.append(f"{label}: authoritative_refs contain duplicates")
    for ref in refs:
        if not safe_ref(ref):
            errors.append(f"{label}: unsafe authoritative ref: {ref!r}")

    if not isinstance(blobs, dict) or not blobs:
        errors.append(f"{label}: authoritative_blobs must be a nonempty object")
        return errors
    if list(blobs) != sorted(blobs):
        errors.append(f"{label}: authoritative_blobs keys must be sorted")
    if set(blobs) != set(ref for ref in refs if isinstance(ref, str)):
        errors.append(f"{label}: authoritative_blobs must bind exactly authoritative_refs")
    for path, oid in blobs.items():
        if not safe_ref(path):
            errors.append(f"{label}: unsafe authoritative blob path: {path!r}")
        if not isinstance(oid, str) or not OID_RE.fullmatch(oid):
            errors.append(f"{label}: authoritative blob id must be full lowercase 40-hex: {path!r}")
    return errors


def parse_lines(text: str) -> tuple[list[dict[str, object]], list[str]]:
    errors: list[str] = []
    if not text.endswith("\n"):
        errors.append("feed must end with one LF")
    if "\r" in text:
        errors.append("feed contains CR bytes")
    if text.startswith("\ufeff"):
        errors.append("feed contains a UTF-8 BOM")
    lines = text.splitlines()
    if not lines:
        return [], [*errors, "feed is empty"]
    records: list[dict[str, object]] = []
    for index, line in enumerate(lines, start=1):
        label = f"line {index}"
        if not line:
            errors.append(f"{label}: blank records are forbidden")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{label}: malformed JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"{label}: record must be a JSON object")
            continue
        if json.dumps(record, separators=(",", ":"), ensure_ascii=False) != line:
            errors.append(f"{label}: record is not compact canonical JSON")
        records.append(record)
    return records, errors


def validate_text(text: str) -> list[str]:
    records, errors = parse_lines(text)
    if not records:
        return errors or ["feed has no parseable records"]
    seen_ids: set[str] = set()
    previous_id = ""
    states: dict[str, str] = {}
    snapshot_count = 0

    for index, record in enumerate(records, start=1):
        label = f"line {index}"
        if record.get("schema") != SCHEMA:
            errors.append(f"{label}: schema must be {SCHEMA}")
        event_id = record.get("event_id")
        if not isinstance(event_id, str) or not EVENT_ID_RE.fullmatch(event_id):
            errors.append(f"{label}: invalid event_id")
        else:
            if event_id in seen_ids:
                errors.append(f"{label}: duplicate event_id: {event_id}")
            if previous_id and event_id <= previous_id:
                errors.append(f"{label}: event_id is not strictly increasing: {event_id}")
            seen_ids.add(event_id)
            previous_id = event_id

        kind = record.get("kind")
        if kind == "snapshot":
            snapshot_count += 1
            if tuple(record) != SNAPSHOT_FIELDS:
                errors.append(f"{label}: snapshot fields/order differ from the contract")
            if index != 1:
                errors.append(f"{label}: snapshot must be first")
            if snapshot_count != 1:
                errors.append(f"{label}: only one snapshot is allowed")
            if record.get("actionability") != "baseline":
                errors.append(f"{label}: snapshot actionability must be baseline")
            raw_states = record.get("states")
            if not isinstance(raw_states, dict) or not raw_states:
                errors.append(f"{label}: snapshot states must be a nonempty object")
            else:
                if list(raw_states) != sorted(raw_states):
                    errors.append(f"{label}: snapshot state keys must be sorted")
                for item_id, state in raw_states.items():
                    if not isinstance(item_id, str) or not ITEM_ID_RE.fullmatch(item_id):
                        errors.append(f"{label}: invalid snapshot item id: {item_id!r}")
                    if state not in STATES:
                        errors.append(f"{label}: invalid snapshot state for {item_id}: {state!r}")
                    elif isinstance(item_id, str):
                        states[item_id] = state
        elif kind == "transition":
            item_id = record.get("item_id")
            from_state = record.get("from")
            to_state = record.get("to")
            actionability = record.get("actionability")
            expected_fields = ACTIVE_FIELDS if to_state == "ACTIVE" else TRANSITION_FIELDS
            if tuple(record) != expected_fields:
                errors.append(f"{label}: transition fields/order differ from the contract")
            if not isinstance(item_id, str) or not ITEM_ID_RE.fullmatch(item_id):
                errors.append(f"{label}: invalid item_id")
            if from_state not in STATES:
                errors.append(f"{label}: invalid from state: {from_state!r}")
            if to_state not in STATES:
                errors.append(f"{label}: invalid to state: {to_state!r}")
            if isinstance(item_id, str) and ITEM_ID_RE.fullmatch(item_id) and from_state in STATES:
                current = states.get(item_id)
                if current is None and from_state != "EXPLORE":
                    errors.append(f"{label}: new item {item_id} must originate from EXPLORE")
                elif current is not None and current != from_state:
                    errors.append(f"{label}: stale from state for {item_id}: declared {from_state}, current {current}")
            legal = from_state in LEGAL_EDGES and to_state in STATES and to_state in LEGAL_EDGES[from_state]
            if from_state in STATES and to_state in STATES and not legal:
                errors.append(f"{label}: illegal planning transition: {from_state} -> {to_state}")
            if to_state == "ACTIVE":
                if actionability != "engineering":
                    errors.append(f"{label}: ACTIVE transition actionability must be engineering")
                increment_id = record.get("increment_id")
                if not isinstance(increment_id, str) or not INCREMENT_RE.fullmatch(increment_id):
                    errors.append(f"{label}: ACTIVE transition requires a concrete increment_id")
                refs = record.get("authoritative_refs")
                if isinstance(increment_id, str) and isinstance(refs, list):
                    prefix = f"docs/increments/{increment_id}"
                    if not any(isinstance(ref, str) and ref.startswith(prefix) for ref in refs):
                        errors.append(f"{label}: ACTIVE transition must reference its increment")
            else:
                if actionability != "awareness":
                    errors.append(f"{label}: non-ACTIVE transition actionability must be awareness")
                if "increment_id" in record:
                    errors.append(f"{label}: non-ACTIVE transition must not carry increment_id")
            if (
                isinstance(item_id, str) and ITEM_ID_RE.fullmatch(item_id)
                and from_state in STATES and to_state in STATES and legal
                and (item_id not in states or states.get(item_id) == from_state)
            ):
                states[item_id] = to_state
        else:
            errors.append(f"{label}: kind must be snapshot or transition")
        errors.extend(validate_source_witness(record, label))

    if snapshot_count != 1:
        errors.append(f"feed must contain exactly one snapshot; observed {snapshot_count}")
    return errors


def load_feed(path: Path = FEED) -> tuple[str | None, str | None]:
    if path.is_symlink():
        return None, "feed path is a symlink"
    if not path.is_file():
        return None, "feed is missing or not a regular file"
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeError) as exc:
        return None, f"feed could not be observed: {exc}"


def transition(**overrides: object) -> dict[str, object]:
    ref = "docs/development/FUTURE_CANDIDATES.md"
    base: dict[str, object] = {
        "schema": SCHEMA,
        "event_id": "plan-20260818-0002",
        "kind": "transition",
        "item_id": "FUT-004",
        "from": "EXPLORE",
        "to": "PRESERVE",
        "source_commit": "1" * 40,
        "authoritative_refs": [ref],
        "authoritative_blobs": {ref: "2" * 40},
        "actionability": "awareness",
    }
    base.update(overrides)
    return base


def compact(obj: dict[str, object]) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def watched_red_errors(honest_text: str) -> list[str]:
    failures: list[str] = []
    snapshot = honest_text.splitlines()[0]
    def require_red(name: str, text: str, needle: str | None = None) -> None:
        messages = validate_text(text)
        if not messages:
            failures.append(f"control {name}: defective feed stayed green")
        elif needle and not any(needle in message for message in messages):
            failures.append(f"control {name}: expected {needle!r}; got {messages!r}")
    require_red("malformed-json", snapshot + "\n{\n", "malformed JSON")
    require_red("duplicate-id", snapshot + "\n" + compact(transition(event_id="plan-20260818-0001")) + "\n", "duplicate event_id")
    require_red("out-of-order-id", snapshot + "\n" + compact(transition(event_id="plan-20260817-9999")) + "\n", "not strictly increasing")
    require_red("second-snapshot", snapshot + "\n" + snapshot.replace("plan-20260818-0001", "plan-20260818-0002", 1) + "\n", "only one snapshot")
    require_red("illegal-edge", snapshot + "\n" + compact(transition(**{"item_id":"FUT-001","from":"SEQUENCED","to":"PROVEN"})) + "\n", "illegal planning transition")
    require_red("stale-from", snapshot + "\n" + compact(transition(**{"item_id":"FUT-001","from":"DECIDED","to":"SUPERSEDED"})) + "\n", "stale from state")
    require_red("unsafe-ref", snapshot + "\n" + compact(transition(authoritative_refs=["docs/../outside.md"], authoritative_blobs={"docs/../outside.md":"2"*40})) + "\n", "unsafe authoritative ref")
    require_red("missing-blob-binding", snapshot + "\n" + compact(transition(authoritative_blobs={})) + "\n", "authoritative_blobs")
    require_red("bad-blob-id", snapshot + "\n" + compact(transition(authoritative_blobs={"docs/development/FUTURE_CANDIDATES.md":"not-an-oid"})) + "\n", "blob id")
    require_red("bad-source-id", snapshot + "\n" + compact(transition(source_commit="main")) + "\n", "source_commit")
    require_red("non-active-engineering", snapshot + "\n" + compact(transition(actionability="engineering")) + "\n", "non-ACTIVE transition actionability")
    active = transition(**{"item_id":"FUT-001","from":"SEQUENCED","to":"ACTIVE","actionability":"engineering"})
    require_red("active-without-increment", snapshot + "\n" + compact(active) + "\n", "requires a concrete increment_id")
    bad_snapshot = json.loads(snapshot)
    bad_snapshot["actionability"] = "engineering"
    require_red("actionable-bootstrap", compact(bad_snapshot) + "\n", "snapshot actionability must be baseline")
    return failures


def main() -> int:
    text, gap = load_feed()
    if gap:
        print("FP-001 planning event producer: COULD_NOT_OBSERVE")
        print(f"- {gap}")
        return 2
    assert text is not None
    errors = validate_text(text)
    if errors:
        print("FP-001 planning event producer: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    controls = watched_red_errors(text)
    if controls:
        print("FP-001 planning event producer: FAIL")
        for failure in controls:
            print(f"- {failure}")
        return 1
    records, _ = parse_lines(text)
    states = records[0]["states"]
    assert isinstance(states, dict)
    print("FP-001 planning event producer: PASS")
    print(f"records={len(records)} bootstrap_snapshot=1 current_states={len(states)}")
    print("source witness: exact source commit + exact Git blob id per authoritative ref")
    print("watched-red: framing/schema/order/snapshot/state/path/source/blob/actionability/ACTIVE-binding")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
