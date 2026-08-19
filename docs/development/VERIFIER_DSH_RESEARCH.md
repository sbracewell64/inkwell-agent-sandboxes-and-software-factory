# Post-DSH Probabilistic Verifier Research

Status: planning research only. This document preserves a future research source and four promoted `CANDIDATE` mechanisms. None is sequenced or authorized for implementation.

## Preserved upstream source

Repository: `https://github.com/llm-as-a-verifier/llm-as-a-verifier.git`

Observed upstream `main` on 2026-08-18:

`115de305f23ed89bc42e86e010853c40059f3f7d`

Paper: `arXiv:2607.05391`, *LLM-as-a-Verifier*.

Preservation role: future post-DSH research source for probabilistic trajectory scoring, best-of-N selection, progress tracking, criteria decomposition, efficient pairwise tournaments, verifier token accounting, and related evaluation ideas.

The pinned commit preserves what was reviewed. When any candidate below is evaluated for implementation, inspect the then-current upstream separately and record its exact source identity. Repository inclusion here does not imply trust, dependency admission, package installation, or production eligibility.

TurboAgent is also useful as a transparency/research reference, but its transparent inference-proxy architecture is **not** the target SSSF integration shape. SSSF/DSH should expose generation, verification, selection, and refinement as attributable inner execution units rather than hiding them behind a model-compatible proxy.

## Shared architecture law

All candidates in this family are gated behind the DSH execution-cell architecture governed by `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`.

Target placement:

```text
SSSF deterministic outer graph
        -> bounded DSH execution cell
             -> generation / refinement / branching
             -> probabilistic verifier observations
             -> code-owned inner policy chooses next action
        -> proposed result
SSSF deterministic verification / independent review / acceptance
```

The verifier is an inner optimization signal, not an SSSF acceptance oracle.

Three verification classes must remain distinct:

1. **Deterministic verifier** — tests, schemas, Git/source identity checks, deterministic validators. These may contribute directly to acceptance according to their governing contracts.
2. **Independent semantic reviewer** — a separately qualified reviewer/cell where semantic judgment or maker/checker independence is required.
3. **Probabilistic verifier** — LLM-derived scoring/ranking/progress evidence. Advisory optimization evidence only.

Hard precedence:

- a probabilistic score can never convert deterministic `FAIL` to `PASS`;
- a probabilistic score can never narrow `COULD_NOT_OBSERVE` into `PASS` or `FAIL`;
- self-verification by the same model is optimization, not maker/checker independence;
- SSSF retains outer retry, acceptance, commit/promotion, and terminal-state authority;
- code, not the verifier model, owns operational interpretation of scores and thresholds.

Criteria ownership also stays outside the verifier. Authoritative criteria derive from Engineer intent / typed WorkPackage / ExecutionCellRequest. An agent or verifier may propose supplemental criteria, but cannot silently rewrite the acceptance specification.

## FUT-005 — Verifier-guided DSH progress and refinement

State: `CANDIDATE`

### Hypothesis

Fine-grained probabilistic **progress proxies** can improve bounded DSH refinement by helping the inner execution policy distinguish useful progress, stagnation, regression, and likely dead ends without giving the verifier authority over outer acceptance.

A progress proxy is an advisory semantic signal calibrated against real outcomes. It is not authoritative percent-complete state and must never be displayed or consumed as if it were a deterministic completion fact.

### DSH gate

Do not implement before a real bounded DSH execution cell and typed trajectory/evidence stream exist. Production evaluation belongs no earlier than DSH-2 (bounded autonomous refinement). A protocol-only fixture may be designed earlier against DSH-0/DSH-1 mocks, but no product value claim is earned there.

### Candidate shape

```text
trajectory step(s)
    -> probabilistic progress-proxy observation
    -> code-owned policy
         continue | branch | revert | stop-inner-refinement | return-candidate
```

The policy consumes typed score history; the model does not directly decide its own budget extension.

Probabilistic verification is applicability-driven. CODE determines whether a progress proxy is useful for a given execution state; it is not a mandatory stage on every bounded agent call.

### Required evaluation

Compare at least:

- DSH single trajectory baseline;
- ordinary bounded refinement without verifier signal;
- bounded refinement with verifier progress signal.

Measure deterministic final acceptance rate, first-attempt acceptance, outer retries, inner iterations, wall time, generation tokens, verifier tokens/cost, defect rate, independent-review burden, progress-proxy calibration, and whether proxy changes predict actual accepted outcomes. Promote only if the added signal improves actual SSSF outcomes enough to justify compute and machinery.

Evaluation must use exact qualification-cohort identity and include historical replay plus fresh/held-out frontier work before production promotion claims.

### Negative controls

