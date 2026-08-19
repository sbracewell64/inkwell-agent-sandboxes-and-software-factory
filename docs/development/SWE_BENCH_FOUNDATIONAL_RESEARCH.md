# SWE-bench Foundational Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **SWE-bench: Can Language Models Resolve Real-World GitHub Issues?**
- arXiv: `2310.06770`

The paper is a foundational evaluation-contract research source, not an adoption decision for SWE-bench as SSSF's qualification framework.

## Governing interpretation

A useful software-engineering episode binds intent, exact pre-change state, an observable state transition, and executable evidence. The historical accepted patch is a reference witness, not the only correct answer.

## EXPLORE-1 — Replay episode core

Future SSSF replay/qualification episodes should bind at least:

- authoritative WorkPackage / requirement identity;
- exact baseline repository/commit/tree;
- exact environment/toolchain identity;
- candidate mutation identity;
- applicable executable verification/evidence;
- terminal disposition.

The baseline identity precedes the candidate and is part of episode authority.

Routing: SWE-Gym replay-corpus research, SWE-bench-Live qualification research, harness scorecard.

## EXPLORE-2 — Discriminative versus preservation evidence

Generalize SWE-bench's fail-to-pass / pass-to-pass distinction beyond unit tests.

Potential evidence classes:

- **discriminative/target control:** exact baseline FAIL / candidate PASS where the desired change is observable;
- **preservation/regression control:** baseline PASS / candidate PASS for behavior that must remain intact;
- other negative/positive controls according to the applicable VerificationContract.

Verification evidence should state how the observed property differs between baseline and candidate where that distinction is meaningful.

## EXPLORE-3 — Historical patch is a reference witness

The historical accepted implementation may support provenance, comparison, environment/episode construction and alternative-analysis, but it is not the unique correct answer.

Future candidates are judged against authoritative requirements and applicable evidence, not textual similarity to the prior accepted patch.

## EXPLORE-4 — Episode construction is itself qualified

A historical engineering record does not automatically become a qualification-quality replay episode.

Episode commissioning should establish, as applicable:

- exact baseline reconstructability;
- environment readiness/identity;
- stable discriminative controls;
- stable preservation controls;
- absence of material flakiness or explicit CNO classification;
- bounded hidden evaluation/reference material;
- valid scorecard/evaluation generation.

Failure to reconstruct/qualify honestly yields historical evidence/CNO rather than a misleading benchmark episode.

## EXPLORE-5 — Solver-visible versus hidden evaluation material

Replay episodes must explicitly separate what a solver is allowed to see from hidden evaluation/reference material.

Possible solver-visible material:

- original WorkPackage / requirements;
- exact baseline source;
- qualified environment;
- admissible repository docs/context.

Possible hidden/reference material:

- historical accepted patch;
- historical successful localization;
- hidden discriminative controls;
- prior semantic-review conclusions.

Do not leak historical answer artifacts into replay and then treat the result as genuine localization/engineering capability.

## EXPLORE-6 — Compile episodes at proof time

Prefer deriving replay episode metadata and evidence while SSSF owns exact execution/acceptance state rather than reconstructing it years later from incomplete Git history.

The episode is a derived/indexed projection over authoritative SSSF evidence, not a second source of truth.

## Additional supporting observations

- Context quality dominates context quantity; minimum-sufficient evidence projection remains the preferred DSH direction.
- Context/retrieval/projection policy is part of the qualified execution binding.
- `MUTATION_VALID`, `VERIFIED`, and `ACCEPTED` are distinct states.
- GitHub issue/request text is intent evidence, not necessarily a complete WorkPackage.
- Patch size/minimality is diagnostic evidence, not a correctness oracle.
- Historical verifier/test provenance should be retained where it clarifies what a control proves.

## Non-decisions

This research does **not** authorize:

- adopting SWE-bench as SSSF's production acceptance framework;
- treating all-tests-pass as complete engineering acceptance;
- giving solvers oracle/historical edit locations during capability evaluation;
- requiring future candidates to reproduce historical diffs;
- changing the Docker-first / Wayfinder / DSH roadmap order.
