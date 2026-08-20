"""One code-computed mutation fact, reconciled BOTH ways against the claims.

A workflow's envelope claims what it changed. Until this module nothing compared
that claim to the repository: `diff_matches_claims` looped the declared list and
proved only that each named path EXISTS, so `changed_files=[]`, an omitted path,
and a claimed-but-untouched path all earned a green gate. Existence is not
mutation, and one direction is not a comparison.

So the fact is computed here, in code, once per observation:

  * per-path CONTENT IDENTITY — git blob oids, before and after, never a proxy.
    Line counts were the old fingerprint and they are blind to an edit that
    replaces a line with another of the same shape, including on a file that
    was already dirty when the phase opened, which is exactly when an agent's
    damage hides;
  * a derived mutation kind per path: added, modified, deleted. A rename is a
    deletion plus an addition whose content identity is EQUAL, so it resolves
    from the bytes rather than from git's similarity heuristic, and the answer
    does not move with a git version or a `diff.renames` setting.

`reconcile()` then compares that fact with the envelope in BOTH directions,
because each direction catches a different lie: a claimed path that did not move
is a fabricated claim, and a path that moved without being claimed is a
concealed one.

One fact, two consumers. `permissions` and the claim gate read the SAME
`MutationObservation` rather than each taking its own snapshot, because two
snapshots taken at different moments are two sources of truth that diverge the
instant either one moves.

## The observation boundary, which every verdict must state

The fact set is bounded, and the bound is load-bearing. It observes tracked
content identity against HEAD and untracked, non-ignored working-tree files. It
does NOT observe gitignored files, writes outside the repository root, network
effects, or process effects.

Under the standing law that negative claims require complete observation, an
agreeing reconciliation means `no discrepancy WITHIN this fact set` and never an
unqualified clean. Every result therefore carries `OBSERVED_CLASSES` alongside
`OUT_OF_SCOPE_CLASSES`, so a green cannot be read as "nothing else happened",
and any candidate this module could not read leaves the result INCOMPLETE rather
than negative.

Deliberately dependency-free: the permission check, the claim gate, and the
offline CI control all consume this one module, and that control has to run on a
runner that installs nothing.
"""

from __future__ import annotations

import os
import posixpath
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

# git's empty tree. A repository with no commit yet still has a mutation fact:
# everything in it is an addition measured against nothing.
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

# `hash-object` takes paths as argv, so a large change set is chunked to stay
# under the platform's command-line ceiling.
HASH_CHUNK = 128

KIND_ADDED = "added"
KIND_MODIFIED = "modified"
KIND_DELETED = "deleted"

# What a verdict from this module is allowed to speak about...
OBSERVED_CLASSES = (
    "tracked path content identity against HEAD (added, modified, deleted)",
    "untracked, non-ignored working-tree files",
    "renames derived from exact content identity across a deletion/addition pair",
)

# ...and what it is not. Naming these is the deliverable, not closing them: a
# reader must be able to see that agreement here is bounded agreement.
OUT_OF_SCOPE_CLASSES = (
    "gitignored files",
    "writes outside the repository root",
    "network effects",
    "process effects",
)


@dataclass(frozen=True)
class PathState:
    """One path's content at one instant, by identity rather than by size."""

    path: str
    head_oid: str | None        # blob identity in the base commit; None = absent there
    work_oid: str | None        # blob identity on disk; None = not on disk
    tracked: bool


@dataclass(frozen=True)
class TreeFact:
    """Every path the working tree differs on at one instant, normalized.

    `unobservable` is a first-class part of the fact, not an error channel. A
    candidate that could not be read is the difference between a truthful
    negative and a could-not-observe, so it travels with the states.
    """

    states: dict[str, PathState]
    unobservable: dict[str, str]
    repo_root: str | None       # None when there was no repository to observe
    base: str | None            # the commit (or empty tree) the states measure from


