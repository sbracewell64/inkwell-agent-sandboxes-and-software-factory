"""Validate the append-only SSSF planning-event producer contract.

Three outcomes:
  0 PASS                 - feed and watched-red controls are observed-good
  1 FAIL                 - an observed contract violation exists
  2 COULD_NOT_OBSERVE    - required Git/source evidence could not be observed
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
FEED = ROOT / "docs" / "development" / "PLANNING_EVENTS.jsonl"
SCHEMA = "sssf-planning-event/v1"

PRIMARY_STATES = (
    "EXPLORE",
    "PRESERVE",
    "CANDIDATE",
    "DECIDED",
    "SEQUENCED",
    "ACTIVE",
    "PROVEN",
)
SIDE_STATES = ("DEFERRED", "REJECTED", "SUPERSEDED")
STATES = frozenset((*PRIMARY_STATES, *SIDE_STATES))

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
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
INCREMENT_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")

SNAPSHOT_FIELDS = (
    "schema",
    "event_id",
    "kind",
    "source_commit",
    "states",
    "authoritative_refs",
    "actionability",
)
TRANSITION_FIELDS = (
    "schema",
    "event_id",
    "kind",
    "item_id",
    "from",
    "to",
    "source_commit",
    "authoritative_refs",
    "actionability",
)
ACTIVE_FIELDS = (*TRANSITION_FIELDS, "increment_id")


class ObservationGap(RuntimeError):
    pass


def git_run(*args: str) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=15,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise ObservationGap(f"git unavailable while observing {' '.join(args)}: {exc}") from exc


def commit_and_refs_observable(commit: str, refs: list[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    gaps: list[str] = []

    result = git_run("cat-file", "-e", f"{commit}^{{commit}}")
    if result.returncode != 0:
        gaps.append(f"source commit is not observable: {commit}")
        return errors, gaps

    result = git_run("merge-base", "--is-ancestor", commit, "HEAD")
    if result.returncode == 1:
        errors.append(f"source commit is not an ancestor of the feed head: {commit}")
        return errors, gaps
    if result.returncode != 0:
        gaps.append(f"could not establish source-commit ancestry: {commit}")
        return errors, gaps

    for ref in refs:
        result = git_run("cat-file", "-t", f"{commit}:{ref}")
        if result.returncode != 0:
            gaps.append(f"authoritative ref is not observable at {commit}: {ref}")
        elif result.stdout.strip() != "blob":
            errors.append(f"authoritative ref is not a file blob at {commit}: {ref}")
    return errors, gaps


def safe_ref(value: object) -> bool:
    if not isinstance(value, str) or not value or not SAFE_PATH_RE.fullmatch(value):
        return False
    if value.startswith("/") or "//" in value or not value.startswith("docs/"):
        return False
    parts = PurePosixPath(value).parts
    return all(part not in ("", ".", "..") for part in parts)


def validate_refs(value: object, label: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if not isinstance(value, list) or not value:
        return [f"{label}: authoritative_refs must be a nonempty list"], []
    if len(value) != len(set(item for item in value if isinstance(item, str))):
        errors.append(f"{label}: authoritative_refs contain duplicates")
    for ref in value:
        if not safe_ref(ref):
            errors.append(f"{label}: unsafe authoritative ref: {ref!r}")
    return errors, []


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
        if not line:
            errors.append(f"line {index}: blank records are forbidden")
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {index}: malformed JSON: {exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"line {index}: record must be a JSON object")
            continue
        compact = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
        if compact != line:
            errors.append(f"line {index}: record is not compact canonical JSON")
        records.append(record)
    return records, errors


def validate_text(text: str, *, check_git: bool) -> tuple[list[str], list[str]]:
    records, errors = parse_lines(text)
    gaps: list[str] = []
    if not records:
        return errors or ["feed has no parseable records"], gaps

    seen_ids: set[str] = set()
    previous_id = ""
    states: dict[str, str] = {}
    snapshot_count = 0

    for index, record in enumerate(records, start=1):
        label = f"line {index}"
        schema = record.get("schema")
        event_id = record.get("event_id")
        kind = record.get("kind")

        if schema != SCHEMA:
            errors.append(f"{label}: schema must be {SCHEMA}")
        if not isinstance(event_id, str) or not EVENT_ID_RE.fullmatch(event_id):
            errors.append(f"{label}: invalid event_id")
        else:
            if event_id in seen_ids:
                errors.append(f"{label}: duplicate event_id: {event_id}")
            if previous_id and event_id <= previous_id:
                errors.append(f"{label}: event_id is not strictly increasing: {event_id}")
            seen_ids.add(event_id)
            previous_id = event_id

        if kind == "snapshot":
            snapshot_count += 1
            if tuple(record) != SNAPSHOT_FIELDS:
                errors.append(f"{label}: snapshot fields/order differ from the contract")
            if index != 1:
                errors.append(f"{label}: snapshot must be the first record")
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
            to_state = record.get("to")
            expected_fields = ACTIVE_FIELDS if to_state == "ACTIVE" else TRANSITION_FIELDS
            if tuple(record) != expected_fields:
                errors.append(f"{label}: transition fields/order differ from the contract")

            item_id = record.get("item_id")
            from_state = record.get("from")
            actionability = record.get("actionability")
            if not isinstance(item_id, str) or not ITEM_ID_RE.fullmatch(item_id):
                errors.append(f"{label}: invalid item_id")
            if from_state not in STATES:
                errors.append(f"{label}: invalid from state: {from_state!r}")
            if to_state not in STATES:
                errors.append(f"{label}: invalid to state: {to_state!r}")

            if isinstance(item_id, str) and ITEM_ID_RE.fullmatch(item_id) and from_state in STATES:
                if item_id in states:
                    if states[item_id] != from_state:
                        errors.append(
                            f"{label}: stale from state for {item_id}: declared {from_state}, current {states[item_id]}"
                        )
                elif from_state != "EXPLORE":
                    errors.append(f"{label}: new item {item_id} must originate from EXPLORE")

            if from_state in LEGAL_EDGES and to_state in STATES:
                if to_state not in LEGAL_EDGES[from_state]:
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
                        errors.append(
                            f"{label}: ACTIVE transition must reference its increment under docs/increments/"
                        )
            else:
                if actionability != "awareness":
                    errors.append(f"{label}: non-ACTIVE transition actionability must be awareness")
                if "increment_id" in record:
                    errors.append(f"{label}: non-ACTIVE transition must not carry increment_id")

            if (
                isinstance(item_id, str)
                and ITEM_ID_RE.fullmatch(item_id)
                and from_state in STATES
                and to_state in STATES
                and (item_id not in states or states.get(item_id) == from_state)
                and to_state in LEGAL_EDGES.get(from_state, frozenset())
            ):
                states[item_id] = to_state
        else:
            errors.append(f"{label}: kind must be snapshot or transition")

        source_commit = record.get("source_commit")
        if not isinstance(source_commit, str) or not COMMIT_RE.fullmatch(source_commit):
            errors.append(f"{label}: source_commit must be a full lowercase 40-hex commit id")

        ref_errors, _ = validate_refs(record.get("authoritative_refs"), label)
        errors.extend(ref_errors)
        refs = record.get("authoritative_refs")
        if (
            check_git
            and isinstance(source_commit, str)
            and COMMIT_RE.fullmatch(source_commit)
            and isinstance(refs, list)
            and refs
            and all(safe_ref(ref) for ref in refs)
        ):
            try:
                git_errors, git_gaps = commit_and_refs_observable(source_commit, refs)
            except ObservationGap as exc:
                gaps.append(str(exc))
            else:
                errors.extend(f"{label}: {message}" for message in git_errors)
                gaps.extend(f"{label}: {message}" for message in git_gaps)

    if snapshot_count != 1:
        errors.append(f"feed must contain exactly one snapshot; observed {snapshot_count}")
    return errors, gaps


def load_feed(path: Path = FEED) -> tuple[str | None, list[str]]:
    if path.is_symlink():
        return None, ["feed path is a symlink"]
    if not path.is_file():
        return None, ["feed is missing or not a regular file"]
    try:
        return path.read_text(encoding="utf-8"), []
    except (OSError, UnicodeError) as exc:
        return None, [f"feed could not be observed: {exc}"]


def record(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema": SCHEMA,
        "event_id": "plan-20260818-0002",
        "kind": "transition",
        "item_id": "FUT-004",
        "from": "EXPLORE",
        "to": "PRESERVE",
        "source_commit": "56b4542a38af8e4435da0fa32ac12497aa6f6016",
        "authoritative_refs": ["docs/development/FUTURE_CANDIDATES.md"],
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
        errors, gaps = validate_text(text, check_git=False)
        messages = [*errors, *gaps]
        if not messages:
            failures.append(f"control {name}: defective feed stayed green")
        elif needle and not any(needle in message for message in messages):
            failures.append(f"control {name}: expected diagnostic containing {needle!r}; got {messages!r}")

    require_red("malformed-json", snapshot + "\n{\n", "malformed JSON")
    require_red("duplicate-id", snapshot + "\n" + compact(record(event_id="plan-20260818-0001")) + "\n", "duplicate event_id")
    require_red("out-of-order-id", snapshot + "\n" + compact(record(event_id="plan-20260817-9999")) + "\n", "not strictly increasing")
    require_red("second-snapshot", snapshot + "\n" + snapshot.replace("0001", "0002", 1) + "\n", "only one snapshot")
    require_red("illegal-edge", snapshot + "\n" + compact(record(item_id="FUT-001", from_state="SEQUENCED", to="PROVEN")) + "\n", "illegal planning transition")
    require_red("stale-from", snapshot + "\n" + compact(record(item_id="FUT-001", from_state="DECIDED", to="SUPERSEDED")) + "\n", "stale from state")
    require_red("unsafe-ref", snapshot + "\n" + compact(record(authoritative_refs=["docs/../outside.md"])) + "\n", "unsafe authoritative ref")
    require_red("non-active-engineering", snapshot + "\n" + compact(record(actionability="engineering")) + "\n", "non-ACTIVE transition actionability")

    active = record(item_id="FUT-001", from_state="SEQUENCED", to="ACTIVE", actionability="engineering")
    require_red("active-without-increment", snapshot + "\n" + compact(active) + "\n", "requires a concrete increment_id")

    bad_snapshot = json.loads(snapshot)
    bad_snapshot["actionability"] = "engineering"
    require_red("actionable-bootstrap", compact(bad_snapshot) + "\n", "snapshot actionability must be baseline")

    # Git/source observation controls use the production observer against bounded
    # one-record variants. Missing evidence is a non-pass but remains distinct
    # from an observed schema defect.
    missing_commit = json.loads(snapshot)
    missing_commit["source_commit"] = "0" * 40
    errors, gaps = validate_text(compact(missing_commit) + "\n", check_git=True)
    if errors or not gaps or not any("source commit is not observable" in gap for gap in gaps):
        failures.append(f"control missing-source-commit: expected CNO gap, got errors={errors!r} gaps={gaps!r}")

    missing_ref = json.loads(snapshot)
    missing_ref["authoritative_refs"] = ["docs/development/DOES_NOT_EXIST.md"]
    errors, gaps = validate_text(compact(missing_ref) + "\n", check_git=True)
    if errors or not gaps or not any("authoritative ref is not observable" in gap for gap in gaps):
        failures.append(f"control missing-authoritative-ref: expected CNO gap, got errors={errors!r} gaps={gaps!r}")

    return failures


def main() -> int:
    text, read_gaps = load_feed()
    if read_gaps:
        print("FP-001 planning event producer: COULD_NOT_OBSERVE")
        for gap in read_gaps:
            print(f"- {gap}")
        return 2
    assert text is not None

    errors, gaps = validate_text(text, check_git=True)
    if errors:
        print("FP-001 planning event producer: FAIL")
        for error in errors:
            print(f"- {error}")
        for gap in gaps:
            print(f"- additional observation gap: {gap}")
        return 1
    if gaps:
        print("FP-001 planning event producer: COULD_NOT_OBSERVE")
        for gap in gaps:
            print(f"- {gap}")
        return 2

    control_failures = watched_red_errors(text)
    if control_failures:
        print("FP-001 planning event producer: FAIL")
        for failure in control_failures:
            print(f"- {failure}")
        return 1

    records, _ = parse_lines(text)
    snapshot = records[0]
    states = snapshot["states"]
    assert isinstance(states, dict)
    print("FP-001 planning event producer: PASS")
    print(f"records={len(records)} bootstrap_snapshot=1 current_states={len(states)}")
    print("watched-red: malformed/duplicate/order/snapshot/edge/stale/path/actionability/ACTIVE-binding")
    print("watched-red: missing source commit and missing authoritative ref remain could-not-observe")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
