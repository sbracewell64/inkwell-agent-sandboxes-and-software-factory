# Roadmap Amendment — Full AI System Design Guide Review for SSSF

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Purpose:** broaden the existing system-design and Agentic Systems source reviews into a full source-level review of folders `01` through `19` in `ombharatiya/ai-system-design-guide`, then require FirstMate to decide which principles are already satisfied, which reveal real SSSF gaps, and when any proposed change should be considered.

The guide is a knowledge source and challenge set. It is not a runtime dependency, framework mandate, model-routing authority, benchmark authority, or automatic backlog generator.

## Exact planning reference

- repository: `ombharatiya/ai-system-design-guide`
- Browser Sol reviewed source generation: `3d391f62635922923eecf66014522a955cab5236`
- tree: `49a44ee7e0d02545b53d21541da22f218b7170ae`
- source scope: tracked human-authored material under `01-foundations/` through `19-multimodal-generation/`
- companion references where materially relevant: `RESEARCH-RADAR.md`, `GLOSSARY.md`, `ai_evals_comprehensive_study_guide.md`, `ai_evals_complete_guide_langwatch_langfuse.md`

The existing `ROADMAP_AGENTIC_SYSTEMS_SOURCE_REVIEW.md` remains the detailed subordinate review for folder `07-agentic-systems/`. Do not delete it or repeat its work unnecessarily; reconcile it into this umbrella review.

Because this is a living guide, model prices, leaderboard scores, framework versions, provider capabilities and other perishable external facts must be refreshed from authoritative current sources before they become decision-critical. Stable principles may be retained when source identity and applicability remain clear.

## Governing law

**Learn primitives; pin frameworks; adopt only measured mechanisms; preserve SSSF as an intelligible Python-owned system.**

For every candidate lesson:

1. identify the concrete problem it addresses;
2. identify the current FirstMate/SSSF owner;
3. determine whether current local semantics are stronger, equivalent, weaker, or merely different;
4. identify the smallest change, if any;
5. identify added state, lifecycle, authority, security, recovery and operator complexity;
6. assign the correct timing trigger;
7. define deterministic qualification and REF-1/Praxist measurement where material;
8. prefer no change when existing owners already satisfy the need.

No framework, database, gateway, vector store, workflow engine, memory platform, optimizer, fine-tuning stack, voice stack, multimodal stack, or monitoring product is authorized merely because the guide discusses it.

## Browser Sol source triage

| Folder | Initial SSSF disposition | Primary use / timing |
|---|---|---|
| `01-foundations` | `REFERENCE_FOUNDATION` | Consult when tokenization, embeddings, attention, context or inference assumptions materially affect a design. No feature by itself. |
| `02-model-landscape` | `ACTIVE_INPUT_WITH_REFRESH` | Model qualification/routing and REF-1 comparisons. Refresh current prices/capabilities; do not chase leaderboards or violate zero-spend policy. |
| `03-training-and-adaptation` | `PHASE_TRIGGERED` | Consider only for later Agent Lightning/local-model experiments after immutable evals and evidence show a real need. No premature fine-tuning/RL. |
| `04-inference-optimization` | `MEASUREMENT_TRIGGERED` | Consider KV/cache/serving/batching/local inference changes only when measured latency, throughput, memory or cost becomes a bottleneck. |
| `05-prompting-and-context` | `ACTIVE_NOW_DESIGN_INPUT` | CRP/EIL/work-packet/context design: smallest high-signal context, JIT retrieval, compaction, structured notes, fresh contexts and prompt-injection boundaries. |
| `06-retrieval-systems` | `PHASE_TRIGGERED` | OpenViking/context retrieval: source identity, chunking, hierarchy, reranking, recall/precision. No vector DB/GraphRAG merely by convention. |
| `07-agentic-systems` | `ACTIVE_SUBREVIEW` | Existing detailed roadmap amendment governs loop, tool, orchestration, recovery, HITL, security, eval and durability review. |
| `08-memory-and-state` | `ACTIVE_PLANNING` | EIL/OpenViking/CRP: memory lifetimes, provenance, freshness, promotion, conflict and poisoning. No second engineering-truth store. |
| `09-frameworks-and-tools` | `REFERENCE_AND_ANTI_CHURN` | Preserve DSH target; learn primitives and pin dependencies. Reject framework churn/golden-hammer adoption unless measured need exists. |
| `10-document-processing` | `PHASE_TRIGGERED_IF_REQUIRED` | Only if SSSF later needs document/image ingestion; deterministic parsing remains preferable where exactness matters. |
| `11-infrastructure-and-mlops` | `ACTIVE_SELECTIVELY` | CI/local infra, resource admission, routing, backpressure, cost-per-task. New gateway/serving platform only after recurring measured need. |
| `12-security-and-access` | `ACTIVE_NOW_AND_EVERY_CAPABILITY_EXPANSION` | Least privilege, capability identity, workspace/tenant isolation, secret boundaries and pre-effect enforcement. |
| `13-reliability-and-safety` | `ACTIVE_NOW_DESIGN_INPUT` | Retry taxonomy, jitter, breakers, bulkheads, layered timeouts, degradation and red-team fixtures through existing owners. |
| `14-evaluation-and-observability` | `HIGHEST_PRIORITY_NOW` | REF-1/Praxist design, benchmark selection, trajectory/reliability metrics, drift and existing JSONL/SQLite observability. |
| `15-ai-design-patterns` | `STANDING_PATTERN_AND_ANTI_PATTERN_LIBRARY` | Use as checklist/challenge material. Patterns are not mandates and anti-pattern labels do not override local evidence. |
| `16-case-studies` | `REFERENCE_AND_CHALLENGE_SET` | Compare SSSF choices against real architecture examples without copying their scale or vendor stack. |
| `17-tool-use-and-computer-agents` | `ACTIVE_PRE_BRIDGE_AND_DSH` | Tool precision, computer-use safety, runtime containment, read-only evidence bridge and DSH tool boundaries. |
| `18-voice-and-audio-agents` | `REFERENCE_ONLY_UNLESS_PRODUCT_REQUIREMENT` | Transfer only generic streaming/latency/observability lessons unless a real SSSF voice requirement emerges. |
| `19-multimodal-generation` | `REFERENCE_ONLY_UNLESS_PRODUCT_REQUIREMENT` | Transfer provenance, async idempotency and stochastic-eval lessons only unless SSSF gains a real multimodal-generation requirement. |

