# HD-09 — Validator Observation Boundary

**Status:** IMPLEMENTED, AWAITING REVIEW
**Starts from:** `991d3a64f1b96a8b9637f97060d692af3518228f`

## Problem

`docs/validation/check_obs_query.py`, registered as
`sqlite-free-observability-validator` in `ci/checks.json`, spawns `just` to
drive the `just obs` integration path. On a host without `just` the spawn
raised an uncaught `FileNotFoundError`, the validator exited 1, and
`tools/ci_gate.py` recorded the row as `observed-bad` — a semantic FAIL
manufactured by a failure to observe.

`tools/ci_gate.py` already classified failure to launch a *top-level* manifest
command as `could-not-observe`. It had no channel for a validator to say the
same thing about its own children, so every child-tool problem inside a
validator was projected as a judgement the validator never made.

## Desired outcome

A verifier that cannot execute its predicate because a required child
dependency is unavailable must not manufacture a FAIL. Observation failure and
predicate failure are distinct. Correctly reclassifying an observation failure
as `could-not-observe` never upgrades the governed property to a pass.

## Non-goals

- No second gate runner and no generic validator framework. The existing
  result owner (`tools/ci_gate.py`) and the existing validators are
  strengthened in place.
- No change to what any predicate asserts. Non-vacuity is preserved: on a host
  that provides `just` and `python`, the observability validator still executes
  the real `just obs` integration path and reports `observed-good`.
- No applicability exemption for any registered check.

## Design

`tools/ci_gate.py` owns the contract:

- `COULD_NOT_OBSERVE_EXIT = 125` — a validator exits with this code when it
  could not execute its predicate.
- `CNO_REASON_PREFIX = "could-not-observe: "` — the reason-line shape
  `docs/validation/check_line_endings.py` already printed. `child_cno_reason()`
  joins those lines into the row's `reason`.

`run_check()` maps exit 125 to the status the result dictionary already
defaults to, `could-not-observe`, and carries the named reasons. Exit 0 stays
`observed-good`; every other nonzero exit stays `observed-bad`.

Each converted validator keeps two lists. An observed defect outranks a failure
to observe: if anything was judged false the validator prints FAIL and exits 1,
listing the unavailable evidence underneath. Only a run that judged nothing
prints CNO and exits 125.

`check_obs_query.py` resolves the integration path's child dependencies by name
before running them — `just`, and the `python` that `just/obs.just` invokes —
so the reason says which tool is missing instead of reading a recipe's exit 127
as a judgement the recipe never made. Child spawns are bounded by
`SSSF_CHILD_TIMEOUT_SECONDS` (default 30) so a wedged tool is a timed-out
observation rather than a validator that never returns.

## Proof

`docs/validation/check_ci_contract.py` gains a watched-red control: a fixture
child that prints a reason line and exits 125 must produce a
`could-not-observe` row carrying its named tool, and the gate must still exit
red. Its existing control that a plain nonzero exit stays `observed-bad` is the
negative half.

`tests/test_validator_observation_boundary.py` drives the real executables:

- `just` absent (empty create-only PATH directory) — validator exits 125, and
  the gate row is `could-not-observe` naming `just`;
- `just` present but hanging — timed-out observation, not FAIL;
- `just` present and answering, contradicting the predicate — still
  `observed-bad`, at the validator and at the gate row, so the boundary cannot
  mask a genuine failure;
- `git` absent — the line-ending and sandbox-source validators report CNO;
- the gate maps exit 0/1/7/125 to observed-good/bad/bad/could-not-observe;
- non-vacuity: with `just` and `python` present the real `just obs` integration
  predicate executes and the validator passes.

Offline gate at this head, on a host without `just`:
`sqlite-free-observability-validator` moved `observed-bad` → `could-not-observe`
(`tool unavailable: just (required by the just obs integration path)`), every
other row unchanged, and the gate conclusion remains `could-not-observe` with a
nonzero exit. On a host with `just` and `python` the same row is
`observed-good`.
