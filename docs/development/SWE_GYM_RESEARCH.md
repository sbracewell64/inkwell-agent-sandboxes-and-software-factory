# SWE-Gym Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **Training Software Engineering Agents and Verifiers with SWE-Gym**
- arXiv: `2412.21139`

The paper is a research/evaluation source, not a model-training authorization or learned-verifier acceptance decision.

## Governing interpretation

The most useful SSSF lesson is that real software-engineering improvement requires executable, replayable episodes with exact environment/task/trajectory/outcome bindings. Learned verifiers may rank or guide search, but they do not replace SSSF acceptance.

## EXPLORE-1 — SSSF replay corpus

Derive replayable engineering episodes from existing canonical SSSF evidence rather than reconstructing them later.

A replay episode should be able to bind, as applicable:

- exact task/WorkPackage identity;
- exact base source/tree identity;
- Docker/environment/toolchain/runtime identity;
- execution class / AgentBackend / DSH generation;
- model-visible action/observation trajectory refs;
- candidate diff/mutation identity;
- deterministic VerificationContract results;
- semantic review/ruling outcome where applicable;
- resource/time/token/cost telemetry;
- terminal cleanup/quiescence facts;
- resulting accepted source identity where the work landed.

The replay corpus is a derived/indexed research/evaluation view over authoritative SSSF evidence, not a second source of truth.

Use it to compare pre-DSH, DSH-1, DSH-2, DSH-3, models, tool surfaces, and verifier generations on controlled historical workloads while retaining fresh/held-out work for promotion claims.

## EXPLORE-2 — Optimization reward is not acceptance

An inner reward such as tests-passed or a learned probability may guide refinement, candidate generation, or selection. SSSF acceptance remains the conjunction of all applicable deterministic and qualified semantic obligations.

Examples of useful optimization signals:

- deterministic tests passed;
- probability candidate will pass tests;
- progress/localization score;
- semantic-quality score;
- regression-risk score.

None may overwrite deterministic FAIL, narrow CNO to PASS, waive independent review, or mint landing authority.

Routing: `FUT-005` through `FUT-008` and VerificationContract design.

## EXPLORE-3 — Selection regret / oracle gap

Best-of-N evaluation must distinguish discovery from selection.

Measure the gap between:

- whether any candidate in the bounded set is actually acceptable under the evaluation oracle (`Pass@N`-like discovery); and
- whether the current verifier/selector chooses that candidate (`Best@N`-like selection).

A large gap means candidate selection/verifier quality is the bottleneck. A small gap with low discovery means generation/refinement is the bottleneck.

Candidate-count ceilings must therefore be qualified per agent/verifier/task generation using measured marginal return, not fixed globally.

Routing: `FUT-006`, harness scorecard, and `FUT-008` telemetry.

## EXPLORE-4 — Corpora differ by purpose

Do not build one undifferentiated "agent memory" dataset.

Potential projections:

- **policy/agent improvement:** successful, efficient, authority-correct, cleanly terminated trajectories;
- **verifier training/evaluation:** balanced successes, failures, near misses, and diverse agent/model trajectories;
- **safety/anomaly evaluation:** permission denials, stale-state attempts, loops, CNO, timeout/cancellation, cleanup failures, and tool misuse.

Failed/disposable work can remain valuable evidence without becoming canonical project state.

## EXPLORE-5 — Bias-controlled evolution data

Repeated easy tasks can dominate self-generated success corpora. Future DSH self-improvement must use deterministic sampling/weighting controls across task identity/class, difficulty, repository area, execution class, model generation, and failure class.

Exact mechanics remain deferred until real DSH trajectory volume exists.

## EXPLORE-6 — Held-out qualification for learned/self-improved generations

A self-trained or self-evolved candidate generation is never promoted merely because its source trajectories were successful.

Required direction for DSH-8:

```text
incumbent generation
        ↓
proposed candidate generation
        ↓
held-out / fresh evaluation
        ↓
regression + security + evidence + cost comparison
        ↓
independent qualification where required
        ↓
SSSF-owned promotion or rejection
```

Historical replay episodes are useful for regression and development. Promotion claims require fresh or properly held-out work so repeated tuning cannot turn the evaluation set into training data.

This requirement should become part of the DSH-8 Harness Mutation Contract before self-evolution is activated.

## Additional supporting observations

- Keep task/environment/trajectory/outcome separate in evidence.
- Preserve failed trajectories and CNO states where useful for evaluation.
- Measure empty/no-op outputs, loop anomalies, inner turns/tool calls, resources, and accepted-value efficiency rather than final solve rate alone.
- Specialized code-owned workflows remain a strong baseline that DSH autonomy must beat on measured value.
- Trajectory evidence should preserve model-visible inputs/actions/observations and typed tool/effect results; private chain-of-thought is not required as an engineering artifact.

## Non-decisions

This research does **not** authorize:

- model fine-tuning or GPU expenditure;
- a learned verifier as SSSF acceptance authority;
- automatic self-training promotion;
- a new authoritative trajectory database;
- immediate DSH activation;
- state promotion of FUT-005 through FUT-008.
