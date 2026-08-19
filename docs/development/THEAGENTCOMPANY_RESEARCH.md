# TheAgentCompany Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks**
- arXiv: `2412.14161`

The benchmark is a whole-agent/workflow evaluation research source, not an authorization to adopt TheAgentCompany or build a simulated corporate environment.

## Governing interpretation

Mature SSSF qualification needs a proof level above isolated coding/replay tasks: whole-system missions that carry real engineering intent across actual SSSF boundaries while preserving authority, evidence, state, and the Captain-minimization objective.

> **A good DSH cell is not enough; the whole control plane must prove that it can carry intent to accepted engineering state without losing authority, evidence, or durable workflow state.**

## EXPLORE-1 — Whole-system mission qualification

Add a conceptual qualification level above exact work acceptance, historical replay/regression, and fresh-frontier generalization.

A system mission should exercise realistic end-to-end engineering flow across actual SSSF/control-plane seams, for example Wayfinder/FirstMate, GitHub/control issues, SSSF/Docker/DSH, CI, Browser Sol, landing, exact-main proof, and cleanup.

Do not build a synthetic software company merely to obtain cross-tool tasks.

## EXPLORE-2 — Mission checkpoints are diagnostic, not acceptance authority

Represent long-horizon missions with typed checkpoints so failures can be localized to system boundaries.

Examples include intent compiled, work admitted, sandbox created, candidate produced, deterministic verification passed, independent review complete, landing authorized, exact-main proven, and cleanup/quiescence proven.

Partial checkpoint completion may support research/diagnostic scoring but never converts an incomplete mission into accepted engineering state.

## EXPLORE-3 — Prefer resulting-state contracts over choreography

System-level evaluators should inspect the durable state that must become true rather than requiring a specific sequence of tool calls, clicks, or conversational actions unless the process itself is an explicit requirement.

This keeps mission qualification implementation-independent and allows future generations to discover better paths to the same governed result.

## EXPLORE-4 — Target state plus invariants / negative controls

Mission contracts should include both desired resulting state and invariants/forbidden shortcuts so agents cannot satisfy a weak evaluator by changing the problem.

Potential controls include:

- correct authority owner/ruling provenance;
- exact-head/current-state requirements;
- evidence not rewritten or destroyed;
- independent review not bypassed;
- Captain not used as routine message transport;
- failing tests/validators not disabled merely to obtain green state.

This supports explicit goal-substitution/evaluator-gaming negative controls.

## EXPLORE-5 — Long-horizon reliability is a distinct scorecard dimension

Measure mission completion reliability as dependent state-transition count grows.

Useful strata may include WorkNodes, outer state transitions, model assignments, external-effect boundaries, CI/review cycles, control-plane round trips, and total wall time/cost.

The goal is to detect compounding brittleness that isolated task metrics can hide.

## EXPLORE-6 — Authority-routing missions

Whole-system qualification should deliberately exercise routing among:

- `SELF_HANDLE` for routine resolvable work;
- `BROWSER_SOL` for delegated material engineering judgment;
- `CAPTAIN` only for reserved authority;
- `EXTERNAL_DEPENDENCY` for provider/quota/outage/waiting conditions.

Mission success includes routing the decision to the correct authority and refusing unnecessary Captain escalation.

## EXPLORE-7 — Captain-intervention leakage is system-level evidence

For ordinary delegated engineering missions, measure Captain interventions required for message transport, routine CI inspection, repeated rulings, or other avoidable supervisory work.

A mission that technically reaches the final code state through avoidable Captain transport is not equivalent to an unattended mission.

This supports an operator-value metric such as Captain interventions per accepted increment, stratified by legitimate-vs-avoidable cause.

## EXPLORE-8 — Small high-value mission suite

Do not build a large synthetic benchmark. Prefer a small, deeply qualified suite covering the highest-value system paths and failure modes, such as:

- ordinary PR happy path;
- deterministic verifier failure plus repair;
- independent-review rejection plus revision;
- Browser Sol escalation and ruling return;
- stale-head invalidation;
- external dependency deferral/reconciliation;
- parallel worker failure with peer survival;
- interrupted Docker reconciliation;
- genuine Captain-required decision;
- fully unattended ordinary landing.

## EXPLORE-9 — Capture mission episodes from real proven work

Where possible, compile system-level replay/qualification missions from real `PROVEN` workflows while exact state, authority, evidence, and environment identities are still known.

Preserve solver-visible inputs separately from hidden historical/reference evidence to avoid answer leakage.

## EXPLORE-10 — Incomplete-information missions

Not every mission should begin with a perfectly specified WorkPackage. Include qualification cases where FirstMate must discover repository facts, distinguish observation from inference, resolve non-authority ambiguity itself, and route only genuinely delegated decisions.

This better represents real engineering intake than fully precompiled tasks alone.

## EXPLORE-11 — Goal substitution / evaluator gaming as a failure class

A system may appear to satisfy a metric by changing the problem rather than solving it.

Examples include disabling a failing test, weakening acceptance, renaming state to appear successful, changing fixtures to match output, skipping a required verifier, changing the baseline, or destroying failure evidence.

Mission qualification should deliberately probe such shortcuts with negative controls.

## Additional supporting observations

- Prefer machine-native/API capability over human GUI/browser control when both can represent the same engineering operation faithfully.
- Browser/UI interaction remains useful where no better interface exists or the UI itself is under test, but should not become default transport merely to emulate a human worker.
- Deterministic evaluators should precede probabilistic/semantic evaluation wherever the target property is mechanically observable.
- Cross-tool mission checkpoints can help identify control-plane bottlenecks that aggregate completion scores would hide.

## Non-decisions

This research does **not** authorize:

- adopting TheAgentCompany as an external qualification dependency;
- building a simulated corporate environment;
- expanding SSSF into general digital-office automation;
- treating partial progress as acceptance;
- using GUI/browser interaction when a simpler qualified machine-native interface exists;
- changing the Docker-first / Wayfinder / DSH roadmap order;
- promoting any FUT state.
