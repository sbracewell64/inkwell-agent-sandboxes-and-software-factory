"""Validation gates: verify the envelope's CLAIMS, never guesses.

A gate is `gate(envelope, run) -> GateReport` — one check per item it looked at.
The typed outcome is derived from failed checks and each gate's explicit
nonempty requirement. Failures and unavailable evidence are sent back to the
SAME agent session as corrections. Every check is recorded either way, so PASS
says WHAT it verified instead of only presenting an empty violations list.

Gates check what is mechanically checkable; plan quality is a reviewer's job.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from . import mutation_fact
from .data_types import (
    EnvelopeBase,
    GateCheck,
    GateCNOReason,
    GateCNOSource,
    GateReport,
    ObservationScope,
)

TAIL_CHARS = 1000        # command output kept as evidence on a failure


def _size(path: Path) -> str:
    n = path.stat().st_size
    return f"{n}B" if n < 1024 else f"{n / 1024:.1f}KB"


def artifacts_exist(envelope: EnvelopeBase, run) -> GateReport:
    report = GateReport(nonempty_required=True)
    for a in envelope.artifacts:
        p = Path(a)
        report.check(a, p.exists(),
                     f"exists, {_size(p)}" if p.exists() else "declared artifact does not exist")
    return report


def files_non_empty(envelope: EnvelopeBase, run) -> GateReport:
    report = GateReport(nonempty_required=True)
    for a in envelope.artifacts:
        p = Path(a)
        if not (p.exists() and p.is_file()):
            continue                       # existence is artifacts_exist's job
        empty = p.stat().st_size == 0
        report.check(a, not empty, "declared artifact is empty" if empty else _size(p))
    return report


def json_parses(envelope: EnvelopeBase, run) -> GateReport:
    report = GateReport(nonempty_required=True)
    for a in envelope.artifacts:
        p = Path(a)
        if p.suffix != ".json" or not p.exists():
            continue
        try:
            parsed = json.loads(p.read_text())
            report.check(a, True, f"parses, {type(parsed).__name__}")
        except json.JSONDecodeError as e:
            report.check(a, False, f"declared JSON artifact does not parse: {e}")
    return report


def _short(oid: str | None) -> str:
    return oid[:7] if oid else "absent"


def _scope(reconciliation) -> ObservationScope:
    """Say what this verdict covers before it says what it found."""
    return ObservationScope(
        observed=list(reconciliation.observed_classes),
        out_of_scope=list(reconciliation.out_of_scope_classes),
        unobservable=[f"{item}: {why}" for item, why in reconciliation.unobservable])


def diff_matches_claims(envelope: EnvelopeBase, run) -> GateReport:
    """Reconcile the claimed change set against the mutation fact, BOTH ways.

    The old gate looped the declared list and proved only that each named path
    EXISTS, so an empty `changed_files`, an omitted path, and a claim on a file
    nobody touched all went green. Existence is not mutation. This compares
    normalized path plus CONTENT IDENTITY in both directions, because each one
    catches a different lie: a claimed path that did not move is a fabricated
    claim, and a path that moved without being claimed is a concealed one.

    The fact is read, never taken — `mutation_fact.observation_of` returns the
    one observation the permission check also consumes, so the two cannot
    disagree about what moved.

    The verdict is bounded, and says so. Agreement here means agreement WITHIN
    the Git and permission fact set; ignored files, out-of-repository writes,
    network effects and process effects are outside it and the report names
    them. A candidate that could not be read makes the result COULD_NOT_OBSERVE
    rather than a negative fact, because a negative claim is only as good as its
    universe.
    """
    observation = mutation_fact.observation_of(run)
    if observation is None:
        return GateReport(
            nonempty_required=True,
            cno_reason=GateCNOReason.INCOMPLETE_OBSERVED_UNIVERSE,
            cno_source=GateCNOSource.MUTATION_FACT,
            cno_detail="no mutation fact was recorded for this phase, so the "
                       "claimed change set could not be reconciled against anything",
            scope=ObservationScope(observed=[],
                                   out_of_scope=list(mutation_fact.OUT_OF_SCOPE_CLASSES),
                                   unobservable=["<mutation fact>: not recorded"]))

    result = mutation_fact.reconcile(observation, getattr(envelope, "changed_files", []))
    checks = [
        GateCheck(item=m.path, ok=True,
                  note=f"claimed and observed {m.kind}, content "
                       f"{_short(m.before_oid)} -> {_short(m.after_oid)}"
                       + (f", rename peer {m.rename_peer}" if m.rename_peer else ""))
        for m in result.agreed
    ]
    checks += [
        GateCheck(item=m.path, ok=False,
                  note=f"observed {m.kind} ({_short(m.before_oid)} -> "
                       f"{_short(m.after_oid)}) but the envelope did not claim it"
                       + (f"; it is the rename peer of the claimed {m.rename_peer}"
                          if m.rename_peer else ""))
        for m in result.unclaimed
    ]
    checks += [
        GateCheck(item=match.claim, ok=False,
                  note=match.problem or "claimed changed, but the mutation fact "
                                        "records no change to it")
        for match in result.unmatched
    ]
    return GateReport(
        nonempty_required=True, checks=checks, scope=_scope(result),
        # Zero discrepancies over a universe with a hole in it is not a negative
        # fact. FAIL still wins over this — an observed defect is never masked.
        cno_reason=None if result.complete else GateCNOReason.INCOMPLETE_OBSERVED_UNIVERSE,
        cno_source=None if result.complete else GateCNOSource.MUTATION_FACT,
        cno_detail="" if result.complete else
        "the mutation fact could not read " + "; ".join(
            f"{item} ({why})" for item, why in result.unobservable))


def verdict_consistent(envelope: EnvelopeBase, run) -> GateReport:
    """A review's verdict must agree with the findings it just wrote down.

    Nothing here judges the code — that is the reviewer's job. This checks the
    envelope against itself: an approval that ships blocking items, or a
    rejection that names no problem, is a claim the harness can refute without
    reading a line of the diff.
    """
    report = GateReport(nonempty_required=True)
    approved = bool(getattr(envelope, "approved", False))
    blocking = list(getattr(envelope, "blocking", []))
    unmet = [f.requirement for f in getattr(envelope, "findings", []) if not f.met]

    report.check("approved vs blocking", not (approved and blocking),
                 "no blocking items" if not blocking
                 else f"{len(blocking)} blocking item(s) while approved=true"
                 if approved else f"{len(blocking)} blocking item(s), not approved")
    report.check("approved vs findings", not (approved and unmet),
                 "every requirement met" if not unmet
                 else f"{len(unmet)} unmet requirement(s) while approved=true"
                 if approved else f"{len(unmet)} unmet requirement(s), not approved")
    report.check("rejection names a problem", approved or bool(blocking or unmet),
                 "verdict is supported" if approved or blocking or unmet
                 else "approved=false but no blocking item or unmet requirement was given")
    return report


def tests_pass(command: str):
    """Gate factory: the given shell command must exit 0."""
    def gate(envelope: EnvelopeBase, run) -> GateReport:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        ok = result.returncode == 0
        note = f"exit {result.returncode}"
        if not ok:
            note += "\n" + (result.stdout + result.stderr)[-TAIL_CHARS:]
        return GateReport(nonempty_required=True).check(command, ok, note)
    gate.__name__ = f"tests_pass({command})"
    return gate
