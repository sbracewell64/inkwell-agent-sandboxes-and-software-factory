# Roadmap Amendment — Agentic Systems Source Review and Phase-Timed Adoption

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Purpose:** require FirstMate to independently review the current `ombharatiya/ai-system-design-guide` Agentic Systems chapters and use them as a phase-timed architecture reference for SSSF maturation. The guide is a knowledge source, not a runtime dependency, framework mandate, or authority owner.

## Exact upstream reference

Repository: `ombharatiya/ai-system-design-guide`

Reviewed planning source generation: `3d391f62635922923eecf66014522a955cab5236`

Relevant source directory: `07-agentic-systems/`

Required chapter set:

1. `01-agent-fundamentals.md`
2. `02-reasoning-loops-react-and-beyond.md`
3. `03-tool-use-and-mcp.md`
4. `04-multi-agent-orchestration.md`
5. `05-agent-memory-and-state.md`
6. `06-planning-and-decomposition.md`
7. `07-error-handling-and-recovery.md`
8. `08-human-in-the-loop-patterns.md`
9. `09-agentic-security-and-sandboxing.md`
10. `10-evaluating-agentic-systems.md`
11. `11-durable-execution.md`
12. `12-loop-engineering.md`

Before relying on the source for a later implementation decision, FirstMate should reobserve current upstream head and refresh only the chapter(s) material to that decision when upstream has materially changed. Do not repeatedly re-read the entire repository without a reason.

## Governing adoption law

The guide teaches mechanisms and tradeoffs. It does not authorize SSSF to adopt those mechanisms merely because they are common in production agent systems.

For each relevant mechanism, FirstMate must map:

```text
upstream concept
  -> current SSSF / FirstMate owner
  -> actual observed gap or no gap
  -> simpler existing alternative
  -> new complexity / authority / state / failure surface
  -> timing trigger
  -> evidence required
  -> KEEP | ADAPT | DEFER | REJECT | CNO
```

The existing SSSF simplification hierarchy and system-design decision lens dominate. Python ADWs remain the visible deterministic execution graph; agents remain bounded reasoning nodes; one JSONL + SQLite observability spine remains preferred; new schedulers, databases, orchestrators, memory authorities, evaluators, or durable-execution engines must earn their existence.

## Browser Sol review — high-value transferable ideas

The current source review finds the following ideas particularly relevant to SSSF.

### 1. Agent versus workflow distinction

The guide distinguishes fixed workflows from increasingly autonomous agents. SSSF should preserve the stronger local interpretation: if the sequence can be known and checked in advance, encode it in Python/CODE; use agentic reasoning only where intermediate observations genuinely determine the next action.

**Timing:** apply immediately in every ADW/workflow design review.

### 2. Reasoning pattern must match task uncertainty

ReAct-like exploration is appropriate for uncertain environments; plan-and-execute is better when the sequence is sufficiently known; failed local strategies may require re-planning rather than repeating the same repair loop.

**Timing:** evaluate during ADW catalog/orchestrator work and when measured retry/stagnation evidence shows current sequencing is inefficient.

**Do not:** add LangGraph or another graph framework solely because the source describes graph execution.

### 3. High-precision typed tools and narrow capability surfaces

The MCP chapter reinforces strict schemas, explicit tool semantics, least capability, tool discoverability, and standardized interoperability. MCP is useful where it removes bespoke integration, but protocol adoption must not create a second authority/state owner.

**Timing:**
- now: use as a design reference for typed tool/AgentBackend/SandboxProvider seams;
- post-Praxist + CE: use during the separately authorized Browser Sol ↔ FirstMate read-only bridge POC;
- DSH/tool expansion: re-evaluate dynamic tool exposure and MCP compatibility only when a concrete tool-surface problem exists.

**Do not:** adopt A2A, MCP Tasks, remote stateless MCP infrastructure, server cards, or additional gateways merely because they exist.

### 4. Multi-agent only where specialization, independence, or parallelism earns value

The multi-agent chapter reinforces specialization, parallel work, isolation, explicit state ownership, transactional handoffs, and the danger of shared-write conflicts.

**Timing:** use directly in the planned parallel Python ADW investigation and later DSH bounded specialist-cell qualification.

**Local override:** ordinary parallelism remains a Python/SSSF graph capability. No persistent DSH captain is currently admitted. An agent may recommend parallelism; CODE admits, bounds, joins, and verifies it.

### 5. Memory tiering is primarily an ownership/freshness problem

The memory chapter's strongest transferable law is not “install a vector DB.” It is: every retained fact needs a lifetime, source/provenance, freshness contract, trust level, conflict behavior, and promotion/eviction rule. Episodic history must not silently become semantic or procedural authority.

**Timing:**
- immediate planning input to EIL/CRP/OpenViking owner reconciliation;
- before any persistent DSH memory/context feature;
- when repeated evidence shows rediscovery/context burden worth solving.