@dataclass(frozen=True)
class PathMutation:
    """What actually happened to one path between two facts."""

    path: str
    kind: str
    before_oid: str | None
    after_oid: str | None
    rename_peer: str | None = None


@dataclass(frozen=True)
class MutationObservation:
    """The ONE fact the claim gate and the permission check both consume."""

    before: TreeFact
    after: TreeFact
    mutations: tuple[PathMutation, ...]

    @classmethod
    def between(cls, before: TreeFact, after: TreeFact) -> "MutationObservation":
        return cls(before=before, after=after, mutations=mutations(before, after))

    @property
    def unobservable(self) -> dict[str, str]:
        """Every candidate either instant failed to read, merged."""
        merged = dict(self.before.unobservable)
        merged.update(self.after.unobservable)
        return merged

    @property
    def repo_root(self) -> str | None:
        return self.after.repo_root or self.before.repo_root


@dataclass(frozen=True)
class ClaimMatch:
    """One claimed path: what the envelope wrote, and where it landed."""

    claim: str
    path: str | None            # normalized repo-relative form, None when unplaceable
    problem: str = ""           # why it could not be placed, when it could not


@dataclass(frozen=True)
class Reconciliation:
    """The bidirectional comparison, with its universe attached.

    `agreed` alone is never the verdict. `unobservable` is what keeps a
    zero-discrepancy result from being read as complete, and the two class
    tuples are what keep it from being read as unqualified.
    """

    agreed: tuple[PathMutation, ...]
    unclaimed: tuple[PathMutation, ...]     # moved, never claimed
    unmatched: tuple[ClaimMatch, ...]       # claimed, never moved
    unobservable: tuple[tuple[str, str], ...]
    observed_classes: tuple[str, ...] = OBSERVED_CLASSES
    out_of_scope_classes: tuple[str, ...] = OUT_OF_SCOPE_CLASSES

    @property
    def discrepancies(self) -> int:
        return len(self.unclaimed) + len(self.unmatched)

    @property
    def complete(self) -> bool:
        """True only when every candidate in the bounded universe was read."""
        return not self.unobservable


# ── git plumbing (bytes in, os.fsdecode out: a path is not necessarily UTF-8) ─

def _git(root: Path, *args: str) -> tuple[int, bytes]:
    result = subprocess.run(["git", *args], cwd=str(root), capture_output=True)
    return result.returncode, result.stdout


def _z(data: bytes) -> list[str]:
    return [os.fsdecode(item) for item in data.split(b"\0") if item]


