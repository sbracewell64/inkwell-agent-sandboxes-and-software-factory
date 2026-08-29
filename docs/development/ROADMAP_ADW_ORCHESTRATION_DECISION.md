# Roadmap Decision — ADW Selection, Parallel ADWs, and DSH Orchestration Ownership

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Applies to:** post-Docker / pre-DSH SSSF planning, `FUT-001`, `DSH-0A+`, and any future workflow-selection/orchestration owner.

This document is a roadmap planning amendment. It does **not** activate DSH, authorize runtime implementation, bypass any existing prerequisite, or weaken maker/checker, provenance, exact-head, security, cost, boundedness, verification, landing-authorization, or three-valued-evidence requirements.

## Governing baseline invariant

The baseline SSSF architecture remains controlling:

> **Deterministic Python owns the workflow graph. Agents are bounded specialist nodes inside it. Agent proposes; code disposes.**

The existing ADW Python scripts are the reference architecture. They encode explicit sequences such as planner → code transition → builder → deterministic test → reviewer → deterministic acceptance. Python owns sequencing, retries, budgets, applicability, gates, acceptance, and terminal state.

DSH is not presumed to replace this architecture.

## Current architectural decision: no DSH captain

The current SSSF target does **not** include a persistent DSH captain or arbitrary DSH-owned execution topology.

DSH should be treated as an implementation substrate for bounded specialist **AGENT nodes** inside Python-owned ADWs. A future DSH captain/inner coordinator may be reconsidered only under a separate Captain-authorized architecture review after a concrete capability gap is demonstrated that registered Python ADWs plus bounded DSH specialist nodes cannot satisfy adequately.

Until such a later authorization exists:

- no DSH captain is part of the target architecture;
- DSH does not choose, create, advance, or rewrite the outer workflow graph;
- DSH does not own SSSF phase sequencing, retries, budgets, acceptance, or terminal state;
- DSH subagents, where later qualified, remain bounded descendants of a Python-owned agent phase;
- no roadmap item may treat dynamic DSH topology as an assumed destination.

## Architectural question: which orchestrator selects the registered ADW?

SSSF must determine **which orchestration layer should own semantic selection of the registered ADW/Python workflow used for a task**.

The assessment must compare at least these two candidate owners:

### Candidate O — outer orchestrator selection

The outer orchestration/supervision layer (for example FirstMate or the existing operator-facing orchestration owner) classifies the task and recommends/selects a registered SSSF workflow.

```text
Captain intent
    ↓
FirstMate / outer orchestrator
    ↓
typed workflow recommendation
    ↓
SSSF CODE admission
    ↓
registered/versioned Python ADW
    ↓
bounded specialist agent/code phases
```

The outer layer may reason about project context, task class, urgency, dependencies, or supervisory context that legitimately exists outside one SSSF run. It must not thereby acquire authority over the ADW's internal sequencing, retries, gates, acceptance, or terminal state.

### Candidate I — inner SSSF orchestrator selection

The request first crosses the SSSF boundary. A bounded semantic orchestration/classification phase inside SSSF recommends which registered/versioned ADW applies. Deterministic SSSF code validates that recommendation and instantiates the graph.

```text
admitted SSSF request
    ↓
bounded SSSF workflow-classifier/orchestrator
    ↓
typed WorkflowRecommendation
    ↓
SSSF CODE admission
    ↓
registered/versioned Python ADW
    ↓
bounded specialist agent/code phases
```

The inner orchestrator may recommend a workflow but does not execute, mutate, or dynamically redefine the workflow graph.

## Required comparison: outer versus inner selector

FirstMate must critically assess which owner provides the minimum-complexity, minimum-duplication architecture while preserving the baseline SSSF control-plane law.

The comparison must evaluate at least:

- which layer already possesses the semantic context needed to classify tasks;
- whether moving workflow selection inward or outward duplicates an existing planning/orchestration owner;
- whether the selected owner can produce a typed, durable, reconstructable recommendation rather than conversational-only state;
- whether CODE can independently validate the selected workflow ID, applicability, version/generation, required roles, qualified models/backends, sandbox requirements, budgets, maker/checker constraints, and authority before execution begins;
- whether failure, stale state, malformed output, or malicious recommendations fail closed before any unauthorized phase/effect occurs;
- whether selection remains separable from execution so that Python, not the selector, owns the ADW lifecycle;
- whether selection and resulting execution can be represented in the existing JSONL/SQLite trace spine without creating another authoritative state database;
- whether restart/reconciliation can reconstruct which workflow was recommended, admitted, and actually executed;
- whether Captain/FirstMate supervision remains simpler rather than gaining a second competing semantic scheduler.

Preference is not pre-decided between Candidate O and Candidate I. The selected owner must earn the role through lower authority surface, fewer duplicate owners, stronger determinism, and cleaner evidence.

## Registered-workflow rule