## Cross-cutting findings Browser Sol wants FirstMate to challenge

- **Context is a systems budget, not free capacity.** Prefer JIT retrieval, progressive disclosure, fresh bounded contexts, offloaded large tool output and measured compaction over context stuffing.
- **Harness/scaffold variance is material.** Benchmark/model conclusions must bind exact harness, tools, effort, configuration and environment. Same-harness comparisons are strongly preferred.
- **Evaluation must match production trajectories.** Deterministic end-state correctness dominates; repeated-run reliability, latency, tokens/cost, retries, CNO and intervention burden matter alongside one successful run.
- **Security should move toward containment and capability control rather than faith in prompt-injection detection.** Untrusted content, skills, plugins, repositories and computer-use observations are data, not authority.
- **Reliability is structural.** Retryable/non-retryable classification, idempotency, bounded retries, backpressure, cancellation, quiescence and restart recovery belong in deterministic owners where applicable.
- **Framework churn is a liability.** Retain primitives and narrow interfaces; prefer native SSSF/Python owners to importing LangGraph/CrewAI/LlamaIndex/DSPy/etc. unless a concrete gap earns them.
- **More reasoning/more agents/more context are not automatically better.** Adaptive compute, task-appropriate topology and measured context are preferable to maximum settings.
- **Memory must have provenance, freshness and promotion law.** Historical retrieval cannot outrank current source/evidence truth, and learned procedures require stronger governance than raw episodes.
- **Cost should be measured per accepted task/outcome, not only per token.** The Captain's no-new-spend boundary remains controlling.
- **Observability should extend the existing typed-event -> JSONL + SQLite spine.** External products may supply useful ideas but should not become duplicate truth stores without proven need.

## FirstMate independent review obligation

FirstMate must independently reobserve the upstream repository and exact current FirstMate/SSSF owners. It should:

1. build an inventory of all tracked paths under folders `01` through `19` at the reviewed generation;
2. read all human-authored Markdown/text chapters in that scope, using the existing `07-agentic-systems` review as reusable evidence rather than duplicating it;
3. inspect companion source/primary references when a claim is decision-critical, novel, contested, or materially stale;
4. for every materially relevant chapter or principle map:
   - source path and source generation;
   - principle/mechanism;
   - current FirstMate owner;
   - current SSSF owner;
   - overlap/gap;
   - local semantics `STRONGER | EQUIVALENT | WEAKER | DIFFERENT | CNO`;
   - new complexity and failure surface;
   - `KEEP | ADAPT | MERGE | DEFER | REJECT | CNO`;
   - timing disposition;
   - exact roadmap phase/trigger;
   - qualification fixtures;
   - REF-1/Praxist measurement when material;
   - code/docs/state that could be simplified or removed if a change subsumes an old owner;