- high score + deterministic failure remains failure;
- low score cannot force an outer retry or reject a deterministically accepted candidate by itself;
- stale/wrong-cell/wrong-candidate score is ignored/refused;
- score unavailability remains `COULD_NOT_OBSERVE` for the verifier signal, not an execution verdict;
- verifier may not extend cell time/token/cost budget;
- rising proxy cannot override information-limited/CNO evidence or justify blind extra inference.

## FUT-006 — Best-of-N DSH candidate selection

State: `CANDIDATE`

### Hypothesis

For selected tasks with meaningful oracle headroom, generating multiple bounded inner candidates and probabilistically ranking them can improve the quality of the one candidate returned to SSSF.

### DSH gate

Requires at least the DSH execution-cell identity/result boundary and candidate-level evidence attribution. Serial best-of-N experimentation belongs after DSH-1/DSH-2 is stable. Parallel candidate generation must wait for DSH-3 subagent/parallel-child qualification and aggregate budget enforcement.

### Candidate shape

```text
outer_attempt = 1
DSH inner candidate A
DSH inner candidate B
DSH inner candidate C
        -> cheap deterministic prefilter
        -> probabilistic ranking / pairwise comparison of survivors
        -> selected inner candidate
        -> deterministic SSSF verification
```

Multiple inner candidates do not become multiple SSSF outer attempts.

Probabilistic Pivot Tournament and similar O(Nk) ranking strategies are implementation options, not SSSF architecture. SSSF should specify a comparison budget/selection contract and keep the ranking algorithm replaceable.

Candidate diversity must be measured explicitly. Distinguish repeated stochastic samples from heterogeneous qualified model/profile/strategy candidates; heterogeneous architecture/profile diversity may provide more oracle headroom per unit cost than additional samples from one identical policy.

### Required evaluation

Compare single trajectory, bounded refinement, and best-of-N under matched or explicitly accounted compute budgets. Measure deterministic acceptance, oracle headroom captured, selection regret/oracle gap, total compute/cost, latency, outer retry reduction, reviewer burden, ranking errors, candidate diversity, and whether simpler refinement achieves the same benefit.

Candidate-count and verifier-comparison ceilings must be qualified per agent/verifier/task/cohort generation using measured marginal return.

### Negative controls

- selected candidate still fails deterministic gates when defective;
- candidate identities and evidence cannot cross-contaminate;
- ranking cannot promote/commit/advance the outer graph;
- aggregate candidate/verifier compute cannot exceed cell ceilings;
- same-model self-ranking is recorded as non-independent;
- candidates failing cheap hard applicable gates are not rescued by probabilistic ranking;
- pairwise ranking is tested for A/B order and position bias, including balanced or reversed presentation controls.

## FUT-007 — Typed criteria decomposition for inner semantic evaluation

State: `CANDIDATE`

### Hypothesis

Mapping typed SSSF work/acceptance dimensions into explicit probabilistic verifier criteria can provide more actionable inner feedback than one undifferentiated quality score.

Illustrative dimensions may include root-cause quality, behavioral correctness, recurrence prevention, scope discipline, evidence-method soundness, and evidence quality, but the actual criteria must come from the authoritative work contract rather than a permanent hard-coded list.

### DSH gate

Requires typed DSH ExecutionCellRequest/WorkPackage semantics and a stable verifier observation contract. Do not implement as a free-standing pre-DSH reviewer layer.

### Architecture constraint

```text
Engineer / WorkPackage / acceptance contract
        -> typed evaluation dimensions
        -> DSH verifier criteria
        -> per-dimension advisory observations
```

Criteria provenance must distinguish:

- **authoritative-derived criterion** — traceable to Engineer intent / WorkPackage / accepted specification; and
- **diagnostic-only criterion** — proposed for uncertainty reduction but non-authoritative unless promoted by the normal specification owner.

The verifier can suggest supplemental diagnostic criteria, but they remain explicitly non-authoritative unless promoted through the normal specification owner.

Probabilistic criteria should target residual semantic uncertainty rather than duplicate cheap deterministic facts. Re-scoring syntax, schema validity, exact source identity, or other already-observed deterministic facts is ineligible by default unless an explicit calibration experiment requires it.

### Required evaluation

Prove that decomposed criteria improve actionable repair/routing decisions relative to a single overall score without increasing false confidence or duplicating deterministic checks. Measure per-dimension calibration, repair localization, total verifier calls/tokens, and downstream deterministic acceptance.

Evaluation must bind exact criteria wording/version/source and the exact trajectory/evidence projection presented to the verifier.

### Negative controls

- omitted authoritative criterion cannot disappear from evaluation silently;
- verifier-generated criterion cannot become acceptance law by itself;
- criterion wording/version/source identity is recorded;
- criteria derived from stale WorkPackage/ExecutionCell identity are refused;
- no probabilistic criterion can override a deterministic contract violation;
- diagnostic-only criteria cannot masquerade as authoritative-derived criteria.

