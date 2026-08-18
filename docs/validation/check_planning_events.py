#!/usr/bin/env python3
"""Validate the Browser-Sol-owned SSSF planning-transition feed (FP-001).

The feed at ``docs/development/PLANNING_EVENTS.jsonl`` is a typed notification
index.  It is never the authority it points at: ``FUTURE_CANDIDATES.md``,
accepted ADRs, ``ROADMAP.md``, and named increment records remain authoritative
for their own facts.  FirstMate consumes typed transitions from this feed and
never derives execution authority from planning prose.

A record's ``source_commit`` names the already-existing authoritative planning
commit that established the state change.  The later commit that appends the
event is transport provenance, not the announced authority.  ``source_commit``
plus one exact Git blob id per authoritative ref is therefore the historical
witness; the current worktree is not.

This validator is offline: it reads tracked repository bytes and local Git
objects only.  It never contacts a forge, a network, or a model.

CI checks out at ``fetch-depth: 1``, so historical commit and blob objects are
frequently absent.  An absent object is *could-not-observe*, not a failure, and
is reported as such.  ``--require-git-witness`` upgrades every unobservable
witness axis to a failure for full-depth qualification runs.

Exit codes:
  0  observed-good  (every observable axis verified; gaps reported explicitly)
  1  observed-bad   (a contract violation was observed)
  2  could-not-observe (the feed itself could not be read)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
FEED_REL = "docs/development/PLANNING_EVENTS.jsonl"
FEED = ROOT / FEED_REL
SCHEMA_REL = "docs/development/planning_event.schema.json"
SCHEMA_PATH = ROOT / SCHEMA_REL
SCHEMA_ID = "sssf-planning-event/v1"

FULL_OID = re.compile(r"^[0-9a-f]{40}$")
EVENT_ID = re.compile(r"^plan-[0-9]{8}-[0-9]{4}$")
ITEM_ID = re.compile(r"^FUT-[0-9]{3}$")
INCREMENT_ID = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
REF_CHARS = re.compile(r"^[A-Za-z0-9._/-]+$")

# Bounds keep an awareness index from becoming an unbounded work queue.
MAX_REF_LENGTH = 200
MAX_REFS = 16
MAX_STATES = 64
MAX_INCREMENTS = 8
MAX_RECORD_BYTES = 4096

KINDS = ("bootstrap", "transition")
ACTIONABILITIES = ("awareness", "engineering")

STATES = (
    "EXPLORE", "PRESERVE", "CANDIDATE", "DECIDED", "SEQUENCED",
    "ACTIVE", "PROVEN", "DEFERRED", "REJECTED", "SUPERSEDED",
)

# PLANNING_LIFECYCLE.md defines the promotion path plus DEFERRED / REJECTED /
# SUPERSEDED as side exits.  DEFERRED work never silently resumes: re-entry to
# the main path is itself an explicit authoritative transition.
EDGES: dict[str, frozenset[str]] = {
    "EXPLORE": frozenset(("PRESERVE", "CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "PRESERVE": frozenset(("CANDIDATE", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "CANDIDATE": frozenset(("DECIDED", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "DECIDED": frozenset(("SEQUENCED", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "SEQUENCED": frozenset(("ACTIVE", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "ACTIVE": frozenset(("PROVEN", "DEFERRED", "REJECTED", "SUPERSEDED")),
    "DEFERRED": frozenset(("PRESERVE", "CANDIDATE", "DECIDED", "SEQUENCED", "ACTIVE", "REJECTED", "SUPERSEDED")),
    "PROVEN": frozenset(("SUPERSEDED",)),
    "REJECTED": frozenset(),
    "SUPERSEDED": frozenset(),
}

COMMON_FIELDS = {
    "schema", "sequence", "event_id", "kind", "source_commit",
    "actionability", "authoritative_refs", "authoritative_blobs",
}
BOOTSTRAP_FIELDS = COMMON_FIELDS | {"states"}
TRANSITION_FIELDS = COMMON_FIELDS | {"item_id", "from", "to", "increments"}


# ---------------------------------------------------------------- git access

def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )


def git_object_present(oid: str, kind: str) -> bool:
    return git("cat-file", "-e", f"{oid}^{{{kind}}}").returncode == 0


# ------------------------------------------------------------ path soundness

def safe_ref(value: object) -> str | None:
    """Return an error reason, or None when the ref is a bounded, normalized,
    repository-relative path under the governed documentation root."""
    if not isinstance(value, str) or not value:
        return "must be a nonempty string"
    if len(value) > MAX_REF_LENGTH:
        return f"exceeds {MAX_REF_LENGTH} characters"
    if not REF_CHARS.fullmatch(value):
        return "contains characters outside [A-Za-z0-9._/-]"
    if value.startswith("/"):
        return "must be repository-relative, not absolute"
    if "//" in value or value.endswith("/"):
        return "is not a normalized path"
    parts = PurePosixPath(value).parts
    if any(part in ("", ".", "..") for part in parts):
        return "contains a traversal or dot segment"
    # PurePosixPath collapses "." and "//"; compare round-trip for normalization.
    if str(PurePosixPath(value)) != value:
        return "is not a normalized path"
    if not value.startswith("docs/"):
        return "must live under the governed docs/ root"
    return None


# ------------------------------------------------------------------- parsing

def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict:
    seen: set[str] = set()
    for key, _ in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r}")
        seen.add(key)
    return dict(pairs)


def _reject_constant(name: str):
    raise ValueError(f"non-finite JSON constant {name}")


def parse_feed(raw: bytes) -> tuple[list[dict], list[str]]:
    """Framing and canonical-representation checks over raw feed bytes.

    One JSON object per line, compact, key-sorted, LF-terminated.  That exact
    representation is what makes a consumer's byte-offset + prefix-SHA-256
    cursor stable, so prefix mutation stays observable.
    """
    errors: list[str] = []
    if raw == b"":
        return [], ["feed is empty"]
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("feed carries a UTF-8 BOM")
    if b"\r" in raw:
        errors.append("feed contains CR bytes; records must be LF-framed")
    if not raw.endswith(b"\n"):
        errors.append("feed must end with one complete LF-terminated record")

    records: list[dict] = []
    for number, line in enumerate(raw.split(b"\n")[:-1] if raw.endswith(b"\n") else raw.split(b"\n"), 1):
        label = f"line {number}"
        if line == b"":
            errors.append(f"{label}: blank records are forbidden")
            continue
        if len(line) > MAX_RECORD_BYTES:
            errors.append(f"{label}: record exceeds {MAX_RECORD_BYTES} bytes")
            continue
        try:
            text = line.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{label}: malformed JSON: not valid UTF-8: {exc}")
            continue
        try:
            obj = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_constant,
            )
        except (json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{label}: malformed JSON: {exc}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"{label}: record must be a JSON object")
            continue
        canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if text != canonical:
            errors.append(f"{label}: record is not canonical compact key-sorted JSON")
        records.append(obj)
    return records, errors


# ---------------------------------------------------------------- witnessing

def witness_errors(record: dict, label: str, mode: str) -> tuple[list[str], list[str]]:
    """Validate the historical source witness.

    Returns (errors, unobservable) where `unobservable` names axes that this
    checkout genuinely cannot decide.  In mode 'require' those become errors.
    """
    errors: list[str] = []
    gaps: list[str] = []

    source = record.get("source_commit")
    if not isinstance(source, str) or not FULL_OID.fullmatch(source):
        errors.append(f"{label}: source_commit must be a full lowercase 40-hex commit id")
        source = None

    refs = record.get("authoritative_refs")
    blobs = record.get("authoritative_blobs")

    if not isinstance(refs, list) or not refs:
        errors.append(f"{label}: authoritative_refs must be a nonempty list")
        refs = []
    else:
        if len(refs) > MAX_REFS:
            errors.append(f"{label}: authoritative_refs exceeds {MAX_REFS} entries")
        if len(refs) != len({r for r in refs if isinstance(r, str)}) or any(not isinstance(r, str) for r in refs):
            errors.append(f"{label}: authoritative_refs must be unique strings")
        if refs != sorted(refs, key=lambda r: r if isinstance(r, str) else ""):
            errors.append(f"{label}: authoritative_refs must be sorted")
        for ref in refs:
            reason = safe_ref(ref)
            if reason:
                errors.append(f"{label}: unsafe authoritative ref {ref!r}: {reason}")

    if not isinstance(blobs, dict) or not blobs:
        errors.append(f"{label}: authoritative_blobs must be a nonempty object")
        return errors, gaps
    if list(blobs) != sorted(blobs):
        errors.append(f"{label}: authoritative_blobs keys must be sorted")
    if isinstance(refs, list) and set(blobs) != {r for r in refs if isinstance(r, str)}:
        errors.append(f"{label}: authoritative_blobs must bind exactly authoritative_refs")
    for path, oid in sorted(blobs.items()):
        reason = safe_ref(path)
        if reason:
            errors.append(f"{label}: unsafe authoritative blob path {path!r}: {reason}")
            continue
        if not isinstance(oid, str) or not FULL_OID.fullmatch(oid):
            errors.append(f"{label}: authoritative blob id for {path} must be a full lowercase 40-hex object id")
            continue
        if mode == "skip":
            continue
        # Strong binding, available only when the historical commit is local.
        if source and git_object_present(source, "commit"):
            observed = git("rev-parse", "--verify", "--quiet", f"{source}:{path}")
            if observed.returncode != 0:
                errors.append(f"{label}: authoritative ref absent at source_commit: {path}")
            elif observed.stdout.strip() != oid:
                errors.append(
                    f"{label}: blob binding mismatch for {path}: "
                    f"declared {oid}, observed {observed.stdout.strip()}"
                )
        elif git_object_present(oid, "blob"):
            gaps.append(f"{label}: {path}: blob present, source_commit absent (shallow checkout)")
        else:
            gaps.append(f"{label}: {path}: neither source_commit nor declared blob is local")

    if mode != "skip" and source and not git_object_present(source, "commit"):
        gaps.append(f"{label}: source_commit {source} is not a local object (shallow checkout)")

    if mode == "require":
        errors.extend(f"{gap} [--require-git-witness]" for gap in gaps)
        gaps = []
    return errors, gaps


# ------------------------------------------------------------ record grammar

def validate_records(records: list[dict], *, mode: str = "observe") -> tuple[list[str], list[str]]:
    errors: list[str] = []
    gaps: list[str] = []
    if not records:
        return ["no planning records were observed"], gaps

    seen_ids: set[str] = set()
    previous_id = ""
    current_states: dict[str, str] = {}
    bootstrap_count = 0

    for index, record in enumerate(records, 1):
        label = f"line {index}"
        kind = record.get("kind")
        actionability = record.get("actionability")

        if record.get("schema") != SCHEMA_ID:
            errors.append(f"{label}: schema must be {SCHEMA_ID}")

        sequence = record.get("sequence")
        if type(sequence) is not int or sequence != index:
            errors.append(f"{label}: sequence must be exactly {index}")

        event_id = record.get("event_id")
        if not isinstance(event_id, str) or not EVENT_ID.fullmatch(event_id):
            errors.append(f"{label}: invalid event_id")
        else:
            if event_id in seen_ids:
                errors.append(f"{label}: duplicate event_id: {event_id}")
            elif previous_id and event_id <= previous_id:
                errors.append(f"{label}: event_id is not strictly increasing: {event_id}")
            seen_ids.add(event_id)
            previous_id = event_id

        if actionability not in ACTIONABILITIES:
            errors.append(f"{label}: actionability must be one of {', '.join(ACTIONABILITIES)}")

        if kind == "bootstrap":
            bootstrap_count += 1
            extra = sorted(set(record) - BOOTSTRAP_FIELDS)
            if extra:
                errors.append(f"{label}: bootstrap carries forbidden fields: {', '.join(extra)}")
            if index != 1:
                errors.append(f"{label}: bootstrap must be the first record")
            if bootstrap_count != 1:
                errors.append(f"{label}: only one bootstrap record is allowed")
            # Mechanical non-actionability: no intake binding can exist here.
            if actionability != "awareness":
                errors.append(f"{label}: bootstrap must be awareness-only")
            for forbidden in ("item_id", "from", "to", "increments"):
                if forbidden in record:
                    errors.append(f"{label}: bootstrap must not carry {forbidden}")
            states = record.get("states")
            if not isinstance(states, dict) or not states:
                errors.append(f"{label}: bootstrap requires a nonempty states object")
            else:
                if len(states) > MAX_STATES:
                    errors.append(f"{label}: bootstrap states exceeds {MAX_STATES} entries")
                if list(states) != sorted(states):
                    errors.append(f"{label}: bootstrap state keys must be sorted")
                for item, state in states.items():
                    if not ITEM_ID.fullmatch(item):
                        errors.append(f"{label}: invalid bootstrap item id: {item!r}")
                    if state not in STATES:
                        errors.append(f"{label}: invalid bootstrap state for {item}: {state!r}")
                    elif ITEM_ID.fullmatch(item):
                        current_states[item] = state

        elif kind == "transition":
            extra = sorted(set(record) - TRANSITION_FIELDS)
            if extra:
                errors.append(f"{label}: transition carries forbidden fields: {', '.join(extra)}")
            item = record.get("item_id")
            before = record.get("from")
            after = record.get("to")
            valid_item = isinstance(item, str) and bool(ITEM_ID.fullmatch(item))
            if not valid_item:
                errors.append(f"{label}: transition requires a valid item_id")
            if before not in STATES:
                errors.append(f"{label}: invalid from state: {before!r}")
            if after not in STATES:
                errors.append(f"{label}: invalid to state: {after!r}")

            legal = before in STATES and after in STATES and after in EDGES[before]
            if before in STATES and after in STATES and not legal:
                errors.append(f"{label}: illegal planning transition: {before} -> {after}")

            # The feed's own established state must agree with the declared
            # origin, so a stale or replayed transition cannot slip through.
            if valid_item and before in STATES:
                known = current_states.get(item)
                if known is None and before != "EXPLORE":
                    errors.append(f"{label}: unknown item {item} must originate from EXPLORE")
                elif known is not None and known != before:
                    errors.append(
                        f"{label}: stale from state for {item}: declared {before}, feed holds {known}"
                    )

            if after == "ACTIVE":
                if actionability != "engineering":
                    errors.append(f"{label}: ACTIVE must be engineering-intake eligible")
                increments = record.get("increments")
                if not isinstance(increments, list) or not increments:
                    errors.append(f"{label}: ACTIVE requires at least one increment binding")
                else:
                    if len(increments) > MAX_INCREMENTS:
                        errors.append(f"{label}: increments exceeds {MAX_INCREMENTS} entries")
                    if increments != sorted(increments, key=lambda i: i if isinstance(i, str) else ""):
                        errors.append(f"{label}: increments must be sorted")
                    if len(increments) != len({i for i in increments if isinstance(i, str)}):
                        errors.append(f"{label}: increments must be unique")
                    for inc in increments:
                        if not isinstance(inc, str) or not INCREMENT_ID.fullmatch(inc):
                            errors.append(f"{label}: invalid increment identity: {inc!r}")
                    refs = record.get("authoritative_refs")
                    if isinstance(refs, list):
                        bound = [
                            inc for inc in increments
                            if isinstance(inc, str) and any(
                                isinstance(r, str) and r.startswith(f"docs/increments/{inc}")
                                for r in refs
                            )
                        ]
                        if not bound:
                            errors.append(
                                f"{label}: ACTIVE must reference an increment record "
                                f"under docs/increments/ for one of its increments"
                            )
            else:
                if actionability != "awareness":
                    errors.append(f"{label}: non-ACTIVE transitions must be awareness-only")
                if "increments" in record:
                    errors.append(f"{label}: non-ACTIVE transitions must not carry increments")

            if valid_item and legal and current_states.get(item, before) == before:
                current_states[item] = after
        else:
            errors.append(f"{label}: kind must be one of {', '.join(KINDS)}")

        record_errors, record_gaps = witness_errors(record, label, mode)
        errors.extend(record_errors)
        gaps.extend(record_gaps)

    if bootstrap_count != 1:
        errors.append(f"feed must contain exactly one bootstrap record; observed {bootstrap_count}")
    return errors, gaps


def validate_text(raw: bytes, *, mode: str = "skip") -> list[str]:
    records, errors = parse_feed(raw)
    if not records:
        return errors or ["feed has no parseable records"]
    record_errors, _ = validate_records(records, mode=mode)
    return errors + record_errors


# ------------------------------------------------------------ schema agreement

def schema_agreement_errors() -> tuple[list[str], list[str]]:
    """The published schema and this validator must not drift apart."""
    if not SCHEMA_PATH.is_file():
        return [], [f"{SCHEMA_REL} is absent; schema/validator agreement not observed"]
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return [f"{SCHEMA_REL} is unreadable: {exc}"], []

    errors: list[str] = []
    props = schema.get("properties", {})
    if schema.get("$id") != SCHEMA_ID:
        errors.append(f"{SCHEMA_REL}: $id must be {SCHEMA_ID}")
    if schema.get("additionalProperties") is not False:
        errors.append(f"{SCHEMA_REL}: additionalProperties must be false")
    if set(props) != (BOOTSTRAP_FIELDS | TRANSITION_FIELDS):
        errors.append(
            f"{SCHEMA_REL}: properties disagree with the validator field set: "
            f"{sorted(set(props) ^ (BOOTSTRAP_FIELDS | TRANSITION_FIELDS))}"
        )
    for name, expected in (("kind", list(KINDS)), ("actionability", list(ACTIONABILITIES))):
        if props.get(name, {}).get("enum") != expected:
            errors.append(f"{SCHEMA_REL}: {name} enum must be {expected}")
    for name, pattern in (
        ("event_id", EVENT_ID.pattern),
        ("item_id", ITEM_ID.pattern),
        ("source_commit", FULL_OID.pattern),
    ):
        if props.get(name, {}).get("pattern") != pattern:
            errors.append(f"{SCHEMA_REL}: {name} pattern must be {pattern!r}")
    for name in ("from", "to"):
        if props.get(name, {}).get("enum") != list(STATES):
            errors.append(f"{SCHEMA_REL}: {name} enum must be the closed state set")
    return errors, []


# -------------------------------------------------------------- continuity

def continuity_errors(baseline: bytes | None, current: bytes) -> list[str]:
    """Prefix continuity against an accepted baseline.

    The consumer's cursor is a byte offset plus a prefix SHA-256, so any
    truncation, replacement, or in-place edit of already-published bytes must be
    observable here rather than silently rebased.
    """
    if baseline is None or baseline == b"":
        return []
    if current.startswith(baseline):
        return []
    if len(current) < len(baseline) and baseline.startswith(current):
        return [
            f"feed was truncated: accepted baseline is {len(baseline)} bytes, "
            f"current is {len(current)} bytes"
        ]
    limit = min(len(baseline), len(current))
    offset = next((i for i in range(limit) if baseline[i] != current[i]), limit)
    return [
        f"feed prefix was mutated at byte offset {offset}: already-published "
        f"bytes must never change"
    ]


def accepted_baseline_bytes() -> tuple[bytes | None, str]:
    """Feed bytes at the accepted surface this branch would fast-forward onto."""
    for ref in ("origin/main", "main"):
        head = git("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if head.returncode != 0:
            continue
        base = git("merge-base", "HEAD", ref)
        if base.returncode != 0:
            continue
        sha = base.stdout.strip()
        blob = git("rev-parse", "--verify", "--quiet", f"{sha}:{FEED_REL}")
        if blob.returncode != 0:
            return None, f"unpublished: no feed at accepted baseline {ref} ({sha[:12]})"
        content = subprocess.run(
            ["git", "-C", str(ROOT), "cat-file", "blob", blob.stdout.strip()],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if content.returncode != 0:
            return None, f"could-not-observe: baseline feed blob unreadable at {ref}"
        return content.stdout, f"verified against accepted baseline {ref} ({sha[:12]})"
    return None, "could-not-observe: no accepted baseline ref (origin/main or main) is local"


# --------------------------------------------------------------- controls

def _bootstrap_of(raw: bytes) -> str:
    return raw.decode("utf-8").splitlines()[0]


def compact(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _transition(**overrides: object) -> dict:
    ref = "docs/development/FUTURE_CANDIDATES.md"
    base: dict = {
        "schema": SCHEMA_ID,
        "sequence": 2,
        "event_id": "plan-20260818-0002",
        "kind": "transition",
        "item_id": "FUT-002",
        "from": "PRESERVE",
        "to": "CANDIDATE",
        "source_commit": "1" * 40,
        "actionability": "awareness",
        "authoritative_refs": [ref],
        "authoritative_blobs": {ref: "2" * 40},
    }
    base.update(overrides)
    return base


def _active(**overrides: object) -> dict:
    refs = ["docs/development/FUTURE_CANDIDATES.md", "docs/increments/FP-002_EXAMPLE.md"]
    base = _transition(
        item_id="FUT-001", **{"from": "SEQUENCED"}, to="ACTIVE",
        actionability="engineering",
        increments=["FP-002"],
        authoritative_refs=refs,
        authoritative_blobs={refs[0]: "2" * 40, refs[1]: "3" * 40},
    )
    base.update(overrides)
    return base


def run_controls(honest: bytes) -> tuple[list[str], list[tuple[str, str]]]:
    """Deterministic watched-red matrix.

    Every control is a named mutation of a feed that is first proven to pass.
    A control counts only when the mutation produces the *specific* expected
    error, so a red caused by unrelated breakage cannot be mistaken for proof.
    """
    failures: list[str] = []
    observed: list[tuple[str, str]] = []

    bootstrap = _bootstrap_of(honest)

    # --- non-vacuity partners: the accepting path must be proven able to pass.
    if validate_text(honest, mode="skip"):
        failures.append(
            "non-vacuity: the honest feed does not pass under the control code "
            f"path; every red below is vacuous: {validate_text(honest, mode='skip')}"
        )
        return failures, observed

    honest_chain = (
        bootstrap + "\n"
        + compact(_transition()) + "\n"
        + compact(_active(sequence=3, event_id="plan-20260818-0003")) + "\n"
    ).encode("utf-8")
    if validate_text(honest_chain, mode="skip"):
        failures.append(
            "non-vacuity: the honest multi-record chain (bootstrap + awareness "
            "transition + ACTIVE transition) does not pass: "
            f"{validate_text(honest_chain, mode='skip')}"
        )
        return failures, observed

    def red(name: str, mutant: bytes, needle: str) -> None:
        messages = validate_text(mutant, mode="skip")
        if not messages:
            failures.append(f"control {name}: mutated feed stayed green")
        elif not any(needle in message for message in messages):
            failures.append(f"control {name}: expected {needle!r}; observed {messages!r}")
        else:
            observed.append((name, needle))

    line2 = compact(_transition())
    chain = bootstrap + "\n" + line2 + "\n"

    # -- canonical one-JSON-object-per-line representation
    red("malformed-json", (bootstrap + "\n{\n").encode(), "malformed JSON")
    red("duplicate-object-key", (bootstrap + "\n" + line2[:-1] + ',"kind":"transition"}\n').encode(), "duplicate object key")
    red("non-canonical-key-order",
        (json.dumps(json.loads(bootstrap), separators=(",", ":")) + "\n").encode()
        if json.dumps(json.loads(bootstrap), separators=(",", ":")) != bootstrap
        else (bootstrap.replace('{"actionability"', '{ "actionability"', 1) + "\n").encode(),
        "canonical compact key-sorted JSON")
    red("non-compact-separators",
        (json.dumps(json.loads(bootstrap), sort_keys=True) + "\n").encode(),
        "canonical compact key-sorted JSON")
    red("non-object-line", (bootstrap + "\n[]\n").encode(), "must be a JSON object")
    red("blank-record", (bootstrap + "\n\n").encode(), "blank records are forbidden")
    red("missing-trailing-lf", bootstrap.encode(), "complete LF-terminated record")
    red("cr-framing", (bootstrap + "\r\n").encode(), "CR bytes")
    red("utf8-bom", b"\xef\xbb\xbf" + bootstrap.encode() + b"\n", "UTF-8 BOM")

    # -- unique, ordered event ids and sequences
    red("duplicate-event-id",
        (chain.replace(line2, compact(_transition(event_id="plan-20260818-0001")))).encode(),
        "duplicate event_id")
    red("non-increasing-event-id",
        (bootstrap + "\n" + compact(_transition(event_id="plan-20260817-9999")) + "\n").encode(),
        "not strictly increasing")
    red("sequence-gap",
        (bootstrap + "\n" + compact(_transition(sequence=3)) + "\n").encode(),
        "sequence must be exactly 2")
    red("sequence-not-integer",
        (bootstrap + "\n" + compact(_transition(sequence=2.0)) + "\n").encode(),
        "sequence must be exactly 2")

    # -- bootstrap uniqueness, position, and mechanical non-actionability
    red("second-bootstrap",
        (bootstrap + "\n" + compact({**json.loads(bootstrap), "sequence": 2,
                                     "event_id": "plan-20260818-0002"}) + "\n").encode(),
        "only one bootstrap record is allowed")
    first_is_transition = _transition(
        sequence=1, event_id="plan-20260818-0000", item_id="FUT-009",
        to="PRESERVE", **{"from": "EXPLORE"},
    )
    red("bootstrap-not-first",
        (compact(first_is_transition) + "\n"
         + compact({**json.loads(bootstrap), "sequence": 2,
                    "event_id": "plan-20260818-0002"}) + "\n").encode(),
        "bootstrap must be the first record")
    red("bootstrap-actionable",
        (compact({**json.loads(bootstrap), "actionability": "engineering"}) + "\n").encode(),
        "bootstrap must be awareness-only")
    red("bootstrap-carries-increments",
        (compact({**json.loads(bootstrap), "increments": ["FP-001"]}) + "\n").encode(),
        "bootstrap must not carry increments")
    red("bootstrap-carries-transition",
        (compact({**json.loads(bootstrap), "to": "ACTIVE"}) + "\n").encode(),
        "bootstrap must not carry to")
    red("bootstrap-missing-states",
        (compact({k: v for k, v in json.loads(bootstrap).items() if k != "states"}) + "\n").encode(),
        "bootstrap requires a nonempty states object")

    # -- closed-set states and event kinds
    red("unknown-kind",
        (bootstrap + "\n" + compact(_transition(kind="promotion")) + "\n").encode(),
        "kind must be one of")
    red("unknown-actionability",
        (bootstrap + "\n" + compact(_transition(actionability="baseline")) + "\n").encode(),
        "actionability must be one of")
    red("unknown-bootstrap-state",
        (compact({**json.loads(bootstrap),
                  "states": {**json.loads(bootstrap)["states"], "FUT-001": "MAYBE"}}) + "\n").encode(),
        "invalid bootstrap state")
    red("unknown-to-state",
        (bootstrap + "\n" + compact(_transition(to="SHIPPED")) + "\n").encode(),
        "invalid to state")

    # -- legal lifecycle transitions only
    red("illegal-edge",
        (bootstrap + "\n" + compact(_transition(item_id="FUT-002", to="PROVEN")) + "\n").encode(),
        "illegal planning transition")
    red("terminal-state-exit",
        (bootstrap + "\n" + compact(_transition(item_id="FUT-002", to="REJECTED")) + "\n"
         + compact(_transition(sequence=3, event_id="plan-20260818-0003", item_id="FUT-002",
                               **{"from": "REJECTED"}, to="CANDIDATE")) + "\n").encode(),
        "illegal planning transition")
    red("stale-from-state",
        (bootstrap + "\n" + compact(_transition(item_id="FUT-002", **{"from": "DECIDED"},
                                                to="SEQUENCED")) + "\n").encode(),
        "stale from state")
    red("unknown-item-not-from-explore",
        (bootstrap + "\n" + compact(_transition(item_id="FUT-404")) + "\n").encode(),
        "must originate from EXPLORE")

    # -- full exact Git source identities
    red("short-source-commit",
        (bootstrap + "\n" + compact(_transition(source_commit="95355df")) + "\n").encode(),
        "full lowercase 40-hex commit id")
    red("uppercase-source-commit",
        (bootstrap + "\n" + compact(_transition(source_commit="A" * 40)) + "\n").encode(),
        "full lowercase 40-hex commit id")
    red("symbolic-source-commit",
        (bootstrap + "\n" + compact(_transition(source_commit="main")) + "\n").encode(),
        "full lowercase 40-hex commit id")
    red("missing-blob-binding",
        (bootstrap + "\n" + compact(_transition(authoritative_blobs={})) + "\n").encode(),
        "authoritative_blobs must be a nonempty object")
    red("short-blob-id",
        (bootstrap + "\n" + compact(_transition(
            authoritative_blobs={"docs/development/FUTURE_CANDIDATES.md": "1febbe1"})) + "\n").encode(),
        "full lowercase 40-hex object id")
    red("blob-ref-set-mismatch",
        (bootstrap + "\n" + compact(_transition(
            authoritative_blobs={"docs/development/ROADMAP.md": "2" * 40})) + "\n").encode(),
        "must bind exactly authoritative_refs")

    # -- bounded, normalized authoritative refs
    for name, ref in (
        ("ref-traversal", "docs/../etc/passwd"),
        ("ref-absolute", "/docs/development/ROADMAP.md"),
        ("ref-outside-docs", "adws/adw_modules/tracer.py"),
        ("ref-double-slash", "docs//development/ROADMAP.md"),
        ("ref-dot-segment", "docs/./development/ROADMAP.md"),
        ("ref-trailing-slash", "docs/development/"),
        ("ref-backslash", "docs\\development\\ROADMAP.md"),
        ("ref-over-length", "docs/" + "a" * MAX_REF_LENGTH),
    ):
        red(name,
            (bootstrap + "\n" + compact(_transition(
                authoritative_refs=[ref], authoritative_blobs={ref: "2" * 40})) + "\n").encode(),
            "unsafe authoritative ref")
    red("refs-unsorted",
        (bootstrap + "\n" + compact(_transition(
            authoritative_refs=["docs/development/ROADMAP.md", "docs/development/FUTURE_CANDIDATES.md"],
            authoritative_blobs={"docs/development/FUTURE_CANDIDATES.md": "2" * 40,
                                 "docs/development/ROADMAP.md": "3" * 40})) + "\n").encode(),
        "authoritative_refs must be sorted")
    red("refs-empty",
        (bootstrap + "\n" + compact(_transition(authoritative_refs=[])) + "\n").encode(),
        "authoritative_refs must be a nonempty list")

    # -- ACTIVE requires a concrete increment binding
    red("active-without-increments",
        (bootstrap + "\n" + compact({k: v for k, v in _active(sequence=2).items()
                                     if k != "increments"}) + "\n").encode(),
        "ACTIVE requires at least one increment binding")
    red("active-awareness-actionability",
        (bootstrap + "\n" + compact(_active(sequence=2, actionability="awareness")) + "\n").encode(),
        "ACTIVE must be engineering-intake eligible")
    red("active-bad-increment-identity",
        (bootstrap + "\n" + compact(_active(sequence=2, increments=["fp-001"])) + "\n").encode(),
        "invalid increment identity")
    red("active-increment-not-referenced",
        (bootstrap + "\n" + compact(_active(
            sequence=2,
            authoritative_refs=["docs/development/FUTURE_CANDIDATES.md"],
            authoritative_blobs={"docs/development/FUTURE_CANDIDATES.md": "2" * 40})) + "\n").encode(),
        "must reference an increment record")
    red("non-active-carries-increments",
        (bootstrap + "\n" + compact(_transition(increments=["FP-001"])) + "\n").encode(),
        "non-ACTIVE transitions must not carry increments")
    red("non-active-engineering",
        (bootstrap + "\n" + compact(_transition(actionability="engineering")) + "\n").encode(),
        "non-ACTIVE transitions must be awareness-only")

    return failures, observed


def run_continuity_controls(honest: bytes) -> tuple[list[str], list[tuple[str, str]]]:
    """Prove prefix mutation, truncation, and replacement are observable."""
    failures: list[str] = []
    observed: list[tuple[str, str]] = []

    published = honest
    appended = honest + compact(_transition()).encode("utf-8") + b"\n"

    # non-vacuity partner: an honest append against the same baseline passes.
    if continuity_errors(published, appended):
        failures.append("non-vacuity: an honest append was rejected by the continuity check")
        return failures, observed
    if continuity_errors(published, published):
        failures.append("non-vacuity: an unchanged feed was rejected by the continuity check")
        return failures, observed

    def red(name: str, current: bytes, needle: str) -> None:
        messages = continuity_errors(published, current)
        if not messages:
            failures.append(f"continuity control {name}: mutation stayed green")
        elif not any(needle in message for message in messages):
            failures.append(f"continuity control {name}: expected {needle!r}; observed {messages!r}")
        else:
            observed.append((name, needle))

    def flip(data: bytes, offset: int) -> bytes:
        """Mutate exactly one published byte, independent of feed content."""
        mutated = bytearray(data)
        mutated[offset] ^= 0xFF
        return bytes(mutated)

    midpoint = len(published) // 2
    red("truncation", published[:midpoint], "feed was truncated")
    red("record-removal", b"", "feed was truncated")
    red("prefix-byte-mutation-first", flip(published, 0), "prefix was mutated")
    red("prefix-byte-mutation-middle", flip(published, midpoint), "prefix was mutated")
    red("prefix-byte-mutation-last", flip(published, len(published) - 1), "prefix was mutated")
    red("historical-replacement", b"x" * len(published), "prefix was mutated")
    red("prefix-mutation-with-honest-append",
        flip(published, midpoint) + compact(_transition()).encode("utf-8") + b"\n",
        "prefix was mutated")
    return failures, observed


# ------------------------------------------------------------------- driver

def main() -> int:
    argv = sys.argv[1:]
    mode = "require" if "--require-git-witness" in argv else "observe"

    if FEED.is_symlink():
        print("FP-001 planning event feed: COULD-NOT-OBSERVE")
        print(f"- {FEED_REL} is a symlink; refusing to follow it")
        return 2
    if not FEED.is_file():
        print("FP-001 planning event feed: COULD-NOT-OBSERVE")
        print(f"- {FEED_REL} is absent or not a regular file")
        return 2
    try:
        raw = FEED.read_bytes()
    except OSError as exc:
        print("FP-001 planning event feed: COULD-NOT-OBSERVE")
        print(f"- {FEED_REL} could not be read: {exc}")
        return 2

    records, errors = parse_feed(raw)
    gaps: list[str] = []
    if records:
        record_errors, record_gaps = validate_records(records, mode=mode)
        errors += record_errors
        gaps += record_gaps
    elif not errors:
        errors.append("feed has no parseable records")

    schema_errors, schema_gaps = schema_agreement_errors()
    errors += schema_errors
    gaps += schema_gaps

    baseline, continuity_note = accepted_baseline_bytes()
    errors += continuity_errors(baseline, raw)

    control_failures: list[str] = []
    controls: list[tuple[str, str]] = []
    continuity_controls: list[tuple[str, str]] = []
    if not errors:
        control_failures, controls = run_controls(raw)
        continuity_failures, continuity_controls = run_continuity_controls(raw)
        control_failures += continuity_failures
        errors += control_failures

    if errors:
        print("FP-001 planning event feed: FAIL")
        for err in errors:
            print(f"- {err}")
        for gap in gaps:
            print(f"- could-not-observe: {gap}")
        return 1

    total = len(controls) + len(continuity_controls)
    print("FP-001 planning event feed: PASS")
    print(f"- records: {len(records)} (1 bootstrap, {len(records) - 1} transitions)")
    print("- bootstrap: unique, first, awareness-only, carries no intake binding")
    print("- representation: one canonical compact key-sorted JSON object per LF-terminated line")
    print("- identity: event ids unique and strictly increasing; sequence dense from 1")
    print("- vocabulary: kinds, actionability, and planning states are closed-set")
    print("- transitions: legal under PLANNING_LIFECYCLE.md and agree with feed-established state")
    print("- source witness: full 40-hex source_commit plus one full blob id per authoritative ref")
    print("- authoritative refs: bounded, normalized, repository-relative, under docs/")
    print(f"- continuity: {continuity_note}")
    print(f"- watched-red controls executed: {total} ({len(controls)} record, {len(continuity_controls)} continuity)")
    print(f"- watched reds observed: {total}; each asserted its own expected diagnostic")
    print("- non-vacuity partners: honest feed, honest bootstrap+awareness+ACTIVE chain, "
          "honest append, unchanged feed")
    for name, needle in controls + continuity_controls:
        print(f"  - red {name}: {needle}")
    if gaps:
        print(f"- could-not-observe axes: {len(gaps)}")
        for gap in gaps:
            print(f"  - {gap}")
        print("  (shallow checkout; re-run with --require-git-witness at full depth)")
    else:
        print("- could-not-observe axes: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
