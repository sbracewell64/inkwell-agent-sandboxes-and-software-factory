# Roadmap Amendment — Sandboxed Praxist Maturation Evaluation

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Purpose:** evaluate whether Praxist can materially strengthen SSSF maturation by improving transparency, controlled feature comparison, longitudinal evidence, variance handling, negative-result retention, and evidence-based promotion decisions without becoming a second SSSF control plane.

This amendment authorizes planning, source/paper research, experiment design, and a future bounded sandbox POC when normal prerequisites are satisfied. It does **not** authorize Praxist as an SSSF runtime dependency, authority owner, scheduler, acceptance mechanism, state store, or canonical observability system.

## Governing architectural boundary

SSSF remains authoritative for software-factory execution and acceptance.

```text
SSSF canonical architecture
    = Python ADWs + CODE-owned transitions + accepted verification/review/landing

Praxist
    = external experimental instrument operating on disposable copies
```

Praxist must not acquire authority over:

- SSSF workflow/ADW selection or phase progression;
- acceptance, promotion, landing, or protected refs;
- maker/checker policy;
- VerificationContracts;
- canonical task/evaluator definitions;
- SSSF JSONL/SQLite truth;
- Docker/SandboxProvider lifecycle authority;
- credentials or canonical host source;
- Browser Sol or Captain authority.

No Praxist result is self-authorizing. Praxist produces experimental evidence. FirstMate interprets that evidence under normal SSSF governance, and ordinary SSSF gates decide whether a candidate feature survives.

## Why Praxist is being considered

Praxist is specifically interesting for properties that complement REF-1 and SSSF maturation:

- preregistered task objectives, metrics, baselines, and evaluation protocols;
- external/task-owned evaluation rather than worker self-assessment;
- exact run artifacts and lineage;
- structured evidence maturity and negative-result retention;
- multi-metric comparison instead of single-score optimization;
- repeated/generational experimentation when justified;
- explicit unknown-usage semantics rather than silently treating missing usage as zero;
- durable experiment records suitable for longitudinal comparison.

The value proposition is **not** to import Praxist's autonomous research control plane into SSSF. The value proposition is to determine whether Praxist can make SSSF feature-admission decisions more transparent, reproducible, and evidence-based.

## Initial question

The first POC should answer:

> **Does sandboxed Praxist produce materially stronger evidence for deciding whether one SSSF feature addition is worthwhile than REF-1 plus the existing FirstMate comparison process alone?**

This is a comparison of evaluation methods, not an assumption that Praxist should become permanent infrastructure.

## Preferred experiment shape

Use an exact frozen REF-1 generation and one isolated candidate SSSF feature.

```text
                  frozen REF-1
                      |
               fixed evaluator
                      |
            +---------+---------+
            |                   |
         ARM A                ARM B
     baseline SSSF       baseline + feature
       exact SHA             exact SHA
            |                   |
            +---------+---------+
                      |
          sandboxed Praxist comparison
                      |
               evidence package
                      |
               FirstMate review
                      |
              normal SSSF governance
```

Praxist and both experimental arms should execute only in disposable sandbox custody. The sandbox must not contain writable canonical SSSF source, host control-plane credentials, Browser Sol authority material, or protected-ref mutation capability.

## Controlled-variable law

For a feature-value experiment, hold comparison-relevant variables constant wherever practical:

- REF-1 task/spec generation;
- starting project commit/tree;
- evaluator/acceptance contract;
- model/provider/profile and reasoning level;
- AgentBackend/runtime generation;
- SandboxProvider/resources;
- tool/capability policy;
- reviewer policy;
- time/token/cost ceilings;
- hardware allocation where material.

The intentional feature difference must be explicit. Any uncontrolled or changed variable is reported as an attribution limitation rather than silently credited to the feature.

## Metrics and transparency

Praxist must not replace existing SSSF telemetry. It should consume or compare evidence derived from accepted owners and may maintain its own task-local experimental artifacts inside its sandbox.

The comparison should expose, when observable:

- acceptance/test/gate/review outcome;
- total and per-phase token usage;
- reported cost;
- wall-clock duration and phase durations;
- agent calls and retries/revisions;
- Captain/Browser-Sol interventions;
- sandbox/process/resource use;
- concurrency where relevant;
- CNO/unknown counts;
- provenance and maker/checker status;
- cancellation/recovery/quiescence;
- exact output/project identity;
- repeated-trial variance where replication is used.

Evidence should remain inspectable as raw/typed records plus concise human-readable projections. Avoid opaque aggregate scores that hide correctness, safety, cost, or autonomy tradeoffs.

## Replication and stochastic variance

For major architectural claims, FirstMate should evaluate whether one A/B execution is statistically or operationally too fragile because of model stochasticity.

Where cost remains bounded, prefer a small replicated design such as multiple baseline and candidate runs under the same frozen protocol. The replication count must be justified by expected variance and experiment cost; it is not fixed globally.

A single unusually good candidate run must not be treated as strong improvement evidence when comparable repeats materially disagree.

