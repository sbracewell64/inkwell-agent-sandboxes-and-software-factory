# SDLC-L2 — Property-Scoped Frozen Evaluator Surface

**Status:** IMPLEMENTED, AWAITING REVIEW
**Starts from:** `c192693ec1f09156fd2ce8d1a9e6ce8470e9bd96`

**Authority:** control #36, `STATE: AUTHORIZED_FOR_ROADMAP_INTEGRATION_AND_INCREMENTAL_IMPLEMENTATION`,
`captain_required: false`. The SDLC-L2 law is registered on the canonical
planning branch at `planning/future-sssf@eab880656b4ef00174ea514cca128f6336632fcf`,
`docs/development/ROADMAP.md` — "Evaluator immutability", whose `EXTEND_OWNER`
disposition reads: *"the one new artifact is a list of protected evaluator paths
inside a file that already exists."* Two boundaries from ruling
`34/5429873101` govern the shape of the fix and are carried below.

`SDLC-L2` has no blocking predecessor: `BOUND-1 → SDLC-L2` is `CONSTRAINS_DESIGN`,
which the same document defines as *"`from` dictates a design choice in `to`
without blocking `to`'s start."*

## Problem

`adws/adw_modules/permissions.py` decides what an agent may change. Four of the
five gaps the law names were reproducible at `c192693`, and every one of them
let an agent reach the machinery that decides whether its own work passed.

1. **The regression that grades a generation is not frozen.** `tests/` appears
   in no protected list, so the builder — `writes: None`, the one unrestricted
   agent — could delete or relax the failing test it was asked to make pass.
2. **The deterministic validators are writable by the builder and by the
   documenter.** The documenter's `writes` grant is `docs/`, and
   `docs/validation/check_*.py` sits underneath it. A documenter that can
   rewrite a validator is not a documenter.
3. **The check manifest and its pinning validator are writable by the same
   agent.** `ci/checks.json` and `docs/validation/check_ci_contract.py` were
   both reachable by one agent, so a coordinated two-file edit went uncaught.
4. **Every agent could write every agent's prompt surface.**
   `always_writable()` returned `{data_dir}/` — all of `adws/adw_data/` — and it
   is consulted *first*, ahead of every protection below it. `data_dir` also
   holds the tracked `prompt_engineering/` and `harness_engineering/` surfaces,
   so a `writes: []` read-only agent could rewrite another agent's system
   prompt and `protected_files` was never reached.
5. **The control is post-effect detect-and-rollback rather than pre-effect
   refusal.** `enforce()` forgives up to `RECOVERED_LIMIT = 3` out-of-scope
   writes when the rollback succeeded, which is right for a redirected scratch
   file and wrong for the acceptance surface.

## Desired outcome

The acceptance surface established for a task generation cannot be silently
weakened or rewritten by the maker or the optimizer trying to satisfy it. A
legitimate evaluator change is an explicit revision: it is declared in the
roster — itself a protected file — and it creates a new generation that
invalidates evidence bound to the old one.

## Non-goals

- **No blanket reversal of the legacy precedence.** Ruling `34/5429873101`
  `F6_permissions_precedence`: *"Do not blanket-reverse the legacy precedence
  under this ruling."* The `always_writable`-before-`protected_files` ordering
  is deliberate for session reportability and is unchanged. Only the *scope* of
  the first rule moved, from all of `data_dir` to the `sessions/` runtime it
  always meant.
- **Rollback is not presented as the protection.** Same ruling: *"Post-effect
  snapshot/rollback can remain defense in depth; it is not the load-bearing
  security guard."* `RECOVERED_LIMIT` keeps its existing job for ordinary slips
  and is explicitly no longer available for the frozen surface.
- **No held-out/hidden-benchmark access control.** Preventing an optimizer from
  *reading* a holdout is `AL-1`'s, deferred behind its `SBX-4..6` + `BOUND-1`
  predicate. What is delivered here is the permission refusal on *writing* a
  declared scorer path. No benchmark, holdout or scorer surface is created.
