"""What an agent may CHANGE, enforced in code after the fact.

`tools:` is a capability list, not a sandbox, and two holes make it
unenforceable on its own:

  * `bash` runs anything. A builder handed bash to run a test suite can also
    run `git checkout adws/` — which is not hypothetical: one did, discarding
    uncommitted changes to the very quality check it was about to be judged by.
  * `write` reaches any path, not just the one report file an agent was given
    it for. A reviewer configured with "no edit, so it cannot quietly fix"
    could still rewrite the code it was reviewing.

So permission is verified the way every other claim in this system is —
after the fact, against the repo itself. `snapshot()` fingerprints the working
tree's change-set before an agent runs; `enforce()` compares it afterwards and
fails the phase if the agent touched anything outside its allowlist.

Comparing change-sets, rather than watching for writes, is what catches the
`git checkout` case: a path that was modified before the agent ran and is clean
afterwards has been reverted, and a reversion is a modification. Appearing,
disappearing, and changing all count.

A breach is NOT a gate violation. Gates are for work an agent can be asked to
redo; a breach cannot be corrected by re-prompting, because the write already
happened. It aborts the phase and names every offending path.

Three keys drive it, all in sssf.config.yaml:
    defaults.protected_files   paths no agent may touch unless it names them itself
    defaults.protected_evaluator_paths   the acceptance surface frozen for this
                               task generation — the machinery that decides
                               whether the work passed. Unlike protected_files,
                               a broad prefix in an agent's own `writes` does
                               not carry one of these along with it; only a
                               declaration scoped inside the surface does, and
                               that declaration is the explicit evaluator
                               revision the law requires.
    agents[].writes      None = unrestricted · [] = read-only · [...] = only these
"""

from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .data_types import AgentConfig, SSSFConfig


class PermissionBreach(RuntimeError):
    """An agent modified a path it was not permitted to modify."""


class SnapshotUnobservable(PermissionBreach):
    """The repository change set could not be observed."""


# The `_roll_back` outcomes that leave the repo byte-for-byte as it was. The
# docstring's reason for aborting — "the write already happened" — is true of a
# destroyed file and false of these: an agent-created file that was unlinked, or
# a tracked edit that was checked out, leaves nothing behind to re-prompt around.
RECOVERED = {"deleted", "rolled back", "restored"}

# ...but only as a slip. One phase producing more than this many out-of-scope
# writes is a pattern, not an accident, and stops being forgiven.
RECOVERED_LIMIT = 3

# Per-file ceiling on what `preserve` will hold in memory for the length of a
# phase. Anything larger keeps the old behaviour — reported, not restorable.
PRESERVE_MAX_BYTES = 1 << 20


@dataclass(frozen=True)
class PreservedPath:
    kind: str
    body: bytes
    mode: int


class TreeSnapshot(dict[str, str]):
    def __init__(self, fingerprints: dict[str, str], base_commit: str,
                 base_tree: str) -> None:
        super().__init__(fingerprints)
        self.base_commit = base_commit
        self.base_tree = base_tree


def _git_out(args: list[str], cwd) -> str | None:
    """git's answer, or None when git ran and refused to give one.

    Deliberately does NOT swallow an unreachable git: a snapshot that quietly
    came back empty because git was missing would report that no agent changed
    anything, which is the one wrong answer this module must never give. The
    caller that needs an unreachable git as a third value catches it itself.
    """
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else None


def _git(args: list[str], cwd) -> str:
    try:
        output = _git_out(args, cwd)
    except OSError as error:
        raise SnapshotUnobservable(
            f"permission snapshot could-not-observe: git {' '.join(args)}"
        ) from error
    if output is None:
        raise SnapshotUnobservable(
            f"permission snapshot could-not-observe: git {' '.join(args)}"
        )
    return output


