# SWE-bench Goes Live Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **SWE-bench Goes Live!**
- arXiv: `2505.23419`

The paper is an evaluation/benchmark-construction research source, not a benchmark adoption decision.

## Governing interpretation

Historical replay/regression and fresh generalization answer different questions and must remain distinct proof obligations.

> **Never use the same continuously reused workload both as the thing optimized against and as the sole evidence that optimization generalized.**

## EXPLORE-1 — Dual evaluation lanes

Future SSSF system-generation qualification should distinguish:

- **historical replay/regression:** exact previously proven workloads used to detect lost capability and compare controlled regressions;
- **fresh frontier/generalization:** new work not previously used for tuning, used to support claims that a new harness/model/verifier/tool/routing generation generalizes.

Replay remains valuable after repeated use but becomes weaker evidence of generalization as it is reused for development.

Routing: harness scorecard, replay-corpus design, DSH/AgentBackend/verifier/tool-interface generation promotion.

## EXPLORE-2 — Exact qualification-cohort identity

Every comparative performance claim must bind the exact evaluated cohort and evaluation generation.

Potential identity includes:

- corpus/frontier generation;
- exact episode-set digest;
- inclusion/commissioning policy generation;
- execution-environment generation;
- scorecard/scoring-contract generation;
- relevant workload strata.

Headline percentages without common cohort identity are not comparable evidence.

## EXPLORE-3 — Qualification-episode commissioning

A historical traceable episode does not automatically become a qualification-quality benchmark episode.

Qualification episodes should prove stable and discriminative behavior under an applicable commissioning contract. For defect-repair work this may include, where applicable:

```text
exact baseline
    +
watched-red failure
    +
accepted repair
    +
watched-green result
    +
stable applicable regression obligations
    +
exact environment identity
```

Unstable/flaky episodes should be classified `CNO_FOR_QUALIFICATION` (or exact successor semantics) rather than silently averaged into a deterministic qualification cohort. They may still be retained for robustness research.

## EXPLORE-4 — Historical dependency closure

Replay must bind environment/dependency identity at the exact source snapshot, not merely repository identity.

Preferred authority is exact lock/image/toolchain/dependency digest. If old state must later be reconstructed, reconstruction must not silently resolve dependencies that did not exist at the original source time.

A timestamp-constrained dependency universe may be explored as a fallback for historical reconstruction, but reconstructed environments must be labeled honestly and become CNO where equivalence cannot be established.

Routing: Docker/replay-corpus environment identity.

## EXPLORE-5 — Repository-family novelty as holdout dimension

Freshness is not only chronological.

Future evaluation should distinguish where useful:

- previously seen task versus unseen task;
- familiar repository versus unfamiliar repository;
- familiar subsystem/domain versus transfer setting;
- familiar environment/toolchain versus novel environment.

This is especially relevant to standalone SSSF's claim that the factory can be stamped into repositories beyond SSSF itself.

## EXPLORE-6 — Difficulty-stratified scorecards

Aggregate success rates can hide cohort composition changes. Future scorecards should stratify by workload properties such as:

- expected/actual write scope;
- number of implicated components/files;
- repository size/complexity;
- cross-module dependency;
- novelty;
- execution class;
- semantic-review requirement.

Exact thresholds must be learned from SSSF evidence rather than copied from SWE-bench-Live.

## EXPLORE-7 — Automated unfamiliar-repository environment commissioning

Long-range standalone-SSSF research may evaluate:

```text
unfamiliar repository
      ↓
agent reduces environment-setup uncertainty
      ↓
candidate SandboxSpec/setup/test commands
      ↓
CODE executes and observes
      ↓
VerificationContract qualifies / FAIL / CNO
      ↓
commissioned repository execution profile
```

This is deferred until the core Docker substrate and later execution-cell foundations are proven. It must not complicate near-term SBX-2/3 work.

## Evaluation hierarchy

Future SSSF evidence should conceptually distinguish:

1. **work acceptance** — did this exact candidate satisfy its exact applicable contracts?
2. **historical regression** — can this new system generation preserve known capability on commissioned replay episodes?
3. **fresh generalization** — does it improve on fresh/held-out work?

A moving frontier qualifies system generations; it must not silently redefine ordinary per-work acceptance contracts.

## Non-decisions

This research does **not** authorize:

- adopting SWE-bench-Live as SSSF's acceptance benchmark;
- a new authoritative benchmark database;
- changing near-term Docker/Wayfinder/DSH sequencing;
- automatic unfamiliar-repository environment synthesis now;
- treating a rolling benchmark score as per-PR landing authority.
