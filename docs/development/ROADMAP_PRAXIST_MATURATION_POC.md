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

## Standing roadmap-governance rule

Praxist consideration is now a standing part of SSSF roadmap work.

Whenever FirstMate performs material roadmap planning, evaluates a Captain-approved new idea, or closes a significant roadmap phase/increment, FirstMate must explicitly consider whether a Praxist-assisted experiment or Praxist-derived evaluation method would materially strengthen the evidence for the next decision.

This obligation is a **consideration step**, not a requirement to run Praxist every time. The default question is:

> **Would a bounded Praxist-backed comparison materially improve transparency, causal attribution, repeatability, negative-result preservation, or evidence quality for this roadmap decision beyond ordinary REF-1 + existing SSSF evidence?**

FirstMate should record one of these dispositions in the relevant roadmap/phase/decision evidence when the question is material:

- `PRAXIST_USEFUL_NOW` — a bounded Praxist experiment is justified and should be planned/executed when prerequisites permit;
- `PRAXIST_METHODS_ONLY` — borrow/elevate specific Praxist evaluation principles, but running Praxist would add unnecessary machinery;
- `PRAXIST_NOT_NEEDED` — existing REF-1/SSSF evidence is already sufficient and simpler;
- `PRAXIST_CNO` — the value of Praxist cannot yet be determined from available evidence.

The disposition must be concise and evidence-linked; do not create a separate bureaucracy or mandatory report for trivial roadmap edits.

### Trigger A — Captain-approved idea enters the roadmap

When the Captain approves a material new SSSF feature, architectural experiment, optimizer, orchestration change, runtime/provider change, memory/context change, parallelism change, verification/review change, or other capability intended to improve the factory, FirstMate should consider whether Praxist can help test the feature against the accepted baseline before the feature is treated as valuable.

Preferred experimental framing where appropriate:

```text
accepted baseline generation
        vs
same baseline + one approved feature difference
        ↓
frozen REF-1 / fixed evaluator / controlled material variables
        ↓
Praxist-assisted repeated comparison if it adds evidence value
        ↓
FirstMate interpretation
        ↓
normal SSSF governance
```

Praxist must never become the reason an idea is authorized. Captain/Browser Sol/normal planning authority decides whether the experiment is allowed; Praxist may only strengthen the evidence about whether the idea is worth retaining.

### Trigger B — significant roadmap phase/increment completes

At completion of a significant accepted SSSF roadmap phase/increment, FirstMate should consider Praxist as part of the post-phase evidence review.

Where REF-1 replay is already required, FirstMate should ask whether Praxist adds useful replication, variance handling, attribution, negative-result retention, or multi-metric analysis beyond the standard replay. If yes, use the narrowest Praxist configuration that provides that value. If no, record `PRAXIST_NOT_NEEDED` or `PRAXIST_METHODS_ONLY` and keep the simpler path.

The phase cannot receive stronger improvement credit merely because Praxist was used. Praxist evidence supplements; it does not replace the phase's own gates, REF-1 comparison, exact-head proof, maker/checker, provenance, quiescence, or acceptance requirements.

### Trigger C — material roadmap review or reprioritization

When FirstMate reviews the roadmap holistically, it should use the longitudinal evidence accumulated so far to identify:

- features that produced repeatable improvement;
- features that produced mixed or workload-specific value;
- features that increased complexity without sufficient value;
- prior negative experiments that should prevent repeated investment;
- metrics whose trends suggest a new hypothesis worth testing;
- evidence gaps where a Praxist experiment could reduce uncertainty.

This is evidence-guided prioritization, not autonomous roadmap authority. FirstMate may recommend; existing authority owners decide activation and material architecture changes.

## Longitudinal maturation tracking — Captain authorized

The longitudinal tracking concept is explicitly authorized as a durable transparency objective for SSSF maturation.

The preferred form is a **read-only projection over accepted evidence**, not a new canonical database, ledger owner, scheduler, or state machine.

For every significant accepted SSSF generation after REF-1 exists, preserve enough evidence to reconstruct a row such as:

| SSSF generation | Change tested | Exact baseline | REF-1 | Tokens | Wall time | Agent calls/retries | Human interventions | Reliability/safety | Praxist disposition | Conclusion |
|---|---|---|---|---:|---:|---:|---:|---|---|---|
| baseline | none | — | PASS | observed | observed | observed | observed | PASS | baseline | BASELINE |
| candidate N | feature X | baseline SHA | PASS | delta | delta | delta | delta | PASS/CNO/FAIL | useful/methods/not-needed/CNO | IMPROVED/MIXED/REGRESSED/... |

Where comparable and useful, the projection should also surface:

- exact SSSF commit/tree;
- exact ADW/workflow identity;
- exact model/runtime/config generations;
- sandbox/resource/concurrency facts;
- review/gate findings;
- CNO counts;
- provenance/maker-checker status;
- cleanup/quiescence;
- repeated-trial variance;
- evidence links and Praxist run identity when Praxist was used;
- the specific reason a feature was retained, revised, deferred, or rejected.

The longitudinal record should make it easy for the Captain and FirstMate to answer:

> **What has actually made SSSF better over time, what did it cost, what tradeoffs appeared, and what evidence supports that conclusion?**

Do not collapse the history into one opaque score. Correctness, safety, autonomy, cost, latency, complexity, and reliability remain visible dimensions.

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
14. identify the exact normal SSSF increment/prerequisites required before a runtime POC may execute;
15. define how the standing roadmap-governance triggers above will be surfaced in ordinary FirstMate roadmap work without adding a second scheduler or state machine;
16. define the smallest read-only longitudinal projection that makes historical SSSF improvements/regressions transparent and evidence-linked.

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

After significant SSSF advancements, REF-1 replay + FirstMate comparison remains mandatory under the REF-1 amendment. At each such checkpoint, FirstMate additionally evaluates the standing Praxist disposition above. Praxist use is required only when the evidence shows that it adds material value commensurate with cost/complexity or when a later accepted maturation policy explicitly promotes it.

## Simplification law

This track is subordinate to the SSSF simplification hierarchy:

> **Every new abstraction must remove more complexity than it adds.**

Praxist may strengthen the measurement of SSSF. It must not become the thing SSSF must understand in order to understand itself.