def _repository_identity(target: Path) -> str:
    metadata = target.lstat()
    if stat.S_ISLNK(metadata.st_mode):
        mode = "120000"
        body = os.fsencode(os.readlink(target))
    elif stat.S_ISREG(metadata.st_mode):
        mode = "100755" if metadata.st_mode & 0o111 else "100644"
        body = target.read_bytes()
    else:
        mode = f"type:{stat.S_IFMT(metadata.st_mode):o}"
        body = b""
    return f"{mode}:{hashlib.sha256(body).hexdigest()}"


def _head_identity(run) -> tuple[str, str]:
    resolved = [line.strip() for line in _git(
        ["show", "-s", "--format=%H%n%T", "HEAD"],
        run.repo_root,
    ).splitlines() if line.strip()]
    if len(resolved) != 2:
        raise SnapshotUnobservable(
            "permission snapshot could-not-observe: incomplete HEAD identity"
        )
    return resolved[0], resolved[1]


def _require_pinned_identity(run, snapshot: TreeSnapshot) -> None:
    identity = f"{snapshot.base_commit}:{snapshot.base_tree}"
    try:
        resolved = [line.strip() for line in _git(
            ["show", "-s", "--format=%H%n%T", snapshot.base_commit],
            run.repo_root,
        ).splitlines() if line.strip()]
    except SnapshotUnobservable as error:
        raise SnapshotUnobservable(
            f"permission snapshot could-not-observe pinned base {identity}"
        ) from error
    if resolved != [snapshot.base_commit, snapshot.base_tree]:
        raise SnapshotUnobservable(
            f"permission snapshot could-not-observe pinned base {identity}"
        )


def _snapshot_against(run, base_commit: str, base_tree: str) -> TreeSnapshot:
    """Fingerprint every path the working tree currently differs on.

    Tracked files ordinarily carry their numstat counts. Frozen evaluator files
    carry content digests, so a same-numstat rewrite of an already-dirty grader
    still registers as a change. Untracked frozen evaluators are also digested.
    Other untracked files are listed by name.
    Gitignored paths never appear, which is why the session runtime under
    `data_dir` — where handoff files legitimately land — needs no special case.
    """
    fingerprints: dict[str, str] = {}
    for line in _git(
        ["diff", base_commit, "--numstat"], run.repo_root
    ).splitlines():
        fields = line.split("\t")
        if len(fields) >= 3:
            path = fields[-1].strip()
            if is_frozen_evaluator(path, run.cfg):
                target = Path(run.repo_root) / path
                identity = _repository_identity(target) \
                    if target.exists() or target.is_symlink() else "absent"
                fingerprints[path] = f"content:{identity}"
            else:
                fingerprints[path] = f"{fields[0]},{fields[1]}"
    for path in _git(["ls-files", "--others", "--exclude-standard"],
                     run.repo_root).splitlines():
        if path.strip():
            path = path.strip()
            if is_frozen_evaluator(path, run.cfg):
                identity = _repository_identity(Path(run.repo_root) / path)
                fingerprints[path] = f"untracked:{identity}"
            else:
                fingerprints[path] = "untracked"
    return TreeSnapshot(fingerprints, base_commit, base_tree)


def snapshot(run) -> TreeSnapshot:
    base_commit, base_tree = _head_identity(run)
    return _snapshot_against(run, base_commit, base_tree)