## Praxist capabilities to admit progressively

Start with the narrowest useful configuration. Do **not** begin by enabling Praxist's full autonomous-research feature set.

Initial POC should prefer:

- fixed task/evaluator;
- fixed baseline/candidate arms;
- bounded run count;
- explicit metrics;
- durable evidence/provenance;
- read-only/isolated comparison output.

The following are **not assumed necessary** and must independently earn admission if later proposed:

- broad parallel research peers;
- many-generation research campaigns;
- QD;
- DIG;
- Gems;
- dynamic topology;
- persistent research memory;
- adaptive budget expansion;
- standing Praxist monitoring or optimization loops.

If the narrow comparison configuration cannot be achieved without substantial customization or architectural distortion, prefer retaining the simpler REF-1 comparator and borrowing only Praxist evaluation principles.

## FirstMate required assessment

FirstMate should produce a comprehensive plan-only assessment before any Praxist runtime POC. It should:

1. inspect the exact current Praxist source, documentation, license, relevant examples, and arXiv paper;
2. identify the exact upstream commit/release evaluated;
3. map Praxist's ownership model against SSSF owners and identify every possible duplicate authority/state/scheduler/observability seam;
4. determine the smallest safe Praxist configuration capable of baseline-vs-feature comparison;
5. determine whether Praxist can use REF-1 as the task/evaluator truth without redefining it;
6. design sandbox custody, source-copy, credential, network, resource, evidence-harvest, cleanup, and quiescence boundaries;
7. specify exact A/B and repeated-trial experimental contracts;
8. map existing SSSF JSONL/SQLite metrics into the comparison and identify any useful Praxist-only evidence;
9. propose the clearest durable comparison report/visualization for Captain/FirstMate review;
10. evaluate how Praxist can improve longitudinal tracking across successive significant SSSF advancements;
11. identify which Praxist ideas should be copied as principles versus which require Praxist runtime use;
12. estimate recurring operational complexity, runtime, token/cost burden, maintenance burden, and license implications;
13. recommend `USE_SANDBOXED_PRAXIST`, `BORROW_METHODS_ONLY`, or `REJECT_AS_NET_COMPLEXITY`, with evidence;
14. identify the exact normal SSSF increment/prerequisites required before a runtime POC may execute.

FirstMate should explicitly weigh the Captain's objective: **SSSF maturation should become more transparent and evidence-driven, not merely more sophisticated.**

## Transparency objective

If Praxist is retained, its principal success criterion is not autonomous experimentation volume. It is whether the Captain and FirstMate can more clearly answer:

- what changed;
- why it was tested;
- what exact baseline it was compared against;
- which variables were controlled;
- what evidence was produced;
- whether the result replicated;
- what improved and what regressed;
- what evidence is unknown/CNO;
- why the feature was retained, revised, or rejected;
- how the conclusion compares with prior SSSF generations.

Prefer compact longitudinal views over additional orchestration complexity.

## Candidate maturation ledger view

A future read-only projection may summarize significant generations conceptually as:

| SSSF generation | Feature | REF-1 result | Tokens | Wall time | Interventions | Reliability/safety | Conclusion |
|---|---|---|---:|---:|---:|---|---|
| baseline | none | PASS | observed | observed | observed | PASS | BASELINE |
| candidate N | feature X | PASS | delta | delta | delta | PASS/CNO/FAIL | IMPROVED/MIXED/... |

This must be generated from accepted evidence and must not become a competing state owner. Prefer extending an existing report/projection surface over introducing a new ledger/database.

## Kill criteria

Do not retain Praxist merely because the POC runs successfully.

Praxist should survive only if it materially strengthens one or more of:

- experimental rigor;
- repeatability/variance handling;
- causal attribution;
- evidence lineage/provenance;
- negative-result preservation;
- longitudinal transparency;
- comparison clarity;
- evidence-based feature admission;

without an unjustified increase in:

- SSSF architectural complexity;
- authority surface;
- state/scheduler duplication;
- operator concepts;
- credential/network exposure;
- recurring spend;
- benchmark runtime;
- maintenance burden.

If comparable evidence quality can be achieved more simply by extending REF-1/FirstMate deterministic reporting, choose the simpler owner.

## Relationship to REF-1

REF-1 remains the canonical longitudinal workload contract. Praxist does not own or silently mutate it.

Before REF-1's first baseline run, the existing REF-1 design-review obligation may use Praxist research findings as one input when evaluating benchmark methodology. Praxist is not itself required for REF-1 to exist.

After significant SSSF advancements, the default remains REF-1 replay + FirstMate comparison. A Praxist-assisted comparison is justified only where it provides additional evidence value commensurate with its cost/complexity, or where the accepted maturation policy later explicitly promotes it.

## Simplification law

This track is subordinate to the SSSF simplification hierarchy:

> **Every new abstraction must remove more complexity than it adds.**

Praxist may strengthen the measurement of SSSF. It must not become the thing SSSF must understand in order to understand itself.