- **No pre-tool projection into the coding harness.** SSSF ships none; that is
  `SDLC-L1`'s `EXTEND_OWNER` row, not this one. The refusal here is the
  permission decision itself, not a harness-side interception.
- **No new framework, no second authority.** The roster/permissions owner is
  extended in place. No validator, no manifest row, no gate runner is added —
  registering a deterministic config eval for this surface belongs to
  `SDLC-L3`, which owns `ci/checks.json`.
- **No roadmap reconciliation.** `docs/development/ROADMAP.md` on `main` carries
  a different item vocabulary from the planning branch and names no `SDLC-L*`
  item. Reconciling the two is its own commissioned work and is not touched
  here.

## Design

**The one new artifact** is `defaults.protected_evaluator_paths`, a list in each
of the five shipped rosters under `adws/adw_sssf_config/`, typed on
`ConfigDefaults`. It defaults to empty in code on purpose: a code default cannot
know which regression grades a generation it has never seen, and a roster that
declares nothing has declared nothing.

It differs from `protected_files` in two ways, and both are the point.

### Surface state law

The declared protected evaluator surface is a CLOSED-WORLD claim, and it is
evaluated at EVERY evaluation point — arm time and post-effect delta evaluation
alike, not admission only. At any evaluation point, a surface that is incomplete
(any enumerated member absent), unresolvable (any exact declaration resolving to
nothing), or visibility-manipulated (assume-unchanged, skip-worktree, or
equivalent index state on a protected member) is could-not-observe, and THAT
phase refuses — including the phase that created the incompleteness.

An authorized revision can never delete a declared evaluator within one phase,
because the roster naming it is itself protected. Removing an evaluator is two
deliberate reviewed acts — first a roster change through the ordinary review
path, then the deletion — never a side effect of a run.

*Property-scoped, never every test file forever.* A path is frozen because it is
named, not because it looks like a test. This generation's regression is frozen;
its neighbours stay ordinary work. The shipped declaration is the durable
grading machinery — `docs/validation/`, `ci/checks.json`, `tools/ci_gate.py`,
`adws/adw_data/prompt_engineering/`, `adws/adw_data/harness_engineering/`,
`tests/fixtures/` — plus the single regression established for this generation,
`tests/test_protected_evaluator_surface.py`.

*A broad `writes` prefix does not unlock one.* "Naming a path is what unlocks a
protected one" still holds, but for the frozen surface the naming has to be an
evaluator revision: `_revises_evaluator()` requires the declaration itself to
match the frozen surface. `docs/` is a decision about documentation that happens
to contain `docs/validation/`; `docs/validation/check_thing.py` is a decision
about the grader. Because the roster is itself in `protected_files`, a
declaration inside the surface can only arrive from outside the run — which is
what makes it explicit.

`permitted()` keeps its original order. Session runtime, then the agent's own
declarations, then `protected_files`, then the frozen surface, then the default.
The frozen check was appended, not inserted ahead of anything.

`always_writable()` now returns `{data_dir}/sessions/`. That is where the
runtime actually lives — `{data_dir}/sessions/{adw_id}/{agent_name}/`, built in
`adw_modules/runner.py` — so every agent still writes its own
`context_handoff/`, envelope, prompts and raw output, and the grant is still
taken from configuration rather than from `.gitignore`.

`evaluator_generation(run)` digests the normalized surface declarations and the
repository-visible identities of tracked and visible untracked members
into one identity, and `evidence_is_current(recorded, run)` compares evidence
against it. Both are three-valued: `None` is could-not-observe and is returned
for a surface that is undeclared, unresolvable, unreadable, or sitting in a tree
git cannot enumerate. An evaluator surface nobody could look at is never
evidence that the evaluator is intact.