def _head_oids(root: Path, base: str,
               paths: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Blob identity of each path in the base commit, in one batch."""
    oids: dict[str, str] = {}
    unreadable: dict[str, str] = {}
    # `cat-file --batch-check` is line-delimited, so a path containing a newline
    # cannot be asked about. That is a could-not-observe, not an absence.
    askable = [p for p in paths if "\n" not in p]
    for path in paths:
        if "\n" in path:
            unreadable[path] = "path contains a newline and cannot be batch-queried"
    if not askable:
        return oids, unreadable

    request = "".join(f"{base}:{path}\n" for path in askable).encode()
    result = subprocess.run(["git", "cat-file", "--batch-check"], cwd=str(root),
                            input=request, capture_output=True)
    lines = result.stdout.decode("utf-8", "replace").splitlines()
    if result.returncode != 0 or len(lines) != len(askable):
        return oids, {p: "the base commit's blob identity could not be read"
                      for p in askable}
    # One answer per request line, in order — the echoed name is not parsed,
    # because a path may contain the very spaces that parsing would split on.
    for path, line in zip(askable, lines):
        fields = line.split()
        if len(fields) == 3 and fields[1] == "blob":
            oids[path] = fields[0]
    return oids, unreadable


def _work_oids(root: Path, paths: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Blob identity of each path as it sits on disk, chunked over argv.

    `hash-object` is used rather than a hand-rolled digest so the repository's
    own attributes apply: the identity compared here is the identity git would
    store, on every platform this repo's LF contract runs on.
    """
    oids: dict[str, str] = {}
    unreadable: dict[str, str] = {}
    for start in range(0, len(paths), HASH_CHUNK):
        chunk = paths[start:start + HASH_CHUNK]
        code, out = _git(root, "hash-object", "--", *chunk)
        lines = out.decode("utf-8", "replace").split()
        if code == 0 and len(lines) == len(chunk):
            oids.update(zip(chunk, lines))
            continue
        # One bad path fails the whole chunk, so the chunk is re-asked one path
        # at a time and only the path that actually cannot be read is named.
        for path in chunk:
            code, out = _git(root, "hash-object", "--", path)
            single = out.decode("utf-8", "replace").split()
            if code == 0 and len(single) == 1:
                oids[path] = single[0]
            else:
                unreadable[path] = "working-tree content could not be hashed"
    return oids, unreadable


# ── observation ──────────────────────────────────────────────────────────────

def observe(repo_root) -> TreeFact:
    """Fingerprint, by content identity, every path the tree currently differs on.

    Tracked paths are measured against HEAD (or the empty tree in a repository
    with no commit), so a staged change and an unstaged one are the same fact.
    Untracked, non-ignored files are named as well, which is why the session
    runtime under `data_dir` — gitignored, and where handoff files legitimately
    land — never appears and needs no special case.
    """
    root = Path(repo_root)
    code, _ = _git(root, "rev-parse", "--git-dir")
    if code != 0:
        return TreeFact(states={}, repo_root=None, base=None, unobservable={
            "<repository>": f"{root} is not a git repository, so no mutation "
                            f"fact exists to compare claims against"})

    code, out = _git(root, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    base = out.decode().strip() if code == 0 else EMPTY_TREE

    code, out = _git(root, "diff", "--name-only", "--no-renames", "-z", base)
    if code != 0:
        return TreeFact(states={}, repo_root=str(root), base=base, unobservable={
            "<diff>": f"the diff against {base[:7]} could not be read"})
    tracked_changed = _z(out)

    code, out = _git(root, "ls-files", "--others", "--exclude-standard", "-z")
    if code != 0:
        return TreeFact(states={}, repo_root=str(root), base=base, unobservable={
            "<untracked>": "the untracked, non-ignored file list could not be read"})
    untracked = set(_z(out))

    candidates = sorted(set(tracked_changed) | untracked)
    head_oids, unreadable = _head_oids(root, base,
                                       [p for p in candidates if p not in untracked])
    on_disk = [p for p in candidates if os.path.lexists(os.path.join(str(root), p))]
    work_oids, work_unreadable = _work_oids(root, on_disk)
    unreadable.update(work_unreadable)

    states = {p: PathState(path=p, head_oid=head_oids.get(p), work_oid=work_oids.get(p),
                           tracked=p not in untracked)
              for p in candidates if p not in unreadable}
    return TreeFact(states=states, unobservable=unreadable,
                    repo_root=str(root), base=base)


def mutations(before: TreeFact, after: TreeFact) -> tuple[PathMutation, ...]:
    """Every path whose content identity moved between the two facts."""
    found: list[PathMutation] = []
    for path in sorted(set(before.states) | set(after.states)):
        was, now = before.states.get(path), after.states.get(path)
        # A path absent from one fact matched the base commit at that instant,
        # so its identity there is the base blob the other instant recorded.
        # That is what makes a REVERSION a mutation: dirty content became the
        # committed content, and undoing someone's work is doing something.
        before_oid = was.work_oid if was is not None else (now.head_oid if now else None)
        after_oid = now.work_oid if now is not None else (was.head_oid if was else None)
        if before_oid == after_oid:
            continue
        kind = (KIND_ADDED if before_oid is None
                else KIND_DELETED if after_oid is None
                else KIND_MODIFIED)
        found.append(PathMutation(path=path, kind=kind,
                                  before_oid=before_oid, after_oid=after_oid))
    return _link_renames(found)


def _link_renames(found: list[PathMutation]) -> tuple[PathMutation, ...]:
    """A rename is a deletion and an addition carrying the SAME bytes.

    Derived from content identity, never from a similarity score, so the answer
    is identical on every run and every git version. Both paths remain mutations
    in their own right — a rename moved two of them, and an envelope that claims
    only the destination has still concealed the source — and each is annotated
    with its peer so the report can say which pairing was found. Pairing walks
    the path-sorted list, so a content oid with several candidates resolves the
    same way every time.
    """
    available: dict[str, list[str]] = {}
    for mutation in found:
        if mutation.kind == KIND_DELETED and mutation.before_oid:
            available.setdefault(mutation.before_oid, []).append(mutation.path)

    peers: dict[str, str] = {}
    for mutation in found:
        if mutation.kind != KIND_ADDED or not mutation.after_oid:
            continue
        candidates = available.get(mutation.after_oid)
        if candidates:
            partner = candidates.pop(0)
            peers[mutation.path] = partner
            peers[partner] = mutation.path
    return tuple(replace(m, rename_peer=peers.get(m.path)) for m in found)


def observation_of(run) -> MutationObservation | None:
    """The fact recorded for the phase now running, or None when none was.

    Returning None rather than computing a fresh one is deliberate: a gate that
    quietly took its own snapshot would be the second source of truth this
    module exists to remove.
    """
    return getattr(run, "mutation", None) if run is not None else None


# ── reconciliation (both directions, because each catches a different lie) ───

def normalize_claim(claim: str, repo_root: str | None) -> tuple[str | None, str]:
    """Place a claimed path in the observed universe, or say why it does not fit.

    Returns `(repo-relative posix path, "")` or `(None, problem)`. Claims arrive
    as an agent wrote them — absolute, `./`-prefixed, or with the separator of
    whichever platform it ran on — and comparing those strings raw would let a
    formatting difference read as a fabricated claim.
    """
    text = (claim or "").strip().replace("\\", "/")
    if not text:
        return None, "empty claimed path"
    if repo_root is None:
        return None, "no repository was observed to place this claim in"

    normalized = posixpath.normpath(text)
    root = posixpath.normpath(str(repo_root).replace("\\", "/")).rstrip("/")
    if posixpath.isabs(normalized) or (len(normalized) > 1 and normalized[1] == ":"):
        if normalized == root:
            return None, "names the repository root, not a file"
        if not normalized.startswith(root + "/"):
            return None, "outside the observed repository root"
        normalized = normalized[len(root) + 1:]
    if normalized == "." or normalized == ".." or normalized.startswith("../"):
        return None, "outside the observed repository root"
    return normalized, ""


def reconcile(observation: MutationObservation, claims) -> Reconciliation:
    """Compare the envelope's claimed change set with the fact, in both directions.

    A claimed path that did not move and a moved path that was not claimed are
    both discrepancies; neither is derivable from the other, which is why the
    comparison is a set equality and not a lookup.
    """
    root = observation.repo_root
    placed: list[ClaimMatch] = []
    unplaceable: list[ClaimMatch] = []
    seen: set[str] = set()
    for claim in claims or []:
        path, problem = normalize_claim(str(claim), root)
        if path is None:
            unplaceable.append(ClaimMatch(claim=str(claim), path=None, problem=problem))
            continue
        if path in seen:                    # a repeated claim is one claim
            continue
        seen.add(path)
        placed.append(ClaimMatch(claim=str(claim), path=path))

    actual = {mutation.path: mutation for mutation in observation.mutations}
    agreed = tuple(actual[match.path] for match in placed if match.path in actual)
    unmatched = tuple(sorted(
        unplaceable + [m for m in placed if m.path not in actual],
        key=lambda match: (match.path or "", match.claim)))
    unclaimed = tuple(m for m in observation.mutations if m.path not in seen)
    return Reconciliation(
        agreed=agreed, unclaimed=unclaimed, unmatched=unmatched,
        unobservable=tuple(sorted(observation.unobservable.items())))