def changed_paths(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Every path whose state differs — appeared, vanished, or was rewritten."""
    return sorted({p for p in set(before) | set(after)
                   if before.get(p) != after.get(p)})


def _glob(pattern: str) -> re.Pattern:
    """Translate a pattern, with `*` stopping at a path separator.

    fnmatch would let `*` cross `/`, which quietly widens every pattern:
    `adws/adw_*.py` would match `adws/adw_data/sessions/x/y.py` as well as the
    ADW scripts it means. `**` is the way to say "cross directories".
    """
    out, i = [], 0
    while i < len(pattern):
        char = pattern[i]
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif char == "*":
            out.append("[^/]*")
            i += 1
        elif char == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(char))
            i += 1
    return re.compile("".join(out))


def _matches(path: str, pattern: str) -> bool:
    if pattern.endswith("/"):                      # directory prefix
        return path.startswith(pattern)
    if "*" in pattern or "?" in pattern:
        return _glob(pattern).fullmatch(path) is not None
    return path == pattern


def always_writable(cfg: SSSFConfig) -> list[str]:
    """The session runtime, which EVERY agent must be able to write.

    `context_handoff/` is the one place agents hand work to each other, and an
    agent's own prompts, raw_output.jsonl, and envelope.json land beside it.
    Scout writes its findings there, the reviewer its review, the planner its
    plan — a read-only agent is read-only with respect to the REPO, never with
    respect to its own report.

    This is granted from `data_dir` rather than left to .gitignore. The runtime
    is normally ignored, so it never even appears in a snapshot — but an agent's
    ability to record its work must not hang on a gitignore entry that someone
    can delete or that a changed `data_dir` can outgrow.

    Scoped to `sessions/`, which is where the runtime actually lives —
    `{data_dir}/sessions/{adw_id}/{agent_name}/`, built in adw_modules/runner.py.
    `data_dir` also holds TRACKED surfaces that grade the work: every agent's
    `prompt_engineering/` and the `harness_engineering/` extensions loaded into
    the harness. Granting the whole directory handed every agent a write on
    every other agent's prompt — and handed it first, ahead of every protection
    below, which is exactly why the too-wide scope was invisible. The order is
    deliberate and unchanged; only the scope was wrong.
    """
    return [cfg.defaults.data_dir.rstrip("/") + "/sessions/"]


def frozen_evaluator_paths(cfg: SSSFConfig) -> list[str]:
    """The acceptance surface frozen for the active task generation.

    Empty is a real answer, and it is not "nothing to protect": it is a roster
    that has declared no evaluator surface, which `evaluator_generation` reports
    as could-not-observe rather than as an intact one.
    """
    return list(cfg.defaults.protected_evaluator_paths)


def is_frozen_evaluator(path: str, cfg: SSSFConfig) -> bool:
    return any(_matches(path, p) for p in frozen_evaluator_paths(cfg))


def _revises_evaluator(declaration: str, cfg: SSSFConfig) -> bool:
    """True when a `writes` entry is itself inside the frozen surface.

    Naming a path is what unlocks a protected one, and that stays true here —
    but only for a declaration narrow enough to BE an evaluator revision.
    `docs/` is a decision about documentation that happens to contain
    `docs/validation/`; treating it as consent to rewrite the graders is how an
    acceptance surface gets edited by an agent nobody meant to hand it to.
    Since the roster is itself a protected file, a declaration inside the
    surface can only arrive by a deliberate edit from outside the run — which
    is what makes it the explicit revision transition.
    """
    return any(_matches(declaration, p) for p in frozen_evaluator_paths(cfg))


def permitted(path: str, agent: AgentConfig, cfg: SSSFConfig) -> bool:
    """Session runtime first, then the agent's own list, then what is protected.

    The order is the original one. The frozen evaluator surface is consulted
    after `protected_files`, never before the session runtime, because an agent
    that cannot write its own report is an agent that cannot report a refusal.
    """
    if any(_matches(path, p) for p in always_writable(cfg)):
        return True
    declarations = agent.writes or []
    if any(_matches(path, p) for p in declarations):
        # Naming a path is what unlocks a protected one. For the frozen
        # evaluator surface the naming has to be an evaluator revision — a
        # declaration inside the surface — and not a broad grant above it that
        # would carry the grader along with the work it grades.
        if not is_frozen_evaluator(path, cfg):
            return True
        return any(_matches(path, d) and _revises_evaluator(d, cfg)
                   for d in declarations)
    if any(_matches(path, p) for p in cfg.defaults.protected_files):
        return False
    if is_frozen_evaluator(path, cfg):
        return False
    return agent.writes is None          # None = unrestricted, [] = no repo writes


def evaluator_generation(run) -> str | None:
    """The identity of the frozen evaluator surface as it stands right now.

    Evidence is only ever evidence about a generation. A legitimate evaluator
    change is explicit — declared in the roster, which no agent can edit — and
    the moment those bytes move this digest moves with them, so evidence
    recorded against the old digest describes an acceptance surface that no
    longer exists.

    Three-valued. `None` is could-not-observe, and it is returned whenever the
    surface cannot be resolved: no surface declared, no git to enumerate the
    tracked tree, a declaration that matches nothing, or a member that cannot be
    read. An evaluator surface nobody could look at is never evidence that the
    evaluator is intact.
    """
    if not frozen_evaluator_paths(run.cfg):
        return None
    try:
        listing = _git_out(
            ["ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            run.repo_root,
        )
    except OSError:
        return None                      # no git, or no tree to ask it about
    if listing is None:
        return None
    digest, members = hashlib.sha256(), 0
    declarations = sorted(set(frozen_evaluator_paths(run.cfg)))
    for declaration in declarations:
        digest.update(f"declaration\0{declaration}\0".encode())
    for path in sorted(p for p in listing.split("\0") if p):
        if not is_frozen_evaluator(path, run.cfg):
            continue
        target = Path(run.repo_root) / path
        try:
            body = (_repository_identity(target)
                    if target.exists() or target.is_symlink() else "absent")
        except OSError:
            return None                  # a member we could not read is not a state
        digest.update(f"{path}\0{body}\0".encode())
        members += 1
    if not members:
        return None                      # declared a surface, resolved nothing
    return digest.hexdigest()


def evidence_is_current(recorded: str | None, run) -> bool | None:
    """Does evidence recorded against `recorded` still describe this surface?

    `None` is could-not-observe — nothing recorded, or nothing observable now —
    and never stands in for "yes".
    """
    current = evaluator_generation(run)
    if recorded is None or current is None:
        return None
    return recorded == current


def preserve(run, tree: TreeSnapshot) -> dict[str, PreservedPath]:
    """Capture every restorable already-dirty path before an agent runs.

    Without this, the module can only undo what an agent INTRODUCED — unlink a
    file it created, `git checkout` an edit it made on top of a clean file. Work
    that was already uncommitted when the phase opened was unrecoverable, and
    unrecoverable is precisely what aborts a run. Holding the state turns the
    module's worst case (`git checkout adws/`, the incident in the docstring
    above) from "reported, gone" into "put back", which is both less damage and
    one less dead run.

    Reading is best-effort: a path that vanishes between snapshot and read, or
    is too large to hold, simply is not preserved and keeps the old behaviour.
    """
    kept: dict[str, PreservedPath] = {}
    for path in tree:
        target = Path(run.repo_root) / path
        try:
            metadata = target.lstat()
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISLNK(metadata.st_mode):
                body = os.fsencode(os.readlink(target))
                if len(body) <= PRESERVE_MAX_BYTES:
                    kept[path] = PreservedPath("symlink", body, mode)
            elif (stat.S_ISREG(metadata.st_mode)
                  and metadata.st_size <= PRESERVE_MAX_BYTES):
                kept[path] = PreservedPath("file", target.read_bytes(), mode)
        except OSError:
            continue
    return kept


def _restore(run, path: str, preserved: dict[str, PreservedPath]) -> bool:
    """Put a preserved path back exactly as it was. True if it is now restored."""
    if path not in preserved:
        return False
    target = Path(run.repo_root) / path
    saved = preserved[path]
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            target.unlink()
        elif target.exists() and not target.is_file():
            return False
        if saved.kind == "symlink":
            if target.exists():
                target.unlink()
            target.symlink_to(os.fsdecode(saved.body))
        else:
            if target.exists():
                target.unlink()
            target.write_bytes(saved.body)
            target.chmod(saved.mode)
        return True
    except OSError:
        return False


def _roll_back(run, path: str, before: TreeSnapshot, after: dict[str, str],
               preserved: dict[str, PreservedPath]) -> str:
    """Undo one unauthorized change. Returns a word describing what happened.

    A path that was already dirty when the agent started is restored to the
    bytes `preserve` captured, so the operator's uncommitted work survives an
    agent that overwrote or deleted it. Only when those bytes are unavailable
    does the old behaviour apply: leave it alone and say so, because discarding
    an operator's work to tidy up would be the same harm this module exists to
    prevent, committed by the cleanup instead of the agent.
    """
    if path in before:
        # Already dirty beforehand — the agent either reverted it or edited it
        # again. Either way the version that belongs here is the operator's.
        if _restore(run, path, preserved):
            return "restored"
        return "REVERTED-BY-AGENT (uncommitted work lost, cannot restore)" \
            if path not in after else "left as-is (was already modified)"
    if (after.get(path) or "").startswith("untracked"):
        try:
            (Path(run.repo_root) / path).unlink()
            return "deleted"
        except OSError as error:
            return f"could not delete ({error})"
    result = subprocess.run(["git", "checkout", before.base_commit, "--", path],
                            cwd=run.repo_root, capture_output=True, text=True)
    return "rolled back" if result.returncode == 0 else "could not roll back"


def enforce(run, phase, agent: AgentConfig, before: TreeSnapshot,
            preserved: dict[str, PreservedPath] | None = None) -> list[str]:
    """Compare the tree against `before`; undo and raise if the agent overstepped.

    Returns the paths it legitimately changed, so the trace records what an
    agent actually touched rather than only what it claimed in its envelope.

    Detection alone would leave the repo holding the unauthorized change while
    reporting a failure, so anything the agent introduced outside its allowlist
    is rolled back before the phase dies. What it cannot undo, it names.
    """
    if not isinstance(before, TreeSnapshot):
        raise SnapshotUnobservable(
            "permission snapshot could-not-observe: missing armed base identity"
        )
    _require_pinned_identity(run, before)
    after = _snapshot_against(run, before.base_commit, before.base_tree)
    touched = changed_paths(before, after)
    breaches = [p for p in touched if not permitted(p, agent, run.cfg)]
    if not breaches:
        return touched

    outcomes = {p: _roll_back(run, p, before, after, preserved or {})
                for p in breaches}
    scope = ("read-only" if agent.writes == []
             else f"limited to {agent.writes}" if agent.writes
             else f"barred from {run.cfg.defaults.protected_files}")
    detail = "\n".join(f"  - {p} — {outcome}" for p, outcome in outcomes.items())

    # Aborting is about damage, not about the rule. When every offending path
    # was put back and there were only a few, the tree is exactly what it would
    # have been had the agent stayed in scope — so the run continues, loudly.
    # A scratch file redirected into the repo should not kill a 13-phase run.
    #
    # The frozen evaluator surface is the exception, and it is why rollback is
    # defense in depth here rather than the guard. "It was put back" answers the
    # damage question; it does not make an attempt on the acceptance surface a
    # slip, and a run that reached for its own grader has not earned the
    # forgiving path.
    unrecovered = [p for p, outcome in outcomes.items() if outcome not in RECOVERED]
    frozen = [p for p in outcomes if is_frozen_evaluator(p, run.cfg)]
    if not unrecovered and not frozen and len(outcomes) <= RECOVERED_LIMIT:
        run.console.note(
            f"permission: {agent.name} is {scope}; "
            f"{len(outcomes)} out-of-scope path(s) undone, continuing:\n{detail}")
        return [p for p in touched if p not in outcomes]

    surface = (f"; {len(frozen)} of them frozen evaluator path(s) against "
               f"pinned base {before.base_commit}:{before.base_tree}: "
               f"{', '.join(frozen)}" if frozen else "")
    raise PermissionBreach(
        f"{agent.name} is {scope} but modified {len(breaches)} path(s)"
        f"{surface}:\n{detail}")