## FUT-008 — Hierarchical probabilistic-verifier evidence and cost telemetry

State: `CANDIDATE`

### Hypothesis

If probabilistic verification is admitted inside DSH, its observations should be first-class attributable evidence with enough identity, lineage, independence, criteria, representation, repetition, ranking, usage, cohort, and budget data to evaluate whether the machinery actually pays for itself.

### DSH gate

Requires the DSH execution-cell evidence model. This is a prerequisite for production use of FUT-005/FUT-006/FUT-007 rather than an optional observability add-on.

### Candidate observation shape

A future typed record should bind at least:

- execution-cell identity;
- outer attempt and inner candidate/trajectory identity;
- verifier implementation/version/source identity;
- verifier model/backend identity;
- effective verifier generation identity including prompt/protocol, scoring granularity, repetition/aggregation, ranking algorithm/policy, and verifier-budget policy;
- maker/verifier independence classification;
- criteria identity/version/source and authoritative-derived vs diagnostic-only provenance;
- exact trajectory/evidence projection generation and digest evaluated by the verifier;
- relevant AgentBackend/agent-interface generation identity where it affects the presented trajectory;
- candidate-pool identity and order/presentation metadata for comparative ranking;
- per-criterion score distribution/aggregate as appropriate;
- repeated-evaluation count and comparison identities;
- generation/verifier/refinement token and cost accounting where observable;
- verifier call/token/cost ceilings and actual consumption;
- cache usage where reported;
- timestamps/ordering needed for progress-proxy observations;
- exact historical replay or fresh-frontier qualification-cohort identity for evaluation records;
- explicit `authority: advisory` / no-acceptance authority.

Hierarchical evidence must distinguish outer attempt, inner iterations, inner candidates, child agents, verifier calls, selection/refinement decisions, and the exact representation each verifier call observed.

### Representation law

> **A verifier score is evidence about the exact representation it evaluated.**

Scores do not transfer by assertion between full trajectories, compressed active-context projections, semantic summaries, or other materially different verifier-input representations.

### Required evaluation

The record must be sufficient to answer empirically whether probabilistic verification improves deterministic acceptance outcomes enough to justify added compute, latency, and complexity. Missing backend usage data must be represented as unobserved rather than zero-cost evidence.

Production qualification of a verifier generation requires both:

- historical replay/regression evaluation on exact commissioned cohorts; and
- fresh/held-out frontier evaluation showing that replay-tuned verifier policy generalizes.

Measure selection regret/oracle gap, position/order bias, criterion calibration, progress-proxy calibration, false-high scores on deterministic or semantic failures, cost/latency, and accepted-value improvement.

### Negative controls

- evidence from another cell/candidate cannot satisfy this one;
- missing usage is not recorded as zero usage;
- self-verification cannot be labeled independent;
- cached and uncached token categories cannot be inferred when the backend did not report them;
- score-only records without provenance/criteria/projection identity are ineligible for governed use;
- verifier evidence cannot itself certify SSSF acceptance;
- scores from one trajectory projection cannot be silently reused for another;
- headline verifier metrics without exact qualification-cohort identity are not comparable evidence;
- verifier configuration changes that alter behavior require a new generation identity and requalification.

## Shared verifier applicability and compute-budget law

Probabilistic verification is a conditional capability, not a mandatory middleware layer.

CODE owns:

- whether probabilistic judgment is applicable to the current cell/state;
- which already-observed deterministic failures prefilter a candidate;
- verifier call/token/cost ceilings;
- repeated-evaluation count;
- ranking/comparison budget;
- whether uncertainty justifies additional verifier compute;
- interpretation of verifier observations into legal refinement/selection transitions.

The verifier may expose uncertainty or disagreement. It may not purchase more compute, enlarge execution authority, extend cell budgets, or make outer retry/acceptance decisions.

Preferred funnel for candidate selection:

```text
bounded candidate set
        ↓
cheap deterministic candidate gates
        ↓
eligible survivors
        ↓
probabilistic semantic ranking if applicable
        ↓
selected candidate(s)
        ↓
real SSSF verification / review / acceptance
```

## Shared promotion boundary

These four candidates may be analyzed and have mock/protocol fixtures designed as DSH architecture matures, but they remain **unsequenced** until their DSH prerequisites exist and are proven.

Before any candidate becomes `DECIDED` or `SEQUENCED`, re-inspect the then-current verifier upstream, the actual qualified DSH implementation, and the latest SSSF evidence/authority model. The implementation proposal must preserve unit-level transparency: generation, verification, selection, refinement, and associated evidence should remain attributable units inside the execution cell.

Promotion must also bind exact replay and fresh-frontier qualification cohorts, exact verifier generation, exact trajectory-projection generation, and relevant AgentBackend/ACI generations. Reused development episodes remain valuable regression evidence but cannot serve as the sole proof that a verifier generation generalized.