Whichever orchestration layer wins the comparison, semantic intelligence selects only from a CODE-owned, registered/versioned workflow catalog or accepted equivalent.

Illustrative workflow families may include plan-only, build-only, plan-build, plan-build-test, plan-build-test-review, simple-SDLC, scout/research, repair, review, and a parallel-capable workflow. These names are examples only and do not register new runtime workflows.

The selection seam should have semantics equivalent to:

```text
request/context
    ↓
semantic recommendation
    ↓
WorkflowRecommendation {
  workflow_id,
  workflow_generation,
  rationale/evidence_refs,
  applicable_task_identity
}
    ↓
CODE validates against registered workflow catalog + policy
    ↓
CODE instantiates the Python-owned graph
```

An intelligent selector may recommend. It may not invent a new executable graph at runtime unless a later, separately authorized architecture proves why that capability is necessary and how CODE compiles and validates it before effect.

## Parallel ADW investigation

FirstMate should investigate whether SSSF should add a **registered Python ADW whose graph contains bounded parallel specialist-agent branches followed by a deterministic join**.

This is a planning and architecture obligation, not authorization to implement immediately. Any implementation still requires the normal named increment/activation, exact candidate, validators, review, proof, and landing path.

The target shape is conceptually:

```text
orchestrator selects registered parallel-capable ADW
    ↓
SSSF CODE admission
    ↓
Python ADW opens bounded fan-out
    ├─ specialist agent A
    ├─ specialist agent B
    └─ specialist agent C
    ↓
Python CODE-owned join
    ↓
deterministic verification / independent review / acceptance
```

Python/SSSF code must own:

- maximum fan-out and total child ceiling;
- which roles may participate;
- dependency edges and start eligibility;
- sandbox/resource/write locks and conflict prevention;
- AgentBackend and SandboxProvider qualifications;
- aggregate time/token/cost/resource ceilings;
- cancellation propagation;
- peer survival rules when one branch fails or is cancelled;
- deterministic result collection and ordering;
- partial-failure/CNO semantics;
- retry eligibility and ceilings;
- maker/checker separation;
- merge/integration sequencing where branches produce changes;
- verification applicability;
- final acceptance and terminal state.

An agent may reason that parallel investigation is useful. It may not acquire spawn/admission, budget, join, acceptance, or landing authority merely by recommending parallelism.

## When the orchestrator should reach for a parallel ADW

FirstMate must define a typed, testable selection policy for when the winning workflow-selector layer may recommend a parallel-capable ADW instead of a serial ADW.

The policy should prefer serial execution by default and recommend parallelism only when the expected benefit is material and the work admits meaningful independent units.

The assessment must cover at least these positive indicators:

1. **Independent semantic work units** — two or more branches can make useful progress without requiring another branch's unfinished result.
2. **Low write-conflict risk** — branches are read-only, operate on disjoint files/surfaces, or have a deterministic integration owner that prevents competing mutation.
3. **Meaningful latency benefit** — parallel execution is expected to reduce critical-path time rather than merely consume more workers.
4. **Reasoning specialization** — distinct specialist roles can investigate materially different dimensions such as security, architecture, implementation, compatibility, or evidence.
5. **Independent evidence value** — multiple observations are useful even if one branch fails or returns CNO.
6. **Capacity is available** — admitted sandbox/worker capacity and aggregate budgets permit fan-out without starving higher-priority or prerequisite work.
7. **Deterministic join exists** — CODE can specify how results are collected, ordered, reconciled, and passed forward before execution begins.

The policy must reject or prefer serial execution when any of these conditions apply materially:

- one branch depends tightly on another branch's semantic output;
- workers would compete for the same mutation surface without a proven isolation/integration contract;
- parallelism would weaken maker/checker independence;
- the same work would simply be duplicated without independent evidentiary value;
- aggregate budgets or sandbox capacity are insufficient or uncertain;
- join semantics require an agent to invent acceptance after seeing results;
- cancellation/quiescence cannot be proven for every branch;
- parallel execution would obscure exact lineage, attribution, or evidence ownership;
- a serial deterministic/code operation is adequate and cheaper/simpler.

The workflow selector may recommend `parallel=true` or a registered parallel workflow only through typed output. CODE independently determines whether the recommendation is admissible under the current policy and capacity state.

## Parallelism qualification requirements

Before a parallel ADW is accepted for production use, qualification should include positive and watched-red controls for at least:

- two genuinely overlapping agent branches;
- one branch failure while an independent peer completes lawfully;
- one branch CNO without false aggregate PASS;
- cancellation of one branch without orphaning peers or descendants;
- global cancellation with complete quiescence;
- deterministic collection independent of completion order;
- conflicting-write proposal refused or isolated before effect;
- capacity exhausted / admission unavailable yields typed hold or CNO rather than oversubscription;
- aggregate budget cannot be enlarged by a worker;
- unregistered role/child request is refused;
- maker cannot become its own required checker through fan-out;
- SQLite/JSONL lineage reconstructs parent, children, timings, budgets, outcomes, and join result.

