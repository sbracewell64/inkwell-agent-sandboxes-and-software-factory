"""What an agent may CHANGE, enforced in code.

`tools:` is a capability list, not a sandbox, and two holes make it
unenforceable on its own:

  * `bash` runs anything. A builder handed bash to run a test suite can also
    run `git checkout adws/` — which is not hypothetical: one did, discarding
    uncommitted changes to the very quality check it was about to be judged by.
  * `write` reaches any path, not just the one report file an agent was given
    it for. A reviewer configured with "no edit, so it cannot quietly fix"
    could still rewrite the code it was reviewing.

Ordinary write boundaries are verified the way every other claim in this system
is — after the fact, against the repo itself. `snapshot()` fingerprints the
working tree's change-set before an agent runs; `enforce()` compares it
afterwards and fails the phase if the agent touched anything outside its
allowlist. Frozen evaluator paths additionally refuse at the `permitted()`
decision unless the agent carries an explicit declaration scoped inside that
surface. Their post-effect snapshot and rollback are damage containment, not
the authority that makes the evaluator writable.

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
from pathlib import Path, PurePosixPath

from .data_types import AgentConfig, SSSFConfig


class PermissionBreach(RuntimeError):
    """An agent modified a path it was not permitted to modify."""


class SnapshotUnobservable(PermissionBreach):
    """The repository change set could not be observed."""


class IndexVisibilityBreach(PermissionBreach):
    """A protected evaluator has hidden index state."""


class EvaluatorSurfaceUndeclared(PermissionBreach):
    """No evaluator surface is declared, so none can be observed as intact."""


class EvaluatorSurfaceUnobservable(PermissionBreach):
    """A declared evaluator surface cannot be observed in full."""


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
                 base_tree: str, unresolved: list[str] | None = None,
                 absent: list[str] | None = None,
                 visibility: dict[str, list[str]] | None = None,
                 unreadable: list[str] | None = None,
                 visibility_unobservable: str | None = None,
                 visibility_sources: dict[str, list[str]] | None = None) -> None:
        super().__init__(fingerprints)
        self.base_commit = base_commit
        self.base_tree = base_tree
        self.unresolved = unresolved or []
        self.absent = absent or []
        self.visibility = visibility or {}
        self.unreadable = unreadable or []
        self.visibility_unobservable = visibility_unobservable
        self.visibility_sources = visibility_sources or {}


class RepositoryPaths(dict[str, str]):
    def __init__(self, paths: dict[str, str],
                 unreadable: list[str] | None = None) -> None:
        super().__init__(paths)
        self.unreadable = unreadable or []


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


def _tagged_paths(listing: str) -> dict[str, str]:
    tagged: dict[str, str] = {}
    for entry in listing.split("\0"):
        if len(entry) >= 3 and entry[1] == " ":
            tagged[entry[2:]] = entry[0]
    return tagged


def _walk_root(root: Path, declaration: str) -> Path | None:
    wildcard = min(
        (position for marker in "*?"
         if (position := declaration.find(marker)) >= 0),
        default=-1,
    )
    if wildcard < 0:
        if not declaration.endswith("/"):
            return None
        prefix = declaration.rstrip("/")
    else:
        prefix = declaration[:wildcard]
        if not prefix.endswith("/"):
            prefix = prefix.rpartition("/")[0]
    candidate = root / prefix
    try:
        candidate.absolute().relative_to(root.absolute())
    except ValueError:
        return None
    return candidate


def _surface_walk_roots(root: Path, declarations: list[str]) -> list[Path]:
    candidates = {
        candidate
        for declaration in declarations
        if (candidate := _walk_root(root, declaration)) is not None
    }
    return sorted(
        candidate for candidate in candidates
        if not any(parent != candidate and parent in candidate.parents
                   for parent in candidates)
    )


def _repository_paths(run) -> RepositoryPaths:
    paths = _tagged_paths(_git(
        ["ls-files", "-v", "-z", "--cached", "--others", "--exclude-standard"],
        run.repo_root,
    ))
    root = Path(run.repo_root)
    declarations = sorted(set(frozen_evaluator_paths(run.cfg)))
    unreadable: list[str] = []
    for declaration in declarations:
        if _walk_root(root, declaration) is not None:
            continue
        target = root / declaration
        try:
            target.absolute().relative_to(root.absolute())
            if target.exists() or target.is_symlink():
                paths.setdefault(declaration, "?")
        except (OSError, ValueError):
            continue

    def record_unreadable(error: OSError) -> None:
        location = Path(error.filename) if error.filename else root
        try:
            unreadable.append(location.relative_to(root).as_posix())
        except ValueError:
            unreadable.append(str(location))

    for walk_root in _surface_walk_roots(root, declarations):
        if not walk_root.exists() and not walk_root.is_symlink():
            continue
        for current, directories, filenames in os.walk(
                walk_root, followlinks=False, onerror=record_unreadable):
            relative_dir = Path(current).relative_to(root)
            if relative_dir == Path("."):
                directories[:] = [name for name in directories if name != ".git"]
            for name in filenames:
                relative = (relative_dir / name).as_posix()
                if is_frozen_evaluator(relative, run.cfg):
                    paths.setdefault(relative, "?")
            for name in list(directories):
                candidate = Path(current) / name
                if candidate.is_symlink():
                    relative = (relative_dir / name).as_posix()
                    if is_frozen_evaluator(relative, run.cfg):
                        paths.setdefault(relative, "?")
    return RepositoryPaths(paths, sorted(set(unreadable)))


# Membership under a directory declaration is TRACKED-ELIGIBLE content: what a
# reviewer can see and freeze. Build output is not a second evaluator — a
# `__pycache__` tree beside its tracked sources is the same code the reviewer
# already read, and refusing it would make every phase on a machine that has
# run the suite once refuse for no security reason.
#
# The exception is executable content with no tracked source under the surface:
# a sourceless `.pyc`, a shadowing `.so`, an ignored `.py`. That is evaluator
# code that runs without ever being reviewable, which is the hiding vector the
# surface exists to close, so it refuses and names itself.
EXECUTABLE_SUFFIXES = frozenset({
    ".py", ".pyc", ".pyo", ".pyd", ".so", ".dll", ".dylib", ".wasm",
    ".exe", ".com", ".cmd", ".bat", ".ps1",
    ".sh", ".bash", ".zsh", ".fish", ".ts", ".js", ".mjs",
})


def _derived_source(path: str) -> str | None:
    """The tracked source a derived artifact claims to come from, if any."""
    candidate = PurePosixPath(path)
    if candidate.suffix not in {".pyc", ".pyo"}:
        return None
    parent = candidate.parent
    if parent.name == "__pycache__":
        parent = parent.parent
    # `x.cpython-314.pyc` -> `x.py`; a plain `x.pyc` -> `x.py` as well.
    return (parent / f"{candidate.stem.split('.')[0]}.py").as_posix()


def _ignored_member_is_hidden(run, path: str, paths: dict[str, str]) -> bool:
    """Does this ignored path hide executable evaluator content from review?"""
    source = _derived_source(path)
    if source is not None:
        tag = paths.get(source)
        if tag is not None and tag != "?" and is_frozen_evaluator(source, run.cfg):
            return False                 # derived from a member review can see
    try:
        executable_mode = (Path(run.repo_root) / path).lstat().st_mode & 0o111
    except OSError:
        executable_mode = 0
    return bool(executable_mode) or PurePosixPath(path).suffix.lower() in EXECUTABLE_SUFFIXES


def _gitignore_observation(run, paths: dict[str, str]) \
        -> tuple[set[str], dict[str, list[str]]]:
    candidates = sorted(path for path, tag in paths.items()
                        if tag == "?" and is_frozen_evaluator(path, run.cfg))
    if not candidates:
        return set(), {}
    try:
        result = subprocess.run(
            ["git", "check-ignore", "--no-index", "-v", "-z", "--stdin"],
            cwd=run.repo_root, input="\0".join(candidates) + "\0",
            capture_output=True, text=True,
        )
    except OSError as error:
        raise SnapshotUnobservable(
            "permission snapshot could-not-observe gitignore visibility"
        ) from error
    if result.returncode not in {0, 1}:
        raise SnapshotUnobservable(
            "permission snapshot could-not-observe gitignore visibility"
        )
    fields = result.stdout.split("\0")
    ignored, sources = set(), {}
    for offset in range(0, len(fields) - 3, 4):
        source, path = fields[offset], fields[offset + 3]
        if not path:
            continue
        ignored.add(path)
        source_path = Path(source)
        if source_path.is_absolute():
            try:
                source = source_path.relative_to(run.repo_root).as_posix()
            except ValueError:
                continue
        if source and source != ".git/info/exclude":
            sources.setdefault(path, []).append(source)
    return ignored, sources


def _visibility_observation(run, paths: dict[str, str]) \
        -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    fsmonitor = _tagged_paths(_git(
        ["ls-files", "-f", "-z", "--cached"], run.repo_root
    ))
    ignored, sources = _gitignore_observation(run, paths)
    violations = {}
    for path, tag in paths.items():
        if not is_frozen_evaluator(path, run.cfg):
            continue
        flags: list[str] = []
        if tag == "?":
            if path in ignored and _ignored_member_is_hidden(run, path, paths):
                flags.append("gitignore")
        else:
            if tag in {"S", "s"}:
                flags.append("skip-worktree")
            if tag.islower():
                flags.append("assume-unchanged")
            if fsmonitor.get(path, "").islower():
                flags.append("fsmonitor-valid")
        if flags:
            violations[path] = flags
    return violations, sources


def _visibility_violations(run, paths: dict[str, str]) -> dict[str, list[str]]:
    return _visibility_observation(run, paths)[0]


def _visibility_detail(violations: dict[str, list[str]]) -> str:
    return "; ".join(
        f"{', '.join(flags)} on {path}"
        for path, flags in violations.items()
    )


def _refuse_hidden_evaluators(run, paths: dict[str, str]) -> None:
    violations = _visibility_violations(run, paths)
    if violations:
        raise IndexVisibilityBreach(
            "permission: protected evaluator index visibility flag(s) "
            + _visibility_detail(violations)
        )


def _numstat(run, base_commit: str, unreadable: list[str]) -> str:
    """The tracked delta against the pinned base, around unreadable members.

    An unreadable protected member makes git refuse the whole-tree diff, and
    that refusal would otherwise abandon enumeration entirely — losing the
    unrelated unauthorized changes this phase still has to roll back. The tree
    is enumerable; one member is not. So the diff is retried excluding exactly
    the members we already know we cannot read, and they keep their own
    `unreadable` fingerprints either way. Only a diff that fails with nothing
    left to exclude is a genuinely unobservable tree.
    """
    try:
        return _git(["diff", base_commit, "--numstat"], run.repo_root)
    except SnapshotUnobservable:
        if not unreadable:
            raise
    return _git(
        ["diff", base_commit, "--numstat", "--", "."]
        + [f":(exclude){path}" for path in unreadable],
        run.repo_root,
    )


def _snapshot_against(run, base_commit: str, base_tree: str,
                      require_observable: bool = False) -> TreeSnapshot:
    """Fingerprint every path the working tree currently differs on.

    Tracked files ordinarily carry their numstat counts. Frozen evaluator files
    carry content digests, so a same-numstat rewrite of an already-dirty grader
    still registers as a change. Untracked frozen evaluators are also digested.
    Other visible untracked files are listed by name. Frozen members are
    enumerated independently from the filesystem, including ignored members;
    ignored runtime outside the declaration remains outside the snapshot.
    """
    fingerprints: dict[str, str] = {}
    repository_paths = _repository_paths(run)
    try:
        visibility, visibility_sources = _visibility_observation(
            run, repository_paths
        )
        visibility_unobservable = None
    except SnapshotUnobservable as error:
        visibility = {}
        visibility_sources = {}
        visibility_unobservable = str(error)
    unresolved, absent = _surface_observation(run, repository_paths)
    unreadable = list(repository_paths.unreadable)
    for path in repository_paths:
        if not is_frozen_evaluator(path, run.cfg):
            continue
        target = Path(run.repo_root) / path
        try:
            identity = _repository_identity(target) \
                if target.exists() or target.is_symlink() else "absent"
        except OSError:
            unreadable.append(path)
            identity = "unreadable"
        fingerprints[path] = f"frozen:{identity}"
    for line in _numstat(run, base_commit, unreadable).splitlines():
        fields = line.split("\t")
        if len(fields) >= 3:
            path = fields[-1].strip()
            if not is_frozen_evaluator(path, run.cfg):
                fingerprints[path] = f"{fields[0]},{fields[1]}"
    for path, tag in repository_paths.items():
        if tag == "?" and not is_frozen_evaluator(path, run.cfg):
            fingerprints[path] = "untracked"
    tree = TreeSnapshot(
        fingerprints, base_commit, base_tree, unresolved, absent, visibility,
        unreadable, visibility_unobservable, visibility_sources,
    )
    if require_observable:
        if visibility_unobservable:
            raise SnapshotUnobservable(visibility_unobservable)
        if visibility:
            raise IndexVisibilityBreach(
                "permission: protected evaluator index visibility flag(s) "
                + _visibility_detail(visibility)
            )
        _require_observable_surface(run, repository_paths)
        if unreadable:
            raise EvaluatorSurfaceUnobservable(
                "permission could-not-observe protected evaluator surface; "
                f"unreadable member(s): {', '.join(unreadable)}"
            )
    return tree


def _surface_observation(run, paths: dict[str, str]) -> tuple[list[str], list[str]]:
    declarations = sorted(set(frozen_evaluator_paths(run.cfg)))
    unresolved = [declaration for declaration in declarations
                  if not any(_matches(path, declaration) for path in paths)]
    absent = []
    for path in sorted(paths):
        if not is_frozen_evaluator(path, run.cfg):
            continue
        target = Path(run.repo_root) / path
        if not target.exists() and not target.is_symlink():
            absent.append(path)
    return unresolved, absent


def _require_observable_surface(run, paths: dict[str, str]) -> None:
    unresolved, absent = _surface_observation(run, paths)
    if not unresolved and not absent:
        return
    details = []
    if unresolved:
        details.append(f"unresolved declaration(s): {', '.join(unresolved)}")
    if absent:
        details.append(f"absent member(s): {', '.join(absent)}")
    raise EvaluatorSurfaceUnobservable(
        "permission could-not-observe protected evaluator surface; "
        + "; ".join(details)
    )


def _require_declared_surface(run) -> None:
    """An undeclared evaluator surface is could-not-observe, so it refuses.

    A roster that names no protected evaluator path has not declared a small
    surface — it has declared nothing, and nothing is what every check of it
    would then vacuously agree with. That is the fail-open shape this module
    exists to refuse, and it is exactly the state a freshly installed factory
    starts in, so it fails loudly at the phase boundary instead of running
    unprotected and reporting success.
    """
    if not frozen_evaluator_paths(run.cfg):
        raise EvaluatorSurfaceUndeclared(
            "permission could-not-observe: defaults.protected_evaluator_paths "
            "declares no evaluator surface, so no phase can be judged against "
            "one — declare the acceptance surface for this task generation"
        )


def snapshot(run) -> TreeSnapshot:
    _require_declared_surface(run)
    base_commit, base_tree = _head_identity(run)
    return _snapshot_against(run, base_commit, base_tree, require_observable=True)


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
        paths = _repository_paths(run)
        if paths.unreadable:
            return None
        _refuse_hidden_evaluators(run, paths)
        _require_observable_surface(run, paths)
    except (OSError, PermissionBreach):
        return None                      # no git, or no tree to ask it about
    digest, members = hashlib.sha256(), 0
    declarations = sorted(set(frozen_evaluator_paths(run.cfg)))
    for declaration in declarations:
        digest.update(f"declaration\0{declaration}\0".encode())
    for path in sorted(paths):
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
        return None
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
    try:
        result = subprocess.run(
            ["git", "checkout", before.base_commit, "--", path],
            cwd=run.repo_root, capture_output=True, text=True,
        )
    except OSError as error:
        return f"could not roll back ({error})"
    return "rolled back" if result.returncode == 0 else "could not roll back"


def _clear_visibility(run, path: str, flags: list[str]) -> str:
    options = {
        "assume-unchanged": "--no-assume-unchanged",
        "skip-worktree": "--no-skip-worktree",
        "fsmonitor-valid": "--no-fsmonitor-valid",
    }
    try:
        result = subprocess.run(
            ["git", "update-index", *(options[flag] for flag in flags), "--", path],
            cwd=run.repo_root, capture_output=True, text=True,
        )
    except OSError as error:
        return f"could not restore visibility ({error})"
    return "visibility restored" if result.returncode == 0 \
        else "could not restore visibility"


def _rollback_unavailable(error: PermissionBreach) -> PermissionBreach:
    return type(error)(
        f"{error}; rollback could not be attempted because the tree was "
        "unobservable"
    )


def enforce(run, phase, agent: AgentConfig, before: TreeSnapshot,
            preserved: dict[str, PreservedPath] | None = None) -> list[str]:
    """Compare the tree against `before`; undo and raise if the agent overstepped.

    Returns the paths it legitimately changed, so the trace records what an
    agent actually touched rather than only what it claimed in its envelope.

    Detection alone would leave the repo holding the unauthorized change while
    reporting a failure, so anything the agent introduced outside its allowlist
    is rolled back before the phase dies. What it cannot undo, it names.
    """
    identity_refusal = None
    try:
        if not isinstance(before, TreeSnapshot):
            base_commit, base_tree = _head_identity(run)
            before = TreeSnapshot(dict(before), base_commit, base_tree)
            identity_refusal = SnapshotUnobservable(
                "permission snapshot could-not-observe: missing armed base identity"
            )
        else:
            try:
                _require_pinned_identity(run, before)
            except SnapshotUnobservable as error:
                identity_refusal = error
        if identity_refusal:
            current_commit, current_tree = _head_identity(run)
            after = _snapshot_against(run, current_commit, current_tree)
        else:
            after = _snapshot_against(run, before.base_commit, before.base_tree)
    except SnapshotUnobservable as error:
        raise _rollback_unavailable(error) from error
    touched = changed_paths(before, after)
    unresolved, absent = after.unresolved, after.absent
    undeclared = not frozen_evaluator_paths(run.cfg)
    if (undeclared or unresolved or absent or after.visibility
            or after.unreadable or after.visibility_unobservable
            or identity_refusal):
        rollback_targets = sorted({
            path for path in touched
            if (not permitted(path, agent, run.cfg)
                or is_frozen_evaluator(path, run.cfg))
        } | set(after.visibility) | {
            source
            for sources in after.visibility_sources.values()
            for source in sources
            if source in touched
        })
        outcomes = {
            path: _roll_back(run, path, before, after, preserved or {})
            for path in rollback_targets
        }
        for path, flags in after.visibility.items():
            index_flags = [flag for flag in flags if flag != "gitignore"]
            if index_flags:
                restored = _clear_visibility(run, path, index_flags)
                outcomes[path] = f"{outcomes.get(path, 'unchanged')}; {restored}"
        details = []
        if undeclared:
            details.append("defaults.protected_evaluator_paths declares no surface")
        if unresolved:
            details.append(f"unresolved declaration(s): {', '.join(unresolved)}")
        if absent:
            details.append(f"absent member(s): {', '.join(absent)}")
        if after.unreadable:
            details.append(
                f"unreadable member(s): {', '.join(after.unreadable)}"
            )
        if after.visibility:
            details.append(
                "index visibility flag(s): "
                + _visibility_detail(after.visibility)
            )
        if after.visibility_unobservable:
            details.append(after.visibility_unobservable)
        if identity_refusal:
            details.append(str(identity_refusal))
        if outcomes:
            details.append("effects:\n" + "\n".join(
                f"  - {path} — {outcome}"
                for path, outcome in outcomes.items()
            ))
        refusal = SnapshotUnobservable \
            if after.visibility_unobservable or identity_refusal \
            else IndexVisibilityBreach if after.visibility \
            else EvaluatorSurfaceUndeclared if undeclared \
            else EvaluatorSurfaceUnobservable
        raise refusal("permission could-not-observe protected evaluator surface; "
                      + "; ".join(details))
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
