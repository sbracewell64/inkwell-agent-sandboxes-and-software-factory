# HD-03 — Nonvacuous three-valued gate outcome

**Status:** IMPLEMENTED — deterministic controls pass
**Starts from:** `04e5484a6190f033d25e1626b96a4cca93b7f755`
**Boundary:** ADW gate result, phase decision, trace, console, and trace UI

## Intent

Replace vacuous Boolean gate success with one explicit `PASS | FAIL |
COULD_NOT_OBSERVE` (CNO) contract. Every gate declares whether nonempty evidence
is required; an empty required observation or zero discovered gates must not
advance a phase or render green.

## Reproduced defect

At the starting SHA, `GateReport().passed` evaluated true because it returned
`not self.violations`. `artifacts_exist`, `files_non_empty`, `json_parses`, and
`diff_matches_claims` each returned zero checks, zero violations, and Boolean
success for empty declared lists. The empty declaration initiated absent
evidence, `not violations` masked it, and `agents.py` plus `console.py` projected
the result as `gate_pass`/green.

## Design

`adws/adw_modules/data_types.py` owns the canonical typed outcome. CNO requires
closed reason and source enums and refuses Boolean coercion. `GateReport`
requires an explicit `nonempty_required` declaration and derives:

- a failed observed check as `FAIL`;
- qualifying positive observations as `PASS`;
- zero required observations or explicit unavailable evidence as CNO.

`agents.py` synthesizes CNO for zero gates, raised collectors, and legacy or
untyped returns. Only PASS advances. Trace events and SQLite retain the typed
outcome, requirement, checks, and CNO provenance. Console and trace UI render
CNO amber rather than green.

Compatibility is fail-closed. `gate_results.passed` remains only a nullable
projection (`1` PASS, `0` FAIL, `NULL` CNO). Migration preserves legacy Boolean
negative as FAIL but downgrades legacy green to CNO because old vacuous and
nonvacuous positives cannot be distinguished. A trace reader lacking typed
columns also projects CNO rather than falling back to the Boolean.

Installed modules and factory templates carry the same contract. Existing
artifact checks and post-agent permission enforcement retain their bounded
behavior.

## Non-goals

This increment does not reconcile envelope claims with actual Git/path/content
mutations (HD-04), define contribution Git context (HD-05), or change path/diff
semantics. Nonempty declared artifact and permission controls are not presented
as proof of claim completeness.

## Deterministic acceptance

`tests/test_gate_outcomes.py` provides watched-red/three-valued controls for:

- zero required checks and zero discovered gates => CNO;
- an explicit failed check => FAIL;
- a qualifying exact nonempty artifact fixture => PASS;
- malformed, unknown, missing, and duplicate typed outcome refusal;
- raised and legacy/untyped gate results => CNO;
- console CNO output containing no PASS or green check mark;
- SQLite PASS/FAIL/CNO persistence with CNO reason/source;
- legacy green migration to CNO while legacy red remains FAIL.

Validation command:

```text
PYTHONPATH=adws pytest -q tests/test_gate_outcomes.py
```

A disposable watched-red mutation restoring empty-report PASS made the zero-check
control fail with observed `PASS != COULD_NOT_OBSERVE`; the unmodified focused
suite passes 15 tests. Python compile and changed-file Ruff import/name checks,
visualizer typecheck/lint/build, B1 bootstrap validation, strict B3-002 line
endings, B2-002 source-contract validation, and `git diff --check` passed. The
visualizer linter retained four pre-existing warnings outside this change.

Two unrelated host-dependent validators were CNO locally, not treated as pass:
repository ownership could not observe the absent `upstream` remote in this
disposable worktree, and the observability validator could not invoke absent
`just`. The delivery pipeline remains responsible for its configured full
validators in an initialized environment.

## Failure modes and rollback

Malformed typed outcomes are refused; missing evidence is CNO; explicit defects
remain FAIL. CNO exhausts the same bounded correction budget but remains typed
in persistence and rendering. Rollback is one increment commit; old databases
remain readable because the legacy column is retained, although rollback would
restore the known vacuous-success defect.