Working-tree snapshots apply the same rule: a missing Git executable or a
nonzero Git enumeration result raises a named could-not-observe refusal, so an
unobservable post-agent tree cannot be accepted as unchanged. Each snapshot
also pins the exact commit and tree it armed against; movement of either during
the phase remains permitted when its deltas are in scope, while protected-path
deltas are detected against the pin and an unavailable pin refuses enforcement.

`enforce()` excludes frozen-surface paths from the recovered-slip continuation.
The rollback still runs and still reports — "it was put back" answers the damage
question — but it no longer decides whether the phase survives, and the breach
message names the frozen paths separately.

## Proof

`tests/test_protected_evaluator_surface.py` — 33 cases: the original 12 covering
the law's four required fixtures, boundary controls, and shipped-roster
non-vacuity checks, plus 21 focused review regressions. The original acceptance
cases were observed red against `c192693` before the change, with
the real failure shape (`permitted()` returning `True`, `DID NOT RAISE
PermissionBreach`), and green at the original feature head.

| Required fixture | Case | Red at `c192693` |
|---|---|---|
| bug-fix agent attempting to delete or relax the failing test is refused | `test_bug_fix_agent_is_refused_the_regression_that_grades_it`, `test_deleting_the_frozen_regression_aborts_even_though_rollback_succeeded` | `permitted(...) is True`; `DID NOT RAISE PermissionBreach` |
| an optimizer editing a scorer is refused | `test_optimizer_cannot_reach_a_scorer_through_a_broad_prefix` | `permitted('benchmarks/scorer/score.py', optimizer) is True` |
| a defective evaluator produces an explicit revision, a new generation, and invalidates old evidence | `test_revising_a_defective_evaluator_creates_a_generation_and_voids_old_evidence` | `the permissions owner exposes no evaluator_generation()` |
| an unrelated test file outside the frozen scope still changes freely | `test_an_unrelated_test_file_outside_the_frozen_scope_changes_freely` | green before and after — a property to preserve, controlled below |

Boundary and non-vacuity controls in the same file: the session-runtime grant is
still consulted first and still beats a path that is both protected and frozen;
the prompt surface is no longer blanket-writable; an ordinary recovered slip
outside the surface still continues the run; an undeclared, unresolvable, or
unreachable surface is `could-not-observe`; every shipped roster declares the
surface and freezes the four named graders while leaving
`tests/test_gate_outcomes.py` and app source free.

**Negative controls, run before trusting either preserved property.**

- Over-freeze: adding `tests/` to the shipped declaration turns
  `test_every_shipped_roster_declares_the_frozen_evaluator_surface` red on
  `assert not frozen("tests/test_gate_outcomes.py", cfg)` — the property-scope
  assertion is not vacuous, and the roster was restored.
- Precedence reversal: moving the `protected_files` check ahead of
  `always_writable()` turns `test_the_session_runtime_grant_is_still_consulted_first`
  red on the scout's `context_handoff/findings.md` — the F6 control would
  actually catch the reversal it forbids, and the module was restored.

**Undeclared surface refuses.** `_require_declared_surface()` makes an absent or
empty `defaults.protected_evaluator_paths` a could-not-observe refusal at both
`snapshot()` and `enforce()`, so a freshly installed factory whose roster
declares nothing fails loudly at the phase boundary instead of running
unprotected. An empty declaration is not a small surface — it is no surface, and
every check of it would agree vacuously.
`test_an_undeclared_evaluator_surface_refuses_the_phase` carries it, with the
non-vacuity half proving a declared surface still judges the same phase.

**Red halves, executed rather than intended.** Each guard was reverted in a
throwaway clone at `e6185d53` and its control watched go red, then green again
with the guard restored:

