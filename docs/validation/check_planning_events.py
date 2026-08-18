#!/usr/bin/env python3
"""Validate the Browser-Sol-managed SSSF planning transition feed.

The feed is a notification index, never the authority it points at.  This
validator is intentionally offline: it reads tracked repository bytes and Git
objects only and never contacts a forge or model.

Exit codes:
  0 observed-good
  1 observed-bad
  2 could-not-observe
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
FEED_REL = "docs/development/PLANNING_EVENTS.jsonl"
FEED = ROOT / FEED_REL
SCHEMA = "sssf-planning-event/v1"
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
EVENT_ID = re.compile(r"^plan-[0-9]{8}-[0-9]{4}$")
ITEM_ID = re.compile(r"^FUT-[0-9]{3}$")
INCREMENT_ID = re.compile(r"^[A-Z][A-Z0-9-]*[0-9][A-Z0-9-]*$")

STATES = {
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

# Main promotion path plus explicit side exits.  DEFERRED work requires a new
# authoritative transition back into the main path; it never silently resumes.
EDGES = {
    "EXPLORE": {"PRESERVE", "CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "PRESERVE": {"CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "CANDIDATE": {"DECIDED", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "DECIDED": {"SEQUENCED", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "SEQUENCED": {"ACTIVE", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "ACTIVE": {"PROVEN", "DEFERRED", "REJECTED", "SUPERSEDED"},
    "DEFERRED": {"PRESERVE", "CANDIDATE", "DECIDED", "SEQUENCED", "ACTIVE", "REJECTED", "SUPERSEDED"},
    "PROVEN": {"SUPERSEDED"},
    "REJECTED": set(),
    "SUPERSEDED": set(),
}


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def safe_ref(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if "\\" in value or "\x00" in value or value.startswith("/"):
        return False
    p = PurePosixPath(value)
    if any(part in {"", ".", ".."} for part in p.parts):
        return False
    return value.startswith("docs/")


def load_lines(path: Path) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    if not path.exists() or not path.is_file() or path.is_symlink():
        return [], [f"feed unavailable or unsafe: {FEED_REL}"]
    raw = path.read_bytes()
    if not raw:
        return [], ["feed is empty"]
    if not raw.endswith(b"\n"):
        errors.append("feed must end with one complete LF-terminated record")
    records: list[dict] = []
    for number, line in enumerate(raw.splitlines(), 1):
        if not line:
            errors.append(f"line {number}: blank records are forbidden")
            continue
        try:
            text = line.decode("utf-8")
            obj = json.loads(text)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"line {number}: malformed JSON: {exc}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"line {number}: record must be a JSON object")
            continue
        # Canonical compact one-line form makes prefix continuity byte-stable.
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if text != canonical:
            errors.append(f"line {number}: record is not canonical compact sorted JSON")
        records.append(obj)
    return records, errors


def validate(records: list[dict], *, check_git: bool = True) -> list[str]:
    errors: list[str] = []
    if not records:
        return ["no planning records were observed"]

    seen_ids: set[str] = set()
    expected_seq = 1
    bootstrap_count = 0

    for idx, r in enumerate(records, 1):
        prefix = f"line {idx}"
        allowed = {
            "schema", "sequence", "event_id", "kind", "source_commit",
            "actionability", "item_id", "from", "to", "states",
            "authoritative_refs", "increments",
        }
        extra = sorted(set(r) - allowed)
        if extra:
            errors.append(f"{prefix}: unknown fields: {', '.join(extra)}")

        if r.get("schema") != SCHEMA:
            errors.append(f"{prefix}: schema must be {SCHEMA}")
        seq = r.get("sequence")
        if type(seq) is not int or seq != expected_seq:
            errors.append(f"{prefix}: sequence must be exactly {expected_seq}")
        expected_seq += 1

        eid = r.get("event_id")
        if not isinstance(eid, str) or not EVENT_ID.fullmatch(eid):
            errors.append(f"{prefix}: invalid event_id")
        elif eid in seen_ids:
            errors.append(f"{prefix}: duplicate event_id {eid}")
        else:
            seen_ids.add(eid)

        source = r.get("source_commit")
        if not isinstance(source, str) or not FULL_SHA.fullmatch(source):
            errors.append(f"{prefix}: source_commit must be a full lowercase 40-hex commit id")
            source = None
        elif check_git:
            observed = git("cat-file", "-e", f"{source}^{{commit}}")
            if observed.returncode != 0:
                errors.append(f"{prefix}: source_commit is not an observable commit: {source}")

        refs = r.get("authoritative_refs")
        if not isinstance(refs, list) or not refs or len(refs) != len(set(map(str, refs))):
            errors.append(f"{prefix}: authoritative_refs must be a nonempty unique list")
            refs = []
        for ref in refs:
            if not safe_ref(ref):
                errors.append(f"{prefix}: unsafe authoritative ref: {ref!r}")
                continue
            if source and check_git:
                observed = git("cat-file", "-e", f"{source}:{ref}")
                if observed.returncode != 0:
                    errors.append(f"{prefix}: authoritative ref absent at source_commit: {ref}")

        kind = r.get("kind")
        actionability = r.get("actionability")
        if kind == "bootstrap":
            bootstrap_count += 1
            if idx != 1:
                errors.append(f"{prefix}: bootstrap must be the first record")
            if actionability != "awareness":
                errors.append(f"{prefix}: bootstrap must be awareness-only")
            if any(k in r for k in ("item_id", "from", "to")):
                errors.append(f"{prefix}: bootstrap cannot carry a transition")
            states = r.get("states")
            if not isinstance(states, dict) or not states:
                errors.append(f"{prefix}: bootstrap requires nonempty states")
            else:
                for item, state in states.items():
                    if not ITEM_ID.fullmatch(str(item)):
                        errors.append(f"{prefix}: invalid bootstrap item id: {item}")
                    if state not in STATES:
                        errors.append(f"{prefix}: invalid bootstrap state for {item}: {state}")
        elif kind == "transition":
            item = r.get("item_id")
            before = r.get("from")
            after = r.get("to")
            if not isinstance(item, str) or not ITEM_ID.fullmatch(item):
                errors.append(f"{prefix}: transition requires valid item_id")
            if before not in STATES or after not in STATES:
                errors.append(f"{prefix}: transition states must be closed-set")
            elif after not in EDGES.get(before, set()):
                errors.append(f"{prefix}: illegal planning edge {before} -> {after}")
            if after == "ACTIVE":
                if actionability != "engineering":
                    errors.append(f"{prefix}: ACTIVE must be engineering-intake eligible")
                increments = r.get("increments")
                if not isinstance(increments, list) or not increments:
                    errors.append(f"{prefix}: ACTIVE requires at least one increment binding")
                else:
                    for inc in increments:
                        if not isinstance(inc, str) or not INCREMENT_ID.fullmatch(inc):
                            errors.append(f"{prefix}: invalid increment identity: {inc!r}")
            elif actionability != "awareness":
                errors.append(f"{prefix}: non-ACTIVE transitions must be awareness-only")
        else:
            errors.append(f"{prefix}: kind must be bootstrap or transition")

    if bootstrap_count != 1:
        errors.append(f"feed must contain exactly one bootstrap record; observed {bootstrap_count}")
    return errors


def check_append_only() -> tuple[list[str], bool]:
    """Compare current feed to first-parent bytes when that parent has a feed."""
    parent = git("rev-parse", "HEAD^")
    if parent.returncode != 0:
        return [], False
    old = git("show", f"{parent.stdout.strip()}:{FEED_REL}")
    if old.returncode != 0:
        return [], False  # introduction commit
    current = FEED.read_bytes()
    prior = old.stdout.encode("utf-8")
    if not current.startswith(prior):
        return ["feed is not append-only relative to first parent"], True
    return [], True


def controls(base: list[dict]) -> list[str]:
    failures: list[str] = []

    def must_fail(name: str, mutator) -> None:
        candidate = copy.deepcopy(base)
        mutator(candidate)
        if not validate(candidate, check_git=False):
            failures.append(f"watched-red {name}: defective feed unexpectedly passed")

    must_fail("duplicate-id", lambda r: r.append({**r[0], "sequence": 2}))
    must_fail("second-bootstrap", lambda r: r.append({**r[0], "sequence": 2, "event_id": "plan-20260818-0002"}))
    must_fail("bootstrap-actionable", lambda r: r[0].__setitem__("actionability", "engineering"))
    must_fail("bad-source-width", lambda r: r[0].__setitem__("source_commit", "abc"))
    must_fail("unsafe-ref", lambda r: r[0].__setitem__("authoritative_refs", ["../outside"]))
    must_fail("unknown-state", lambda r: r[0]["states"].__setitem__("FUT-001", "MAYBE"))

    def illegal_edge(r: list[dict]) -> None:
        r.append({
            "schema": SCHEMA,
            "sequence": 2,
            "event_id": "plan-20260818-0002",
            "kind": "transition",
            "source_commit": "0" * 40,
            "actionability": "awareness",
            "item_id": "FUT-003",
            "from": "PRESERVE",
            "to": "PROVEN",
            "authoritative_refs": ["docs/development/FUTURE_CANDIDATES.md"],
        })
    must_fail("illegal-edge", illegal_edge)

    def active_without_increment(r: list[dict]) -> None:
        r.append({
            "schema": SCHEMA,
            "sequence": 2,
            "event_id": "plan-20260818-0002",
            "kind": "transition",
            "source_commit": "0" * 40,
            "actionability": "engineering",
            "item_id": "FUT-004",
            "from": "SEQUENCED",
            "to": "ACTIVE",
            "authoritative_refs": ["docs/development/FUTURE_CANDIDATES.md"],
        })
    must_fail("active-without-increment", active_without_increment)
    return failures


def main() -> int:
    records, parse_errors = load_lines(FEED)
    errors = parse_errors + validate(records)
    append_errors, compared = check_append_only() if FEED.exists() else ([], False)
    errors += append_errors

    control_errors: list[str] = []
    if "--controls" in sys.argv and records:
        control_errors = controls(records)
        errors += control_errors

    if errors:
        print("FP-001 planning event feed: FAIL")
        for err in errors:
            print(f"- {err}")
        return 1

    print("FP-001 planning event feed: PASS")
    print(f"- records: {len(records)}")
    print("- bootstrap: exactly one, first, awareness-only")
    print("- event/state/transition vocabulary: closed-set")
    print("- source commits and authoritative refs: exact and observable")
    print("- ACTIVE: requires engineering actionability plus increment binding")
    print(f"- append-only first-parent comparison: {'checked' if compared else 'not-applicable (feed introduction)'}")
    if "--controls" in sys.argv:
        print("- watched-red controls: duplicate id, second/actionable bootstrap, bad source identity, unsafe ref, unknown state, illegal edge, ACTIVE without increment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