Parallelism is therefore an **SSSF graph capability**, not a DSH-captain capability.

## DSH default architecture

DSH should be treated primarily as an implementation substrate for bounded **AGENT nodes** inside the selected Python ADW.

Example:

```text
Python ADW

DSH planner cell
    ↓ CODE
DSH builder cell
    ↓ CODE
deterministic tests
    ↓ CODE
DSH reviewer cell
    ↓ CODE
deterministic acceptance
```

A future parallel ADW may contain multiple bounded DSH specialist cells, but Python owns their admission, fan-out, join, budgets, cancellation, and result folding.

## DSH captain reconsideration boundary

A persistent DSH captain is rejected from the current target architecture.

Reconsideration requires a **new Captain authorization** and a concrete demonstrated capability gap. A future proposal must answer:

> **What concrete capability or measurable factory value is lost if SSSF uses registered serial/parallel Python ADWs plus bounded DSH specialist nodes without a persistent DSH captain?**

If registered Python ADWs plus bounded specialist DSH nodes can satisfy the use case adequately, complexity does not earn admission.

## Required negative control

For every intelligent workflow-selection decision, qualification must answer:

> **If this agent returns adversarial, stale, malformed, or nonsensical output, can SSSF cross any execution boundary that deterministic CODE did not independently authorize?**

Any `yes` is a design failure.

Representative watched-reds include attempted workflow substitution, unregistered workflow ID, stale workflow generation, omitted required test/review phase, unauthorized model/role/capability, widened budget, changed acceptance obligation, CNO-to-PASS coercion, unauthorized fan-out, unregistered child role, and direct promotion/landing claims.

## Observability and SQLite continuity

This decision preserves the baseline trace architecture.

Relevant workflow-selection, parallel-branch, and DSH events join the existing SSSF execution evidence spine:

```text
typed producer events
    ↓
raw durable JSONL/history
    +
existing SQLite query projection (`sssf.db`)
    ↓
UI / observability / reconstruction
```

Do not create a second authoritative DSH, parallelism, or workflow-selection database.

The trace should be able to reconstruct at least:

- request/task identity;
- selector owner (outer or inner);
- recommended workflow ID/generation;
- deterministic admission/refusal result;
- actual instantiated ADW identity;
- each Python phase and CODE transition;
- fan-out group identity where used;
- each child branch/DSH cell/inner-unit lineage;
- branch start/end timing and outcome;
- aggregate and per-branch budgets/capability/effect policy identities;
- deterministic join identity/result;
- verification/review/acceptance outcomes;
- cleanup/quiescence and terminal disposition.

SQLite remains the live queryable projection of SSSF execution evidence; raw durable history remains distinct from the query projection and from model-visible context.

## FirstMate required architecture report

Before DSH architecture is considered settled, FirstMate should produce a plan-only report that:

1. inventories the existing baseline ADW Python scripts and their encoded agent/code sequences;
2. maps the current outer and inner orchestration owners and identifies their existing responsibilities;
3. compares Candidate O versus Candidate I for registered ADW selection;
4. recommends the minimum-complexity owner and explains why the other placement is inferior or redundant;
5. evaluates bounded DSH specialist-only execution as the default;
6. designs or recommends the minimum useful registered parallel-capable ADW shape without implementing it prematurely;
7. defines a typed orchestrator selection policy for when parallel ADW execution is justified versus serial execution;
8. specifies fan-out/join, conflict, capacity, budget, cancellation, CNO, maker/checker, and quiescence controls;
9. specifies typed selection/admission contracts and watched-red negative controls;
10. specifies JSONL/SQLite trace integration without a second state owner;
11. identifies any amendments required to `FUT-001`, the DSH implementation plan, ADRs, validators, or workflow catalog before implementation.

No DSH-captain proof is required under the current architecture because DSH captain is not admitted. If a future capability gap motivates reconsideration, that is a new planning decision requiring Captain authorization.

## Roadmap effect

This amendment changes architectural evaluation, not the existing commissioning order.

The current hard chain remains:

```text
Docker commissioning
→ real Docker-backed baseline PR
→ immutable post-Docker/pre-DSH baseline
→ existing Wayfinder technical gate
→ DSH qualification
```

No Docker, Wayfinder, DSH, maker/checker, provenance, security, cost, exact-head, acceptance, or LandingAuthorization gate is bypassed.

Before DSH progresses beyond deterministic protocol/bounded specialist-cell stages, the outer-vs-inner ADW selection owner and registered-workflow admission model must be resolved and recorded. Parallel ADW work may be researched/planned dependency-independently, but production activation requires its own ordinary increment and proof.

**Default if unresolved:** retain baseline SSSF — registered Python ADWs connecting bounded specialized agents through CODE-owned seams, with serial execution unless a registered parallel ADW is explicitly admitted by deterministic policy.