**Local override:** current authoritative source always outranks historical/retrieved memory; learning promotion must route through existing owners and qualification. Do not add Mem0/Letta/Graphiti/LangMem or another store without a demonstrated non-overlapping need.

### 6. Planning/decomposition requires bounded depth, minimal context, and explicit admission

Recursive decomposition, checkpointed plans, and minimal subagent context are useful principles. The guide's suggested model-authored DAG becomes acceptable only after deterministic SSSF validates the graph/roles/dependencies/bounds before effects.

**Timing:** ADW workflow selection, parallel ADW design, DSH subagent work, and any future decomposition capability.

**Do not:** assume MCTS/tree search or recursive spawning is useful for ordinary engineering tasks. Require measurable benefit first.

### 7. Error results should become structured observations, not hidden logs

Tool/schema/environment/logical-stall failures should return typed observations that permit bounded recovery. Logical repetition should be distinguished from ordinary retry.

**Timing:** review current retry/recovery owners now; implement only identified gaps through normal increments. This is especially relevant to stagnation detection and retry-versus-strategy-reset semantics.

**Local override:** do not rely on a model “reflecting” as the correctness mechanism. CODE owns retry ceilings, applicability, failure classification, and escalation.

### 8. Human-in-the-loop should be reserved for real authority/risk boundaries

Deterministic breakpoints and durable pauses are useful, but Captain involvement should remain sparse and intentional. Existing Captain/Browser-Sol/SELF_HANDLE classification is stronger than generic confidence-based escalation.

**Timing:** use immediately when designing authority gates and future durable pauses.

**Reject by default:** model confidence/logprob thresholds as an authority source; hidden scratchpad/co-reasoning disclosure requirements; artificial human-attention traps. Escalate on typed authority/risk/unknown conditions, not vague confidence.

### 9. Sandbox and capability boundaries dominate prompt-injection defenses

The security chapter strongly reinforces disposable execution, least privilege, no host credential exposure, action-layer capability enforcement, default-deny network egress, and treating skills/config files as executable attack surfaces.

**Timing:** directly applicable to SBX-2..SBX-8 and all later DSH/Praxist/third-party-tool qualification. Revisit whenever installing a skill/plugin/MCP or allowing network/effect capabilities.

**Local preference:** deterministic policy/hook/type enforcement before model-in-the-middle “firewall agents” where code can settle the decision exactly.

### 10. Evaluate trajectories, not only final answers

Agent evaluation should measure task success, path efficiency, action/tool success, tokens/cost, wall time, retries, safety, and failure classes. Shadow/sandbox comparison is directly aligned with REF-1 and Praxist.

**Timing:** incorporate into REF-1 pre-freeze design review and Praxist maturation work before the first reference generation is finalized.

**Local override:** deterministic acceptance remains authoritative. LLM-as-judge is optional semantic evidence and must be calibrated; it does not replace tests, exact-head evidence, maker/checker, or three-valued observation.

### 11. Durable execution is a property set, not a mandate to install Temporal

The durable-execution chapter's valuable distinction is between state checkpointing and a journal that can survive crashes without duplicating side effects. Record nondeterministic results once; use effect identities/idempotency; support durable waits where needed; make restart behavior explicit.

**Timing:**
- now: audit current FirstMate/SSSF side-effect boundaries against these semantics;
- before asynchronous long-running sandbox/DSH workflows or durable human approval waits;
- only consider DBOS/Restate/Temporal/Inngest/Step Functions if current owners demonstrably cannot provide required correctness/recovery without growing worse custom machinery.

**Default:** stay with existing native durable state, typed effect identity, one-use authorization, idempotency, reconciliation, and append-only evidence if sufficient.

### 12. Loop engineering should sharpen existing loops, not multiply them

Highest-value additions from the loop-engineering chapter:

- harness-enforced deterministic termination;
- structural maker/checker separation;
- explicit progress/stagnation detection;
- local retry versus strategy reset;
- fresh context and progressive disclosure;
- large-output offload with references;
- external budget/resource ceilings;
- failure-bucket metrics;
- review-capacity-aware concurrency;
- REF-1/Praxist as the evidence-bearing improvement loop.

**Timing:** immediate ADW/loop architecture review; implement gaps only through bounded increments and measure significant changes longitudinally.

## Phase-timed review matrix

FirstMate should use this timing map as a starting hypothesis and refine it against exact current owners.