5. deduplicate concepts repeated across folders into one canonical local owner rather than producing one SSSF feature per chapter;
6. explicitly record useful ideas that should **not** be implemented because SSSF already has stronger semantics or because the recommendation assumes enterprise/cloud scale SSSF does not have;
7. identify any material gaps that should influence already-planned increments without creating a competing roadmap;
8. keep unrelated implementation-ready roadmap work progressing while this review runs.

## Timing vocabulary

Use one of these dispositions so ideas do not become accidental backlog:

- `ALREADY_SATISFIED`
- `ACTIVE_NOW_DESIGN_INPUT`
- `CURRENT_GAP_EXISTING_INCREMENT`
- `PHASE_TRIGGERED`
- `MEASUREMENT_TRIGGERED`
- `REFERENCE_ONLY`
- `OUT_OF_SCOPE_UNLESS_PRODUCT_REQUIREMENT`
- `REJECT_AS_DUPLICATION_OR_NET_COMPLEXITY`
- `CNO`

A `PHASE_TRIGGERED` finding must name the phase/capability whose activation makes it relevant. A `MEASUREMENT_TRIGGERED` finding must name the metric/threshold or observed limitation that would justify reconsideration. Do not implement either merely because the review is complete.

## Required reconciliation

The review must reconcile with, not duplicate:

- `ROADMAP_SYSTEM_DESIGN_DECISION_LENS.md`;
- `ROADMAP_AGENTIC_SYSTEMS_SOURCE_REVIEW.md`;
- REF-1 and its pre-freeze external benchmark review;
- Praxist maturation evaluation and longitudinal tracking;
- Docker/SBX and BOUND-1;
- Python ADW workflow selection and deterministic fan-out/join;
- DSH qualification while preserving Python as outer graph owner;
- CRP/HQC/EIL;
- OpenViking context/history work;
- Agent Lightning and complexity work;
- transparency/lineage and JSONL/SQLite observability;
- Seam Contract Law;
- Compound Engineering controls and source dossier;
- Browser Sol <-> FirstMate hybrid bridge POC;
- existing security/privacy/cost/maker-checker/exact-head/LandingAuthorization laws.

## REF-1 and Praxist obligation

Before the first REF-1 baseline is frozen, FirstMate should use the guide's evaluation/benchmark material as one input to the already-required external benchmark design review. Public benchmark scores are orientation data, not the REF-1 truth.

After REF-1/Praxist are operational, a significant SSSF change inspired by this corpus should normally become a longitudinal comparison generation when the claimed effect is observable. Compare against the original baseline and immediately previous accepted generation. Negative and no-material-change results are retained.

Useful candidate metrics include task success, repeated-run reliability, first-pass success, wall time, tokens/cost proxy, tool/action failure rate, retries, stagnation, CNO, context burden, review findings, operator interventions, provenance/safety status, resource use and review/integration burden.

## Perishable benchmark/model law

The guide itself warns that benchmark scores are perishable and sensitive to harness/scaffold configuration. Therefore:

- do not compare provider headline numbers from different harnesses as if they were controlled experiments;
- refresh benchmark definitions/current contamination/saturation status before relying on them;
- prefer current contamination-resistant repository/terminal benchmarks when designing REF-1 external comparisons, but do not preselect one solely from this source;
- preserve exact model/provider/harness/config/tool/environment identity for any comparison;
- never allow a benchmark win to override deterministic SSSF acceptance, provenance, security or authority requirements.

## Companion-source posture

`RESEARCH-RADAR.md` is directional. Its research claims should trigger primary-source inspection before system bets. `GLOSSARY.md` is vocabulary, not architecture authority. The two eval deep-dives may inform REF-1/Praxist design without creating a Langfuse/LangWatch/Phoenix dependency. `COURSES.md`, `TRANSITION_GUIDE.md` and folder `00-interview-prep/` are optional supporting references rather than mandatory SSSF architecture corpus.

## Non-authorization

This amendment authorizes **source review, owner reconciliation, timing classification and roadmap planning only**. It does not independently authorize runtime implementation, installation, provider spend, new credentials, external data egress, new framework adoption, fine-tuning, model hosting, new databases, vector stores, gateways, workflow engines, memory products, voice systems, or multimodal-generation systems.

Any implementation must proceed through the already-applicable SSSF/FirstMate roadmap authority and normal engineering gates. New spend, security/privacy weakening, credential/private-data exposure or materially irreversible choices remain Captain-reserved.

## Success condition

The review succeeds if SSSF gains a durable map of **which AI-system-design lessons matter, which are already solved, what evidence would trigger reconsideration, and at what exact roadmap phase each remaining idea belongs**—without turning a broad educational repository into 19 folders of implementation work.