| Guard | Control | Observed red without it |
|---|---|---|
| unobservable git is could-not-observe | `test_corrupt_git_metadata_refuses_an_unobservable_frozen_rewrite` | raises `PermissionBreach` instead of `SnapshotUnobservable` — an observation failure reported as a judgement |
| index-visibility flags refuse | `test_assume_unchanged_frozen_rewrite_is_refused`, `test_skip_worktree_frozen_rewrite_is_refused` | generic `PermissionBreach`, the flag never named |
| declared surface required | `test_an_undeclared_evaluator_surface_refuses_the_phase` | `snapshot()` succeeds, the agent rewrites the grader to `assert False`, and `enforce()` ACCEPTS the phase |
| pinned base identity | `test_committed_ordinary_edit_passes_against_the_pinned_base` | committed in-phase work vanishes from `touched` entirely |

One honest correction to the attribution. The pinned base is **not** what
refuses a committed frozen rewrite: `test_committed_frozen_rewrite_is_refused_against_the_pinned_base`
stays green with the pin removed, because frozen members are enumerated and
digested independently of the diff. That control only goes red when the pin and
the independent enumeration are both removed. The independent enumeration is the
load-bearing guard for that case and the pin is defense in depth behind it; the
pin's own isolating control is the committed-ordinary-edit row above.

Current-head suite and gate totals are intentionally left to the dedicated test
phase that observes them after review fixes. Historical pre-review totals are
not evidence for this head.

## The suite was outside the gate

`ci/checks.json` drove ten validators and never ran `tests/`. That is how this
candidate reached `checks-passed` on a head whose own suite was
`3 failed, 112 passed`: CI was green because CI was not looking. The failures
were found by executing the suite by hand at the pushed head, not by any gate.

`docs/validation/check_repository_test_suite.py` closes it, registered as
`repository-test-suite`. It is three-valued in the shape `tools/ci_gate.py`
owns, because the suite needs dependencies the offline gate deliberately does
not ship: a host that cannot run it reports `could-not-observe` naming the
missing modules, never a FAIL manufactured from a failure to observe. A run
that collects nothing is also `could-not-observe`, so un-collecting the suite
can never be what makes the row green. `.github/workflows/ci.yml` installs the
pinned dependencies so the row actually executes on both matrix legs rather
than reporting could-not-observe forever, which would be the same vacuous
non-answer in a different costume.

All three states were executed, not asserted:

| State | How it was produced | Result |
|---|---|---|
| observed-good | suite green at this head | row `observed-good`, 114 executed, 2 skipped |
| observed-bad | one deliberately failing case added in a throwaway clone | row `observed-bad` naming the failing test, gate exit nonzero |
| could-not-observe | the virtualenv hidden so no interpreter carries the dependencies | row `could-not-observe`, exit 125, naming `pydantic, dotenv` |

Registering a row also required updating `docs/validation/check_ci_contract.py`,
which pins the manifest by exact enumeration. That is the coordinated
manifest-plus-pinning-validator edit this increment's own `Problem` section
names as gap 3 — done here deliberately, by the operator, under explicit
authority, and it is precisely the pair the frozen surface now refuses to an
agent inside a run.

Two skipped cases are `could-not-observe` for their own claims and are counted
as neither pass nor failure: `test_fsmonitor_valid_frozen_rewrite_is_refused`,
because git records no fsmonitor-valid index bit unless `core.fsmonitor` is
configured and asserting a refusal git never performs would be a control that
can only pass vacuously; and one pre-existing skip elsewhere in the suite. The
fsmonitor guard itself stays in place for hosts that do set the bit, and the
`assume-unchanged` and `skip-worktree` cases beside it execute on every host.

## Known unresolved observations

- The shipped rosters declare the surface; the installer template under
  `.claude/skills/sssf/templates/` does not, so a freshly installed factory
  starts with an empty declaration. That template is a different owner and is
  out of this increment's write domain.
- Nothing yet fails CI when a roster declares an empty surface. The deterministic
  config eval that would catch it belongs to `SDLC-L3`, which owns
  `ci/checks.json`.
- Independent qualification of a *new* evaluator generation stays with the
  review owner. What is mechanical here is that the revision is explicit, that
  it produces a new generation identity, and that evidence bound to the previous
  identity reports as not current.