| Roadmap point | Chapters to actively reconsider | Primary questions |
|---|---|---|
| Current roadmap/ADW planning | 01, 02, 06, 07, 08, 12 | Is this agentic step necessary? What is the stop predicate? What counts as progress? Retry or re-plan? Who owns escalation? |
| REF-1 design + Praxist operationalization | 10, 12, plus 07 | Are trajectory, failure-bucket, cost/token, latency, intervention, stagnation and reliability metrics sufficient? |
| SBX-2..SBX-8 Docker qualification | 03, 07, 09, 11, 12 | Least privilege, tool contracts, effect idempotency, crash/restart, sandbox/network/credential containment, quiescence |
| Parallel Python ADW | 04, 06, 07, 10, 12 | Decomposability, write isolation, deterministic fan-out/join, aggregate budget, review capacity, measured value |
| CRP / EIL / OpenViking | 03, 05, 07, 10, 11 | Context/memory ownership, freshness, provenance, promotion, poisoning/staleness, projection vs authority |
| Post-Praxist + CE Browser Sol bridge POC | 03, 08, 09, 10, 11 | Read-only MCP/evidence access, transport durability, security, HITL/authority separation, measured communication improvement |
| DSH-0A/0B/1 | 01, 02, 03, 06, 07, 09, 10, 11, 12 | Bounded agent cell, tool surface, termination, recovery, sandbox custody, trajectory evidence |
| DSH parallel/subagent stage if still justified | 04, 05, 06, 07, 09, 10, 11, 12 | Team value, context isolation, lineage, shared-state/write conflicts, cancellation, review bandwidth |
| Any later persistent memory/adaptive orchestration | 04, 05, 06, 10, 11, 12 | Does measured need justify new durable state or adaptation? Can existing owners solve it more simply? |

## Immediate review versus implementation timing

FirstMate should perform the **source/owner review dependency-independently** when practical, because the output is planning knowledge. That does not mean immediate implementation.

Classify each finding into one timing state:

- `ALREADY_SATISFIED` — current accepted owner already proves the property; add nothing.
- `CURRENT_GAP_IMPLEMENT_WHEN_ORDINARY_INCREMENT_PERMITS` — concrete current defect/gap with no missing architectural prerequisite.
- `PHASE_TRIGGERED` — relevant only when a named roadmap phase/capability activates.
- `MEASUREMENT_TRIGGERED` — implement only if REF-1/Praxist/operational evidence shows a limitation.
- `REFERENCE_ONLY` — useful design knowledge, no current implementation need.
- `REJECT_AS_DUPLICATION_OR_NET_COMPLEXITY` — conflicts with simplification/authority or current owners are stronger.
- `CNO` — ownership/value/timing cannot yet be established.

A chapter's existence does not create work. Only a demonstrated gap plus the correct timing state creates an implementation candidate.

## FirstMate required independent review

FirstMate must independently read all 12 chapters at the pinned source generation (or a freshly observed successor if it chooses to update the corpus) and produce a concise owner-reconciliation assessment before treating this source review as settled.

For every chapter, report:

- exact source identity reviewed;
- strongest transferable laws;
- current FirstMate/SSSF owner(s) already satisfying them;
- concrete observed gaps;
- recommendations that should be rejected or modified for SSSF;
- timing classification from the vocabulary above;
- exact roadmap phase/trigger if `PHASE_TRIGGERED`;
- measurable trigger and REF-1/Praxist metric if `MEASUREMENT_TRIGGERED`;
- smallest proposed change if any;
- positive and watched-red fixtures for any future implementation;
- constructs that could be simplified or removed rather than added.

FirstMate should explicitly challenge Browser Sol's dispositions above and may strengthen, narrow, merge, or reject them with evidence.

## Guide-specific recommendations that are not local authority

The source contains numerical/model/framework heuristics and contemporary ecosystem claims. Treat them as references, not SSSF policy. In particular, do not hard-code without local measurement:

- universal iteration/retry/tool-count thresholds;
- confidence/logprob escalation thresholds;
- model-tier examples;
- fixed recursion depth recommendations;
- plan-similarity percentages;
- rate-of-spend thresholds;
- claims that one orchestration framework is dominant;
- claims that a knowledge graph/vector DB is the best memory implementation;
- claims that a stronger LLM is inherently an independent reviewer;
- claims that “correct answer via wrong path” universally means zero value.

Where a principle is valuable, derive SSSF thresholds and acceptance rules from local deterministic contracts and REF-1/Praxist evidence.

## Relationship to existing roadmap laws

This source review is subordinate to:

- `ROADMAP_SYSTEM_DESIGN_DECISION_LENS.md`;
- the SSSF simplification hierarchy;
- REF-1 longitudinal comparison;
- sandboxed Praxist maturation evaluation;
- Python ADW / CODE-owned outer graph law;
- no-current-DSH-captain decision;
- one JSONL + SQLite observability spine;
- existing Seam Contract, maker/checker, three-valued evidence, exact-head, provenance, security, boundedness and LandingAuthorization laws.

It must not create a parallel roadmap, generic agent framework, second state machine, second memory truth store, or another evaluation authority.

## Success condition

This source is being used correctly when FirstMate can say not only **which agentic-system technique might help**, but **why SSSF needs it, which owner should absorb it, when it should be considered, how failure is controlled, and how later evidence will prove whether it was worth the added complexity**.

**Default:** learn broadly, adopt narrowly, time changes to demonstrated need, and preserve the simplest architecture that passes the real evidence.
