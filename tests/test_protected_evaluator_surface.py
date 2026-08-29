"""Executable proof that the frozen evaluator surface refuses its own maker.

SDLC-L2 — evaluator immutability. Once an acceptance surface is established for
a task generation, the maker or the optimizer must not be able to weaken or
rewrite that surface while trying to satisfy it. A legitimate evaluator change
is an explicit revision: it is declared in the roster — itself a protected file
no agent can edit — and it creates a new generation that invalidates evidence
bound to the old one.

The four cases the law requires, in order:

  1. a bug-fix agent attempting to delete or relax the failing test is refused;
  2. an optimizer reaching a scorer path through a broad grant is refused;
  3. a genuinely defective evaluator produces an explicit revision that creates
     a new generation and invalidates the old evidence;
  4. an unrelated test file outside the frozen property scope still changes
     freely.

Two boundaries are proven beside them, because getting either wrong would be a
worse defect than the one this closes:

  * the session-runtime grant is still consulted FIRST and still wins over a
    protected path. The precedence is not reversed — only its scope narrowed,
    from all of `data_dir` to the `sessions/` runtime it always meant;
  * rollback is not the guard. A frozen-surface breach aborts the phase even
    when every offending path was successfully put back.

Deliberately not proven here, because it is not built here: held-out/hidden
benchmark ACCESS control — reading a holdout rather than writing a scorer —
which belongs to `AL-1` and its `SBX-4` execution boundary; and any pre-tool
projection into the coding harness, which SSSF does not ship.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from adw_modules import agents, permissions
from adw_modules.data_types import (
    AgentConfig,
    ConfigDefaults,
    PromptEngineering,
    SSSFConfig,
)

ROOT = Path(__file__).resolve().parents[1]
ROSTERS = sorted((ROOT / "adws" / "adw_sssf_config").glob("*.yaml"))

# The graders the shipped roster must hold frozen: the deterministic validators,
# the check manifest and the runner that pins its three-valued result, and every
# agent's prompt surface.
SHIPPED_GRADERS = (
    "docs/validation/check_ci_contract.py",
    "ci/checks.json",
    "tools/ci_gate.py",
    "adws/adw_data/prompt_engineering/builder/system.md",
)


# ── harness ──────────────────────────────────────────────────────────────────

def _owner(name: str):
    """Fetch a permissions-owner symbol, or say plainly that it is absent."""
    fn = getattr(permissions, name, None)
    assert fn is not None, f"the permissions owner exposes no {name}()"
    return fn


class _Console:
    def __init__(self) -> None:
        self.notes: list[str] = []

    def note(self, message: str) -> None:
        self.notes.append(message)


class _Run:
    """The three attributes `permissions` reads off a run."""

    def __init__(self, repo_root: Path, cfg: SSSFConfig) -> None:
        self.repo_root = repo_root
        self.cfg = cfg
        self.console = _Console()


def _cfg(*, frozen=(), protected=("adws/adw_modules/",), data_dir="adws/adw_data"):
    return SSSFConfig(defaults=ConfigDefaults(
        protected_files=list(protected),
        protected_evaluator_paths=list(frozen),
        data_dir=data_dir,
    ))


def _agent(name: str, writes):
    return AgentConfig(name=name, writes=writes,
                       prompt_engineering=PromptEngineering(system="s.md", user="u.md"))


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    for relative, body in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@example", "-c", "user.name=t",
                    "commit", "-qm", "base"], cwd=root, check=True)
    return root


# ── 1. the failing regression is frozen for its generation ───────────────────

def test_bug_fix_agent_is_refused_the_regression_that_grades_it():
    cfg = _cfg(frozen=["tests/test_widget_regression.py"])
    builder = _agent("builder", None)          # unrestricted — the only agent that is

    assert permissions.permitted("tests/test_widget_regression.py", builder, cfg) is False
    # Non-vacuity: the refusal comes from the declaration, not from the path's
    # shape. Undeclare it and the very same write is ordinary work again.
    assert permissions.permitted(
        "tests/test_widget_regression.py", builder, _cfg(frozen=[])) is True


def test_deleting_the_frozen_regression_aborts_even_though_rollback_succeeded(tmp_path):
    """Rollback is defense in depth. It is not what refuses the write."""
    root = _repo(tmp_path, {"tests/test_widget_regression.py": "assert False\n",
                            "app/widget.py": "value = 1\n"})
    run = _Run(root, _cfg(frozen=["tests/test_widget_regression.py"]))
    before = permissions.snapshot(run)
    preserved = permissions.preserve(run, before)

    (root / "tests/test_widget_regression.py").unlink()

    with pytest.raises(permissions.PermissionBreach) as breach:
        permissions.enforce(run, None, _agent("builder", None), before, preserved)
    assert "tests/test_widget_regression.py" in str(breach.value)
    # The rollback did work — and the phase died anyway. One recovered path is
    # inside RECOVERED_LIMIT, so the legacy slip path would have continued.
    assert (root / "tests/test_widget_regression.py").read_text() == "assert False\n"


def test_same_numstat_rewrite_of_dirty_frozen_regression_is_refused(tmp_path):
    root = _repo(tmp_path, {"tests/test_widget_regression.py": "assert False\n"})
    target = root / "tests/test_widget_regression.py"
    target.write_text("assert 0 == 1\n")
    run = _Run(root, _cfg(frozen=["tests/test_widget_regression.py"]))
    before = permissions.snapshot(run)
    preserved = permissions.preserve(run, before)

    target.write_text("assert 1 == 0\n")

    with pytest.raises(permissions.PermissionBreach):
        permissions.enforce(run, None, _agent("builder", None), before, preserved)
    assert target.read_text() == "assert 0 == 1\n"


def test_frozen_snapshot_includes_repository_mode_and_symlink_target(tmp_path):
    root = _repo(tmp_path, {
        "tests/check.py": "assert True\n",
        "tests/a.txt": "same\n",
        "tests/b.txt": "same\n",
        "tests/c.txt": "same\n",
    })
    link = root / "tests/evaluator"
    link.symlink_to("a.txt")
    subprocess.run(["git", "add", "tests/evaluator"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@example", "-c", "user.name=t",
                    "commit", "-qm", "link"], cwd=root, check=True)
    run = _Run(root, _cfg(frozen=["tests/"]))

    (root / "tests/check.py").write_text("assert False\n")
    link.unlink()
    link.symlink_to("b.txt")
    before = permissions.snapshot(run)

    (root / "tests/check.py").chmod(0o755)
    link.unlink()
    link.symlink_to("c.txt")
    after = permissions.snapshot(run)

    assert permissions.changed_paths(before, after) == [
        "tests/check.py", "tests/evaluator"]


def test_an_ordinary_recovered_slip_outside_the_surface_still_continues(tmp_path):
    """The negative half: the frozen surface is what stops being forgiven."""
    root = _repo(tmp_path, {"app/widget.py": "value = 1\n"})
    run = _Run(root, _cfg(frozen=["tests/test_widget_regression.py"]))
    before = permissions.snapshot(run)

    (root / "scratch.txt").write_text("out of scope\n")

    touched = permissions.enforce(run, None, _agent("scout", []), before, {})
    assert touched == []
    assert not (root / "scratch.txt").exists()
    assert run.console.notes, "a forgiven slip is reported, not silent"


# ── 2. an optimizer cannot reach a scorer through a broad grant ──────────────

def test_optimizer_cannot_reach_a_scorer_through_a_broad_prefix():
    cfg = _cfg(frozen=["benchmarks/scorer/"])
    optimizer = _agent("optimizer", ["benchmarks/"])

    assert permissions.permitted("benchmarks/scorer/score.py", optimizer, cfg) is False
    # Non-vacuity: the rest of what it declared is still its to write.
    assert permissions.permitted("benchmarks/run.py", optimizer, cfg) is True
    # And the explicit revision — a declaration scoped INSIDE the surface, which
    # only a roster edit can make — is honoured.
    reviser = _agent("optimizer", ["benchmarks/scorer/score.py"])
    assert permissions.permitted("benchmarks/scorer/score.py", reviser, cfg) is True


# ── 3. an explicit revision creates a new generation ─────────────────────────

def test_revising_a_defective_evaluator_creates_a_generation_and_voids_old_evidence(tmp_path):
    root = _repo(tmp_path, {"docs/validation/check_thing.py": "print('v1')\n",
                            "tests/test_unrelated.py": "assert True\n"})
    cfg = _cfg(frozen=["docs/validation/"])
    run = _Run(root, cfg)
    generation = _owner("evaluator_generation")
    current = _owner("evidence_is_current")

    first = generation(run)
    assert first is not None, "a declared surface that resolves must have an identity"

    # The maker cannot revise it in flight...
    assert permissions.permitted("docs/validation/check_thing.py",
                                 _agent("builder", None), cfg) is False
    # ...only a roster declaration inside the surface can.
    reviser = _agent("builder", ["docs/validation/check_thing.py"])
    assert permissions.permitted("docs/validation/check_thing.py", reviser, cfg) is True

    (root / "docs/validation/check_thing.py").write_text("print('v2')\n")
    second = generation(run)
    assert second is not None and second != first

    assert current(first, run) is False, "evidence bound to the old generation is stale"
    assert current(second, run) is True

    # A file outside the surface does not move the generation — otherwise every
    # commit would invalidate every piece of evidence.
    (root / "tests/test_unrelated.py").write_text("assert 1 == 1\n")
    assert generation(run) == second


def test_untracked_evaluator_revision_creates_a_generation(tmp_path):
    root = _repo(tmp_path, {"docs/validation/check_thing.py": "print('v1')\n"})
    run = _Run(root, _cfg(frozen=["docs/validation/"]))
    generation = _owner("evaluator_generation")
    first = generation(run)

    (root / "docs/validation/check_new.py").write_text("print('new')\n")

    second = generation(run)
    assert first is not None and second is not None and second != first
    assert _owner("evidence_is_current")(first, run) is False


def test_evaluator_declaration_revision_creates_a_generation(tmp_path):
    root = _repo(tmp_path, {"docs/validation/check_thing.py": "print('v1')\n"})
    cfg = _cfg(frozen=["docs/validation/"])
    run = _Run(root, cfg)
    generation = _owner("evaluator_generation")
    first = generation(run)

    cfg.defaults.protected_evaluator_paths = ["docs/validation/check_thing.py"]

    second = generation(run)
    assert first is not None and second is not None and second != first
    assert _owner("evidence_is_current")(first, run) is False


def test_an_unobservable_evaluator_surface_is_could_not_observe(tmp_path):
    """Absent, unresolvable, or unreadable is never a pass."""
    root = _repo(tmp_path, {"app/widget.py": "value = 1\n"})
    generation = _owner("evaluator_generation")
    current = _owner("evidence_is_current")

    assert generation(_Run(root, _cfg(frozen=[]))) is None           # nothing declared
    assert generation(_Run(root, _cfg(frozen=["docs/validation/"]))) is None  # resolves to nothing
    assert generation(_Run(root / "absent", _cfg(frozen=["app/"]))) is None   # no repo to ask
    assert current("whatever", _Run(root, _cfg(frozen=[]))) is None
    assert current(None, _Run(root, _cfg(frozen=["app/"]))) is None   # nothing recorded


def test_an_unreachable_git_never_reads_as_an_intact_surface(tmp_path, monkeypatch):
    """The generation goes could-not-observe; the snapshot still refuses to lie.

    Reporting the surface as unobservable must not buy that by teaching the
    change-set snapshot to return "nothing changed" when git is missing — that
    single answer would make every permission decision in the module vacuous.
    """
    root = _repo(tmp_path, {"docs/validation/check_thing.py": "print('v1')\n"})
    run = _Run(root, _cfg(frozen=["docs/validation/"]))
    assert _owner("evaluator_generation")(run) is not None      # non-vacuity

    monkeypatch.setenv("PATH", str(tmp_path / "empty-path"))
    assert _owner("evaluator_generation")(run) is None
    with pytest.raises(OSError):
        permissions.snapshot(run)


# ── 4. outside the frozen property scope, work stays ordinary ────────────────

def test_an_unrelated_test_file_outside_the_frozen_scope_changes_freely(tmp_path):
    root = _repo(tmp_path, {"tests/test_widget_regression.py": "assert False\n",
                            "tests/test_unrelated.py": "assert True\n"})
    cfg = _cfg(frozen=["tests/test_widget_regression.py"])
    run = _Run(root, cfg)
    builder = _agent("builder", None)

    assert permissions.permitted("tests/test_unrelated.py", builder, cfg) is True

    before = permissions.snapshot(run)
    (root / "tests/test_unrelated.py").write_text("assert 1 == 1\n")
    assert permissions.enforce(run, None, builder, before, {}) == ["tests/test_unrelated.py"]


# ── the precedence boundary: scope narrowed, order untouched ─────────────────

def test_the_session_runtime_grant_is_still_consulted_first():
    """A path that is protected AND frozen is still writable when it is runtime."""
    cfg = _cfg(frozen=["adws/adw_data/"], protected=["adws/adw_data/"])
    runtime = "adws/adw_data/sessions/a1b2c3d4/scout/context_handoff/findings.md"
    for agent in (_agent("scout", []), _agent("reviewer", []), _agent("builder", None)):
        assert permissions.permitted(runtime, agent, cfg) is True


def test_every_agent_no_longer_owns_every_agents_prompt_surface():
    cfg = _cfg(frozen=["adws/adw_data/prompt_engineering/"])
    prompt = "adws/adw_data/prompt_engineering/builder/system.md"
    for agent in (_agent("scout", []), _agent("reviewer", []), _agent("builder", None)):
        assert permissions.permitted(prompt, agent, cfg) is False


# ── the shipped roster ───────────────────────────────────────────────────────

def test_every_shipped_roster_declares_the_frozen_evaluator_surface():
    assert ROSTERS, "no shipped roster found — nothing was observed"
    frozen = _owner("is_frozen_evaluator")
    for roster in ROSTERS:
        cfg = agents.load_config(str(roster))
        assert cfg.defaults.protected_evaluator_paths, \
            f"{roster.name} declares no frozen evaluator surface"
        for grader in SHIPPED_GRADERS:
            assert frozen(grader, cfg), f"{roster.name}: {grader} is not frozen"
        # Property-scoped, never every test file forever: this generation's
        # regression is frozen, and its neighbours are not.
        assert frozen("tests/test_protected_evaluator_surface.py", cfg)
        assert not frozen("tests/test_gate_outcomes.py", cfg)
        assert not frozen("apps/inkwell/src/main.ts", cfg)


def test_the_shipped_roster_refuses_its_graders_to_the_agents_that_could_reach_them():
    cfg = agents.load_config(str(ROOT / "adws/adw_sssf_config/sssf.config.yaml"))
    builder = agents.resolve(cfg, "builder")
    documenter = agents.resolve(cfg, "documenter")

    # The documenter's `docs/` grant used to carry every deterministic validator
    # with it — a documenter that can rewrite the grader is not a documenter.
    assert permissions.permitted("docs/validation/check_ci_contract.py", documenter, cfg) is False
    assert permissions.permitted("docs/reference/FILE_MAP.md", documenter, cfg) is True

    # The builder is unrestricted everywhere except the machinery that grades it,
    # and the manifest/runner pair is one coordinated edit away from vacuous.
    assert permissions.permitted("ci/checks.json", builder, cfg) is False
    assert permissions.permitted("tools/ci_gate.py", builder, cfg) is False
    assert permissions.permitted("docs/validation/check_obs_query.py", builder, cfg) is False
    assert permissions.permitted("apps/inkwell/src/main.ts", builder, cfg) is True


def test_the_repository_surface_resolves_to_real_tracked_files():
    """Non-vacuity: the shipped declaration names paths that actually exist."""
    cfg = agents.load_config(str(ROOT / "adws/adw_sssf_config/sssf.config.yaml"))
    assert _owner("evaluator_generation")(_Run(ROOT, cfg)) is not None
