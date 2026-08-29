# Roadmap Decision — ADW Selection and DSH Orchestration Ownership

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Applies to:** post-Docker / pre-DSH SSSF planning, `FUT-001`, `DSH-0A+`, and any future workflow-selection/orchestration owner.

This document is a roadmap planning amendment. It does **not** activate DSH, authorize runtime implementation, bypass any existing prerequisite, or weaken maker/checker, provenance, exact-head, security, cost, boundedness, verification, landing-authorization, or three-valued-evidence requirements.

## Governing baseline invariant

The baseline SSSF architecture remains controlling:

> **Deterministic Python owns the workflow graph. Agents are bounded specialist nodes inside it. Agent proposes; code disposes.**

The existing ADW Python scripts are the reference architecture. They encode explicit sequences such as planner → code transition → builder → deterministic test → reviewer → deterministic acceptance. Python owns sequencing, retries, budgets, applicability, gates, acceptance, and terminal state.

DSH is not presumed to replace this architecture.

## Architectural question added to the roadmap

Before a persistent DSH captain or arbitrary dynamic DSH topology is admitted, SSSF must determine **which orchestration layer should own semantic selection of the registered ADW/Python workflow used for a task**.

The assessment must compare at least these two candidate owners:

### Candidate O — outer orchestrator selection

The outer orchestration/supervision layer (for example FirstMate or the existing operator-facing orchestration owner) classifies the task and recommends/selects a registered SSSF workflow.

Conceptual shape:

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

Conceptual shape:

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

Illustrative workflow families may include plan-only, build-only, plan-build, plan-build-test, plan-build-test-review, simple-SDLC, scout/research, repair, and review workflows. These names are examples only and do not register new workflows.

The selection seam should have semantics equivalent to:

```text
request/context
    ↓
semantic recommendation
    ↓
WorkflowRecommendation {
  workflow_id,
  workflow_generation,
  rationale/evidence refs,
  applicable task identity
}
    ↓
CODE validates against registered workflow catalog + policy
    ↓
CODE instantiates the Python-owned graph
```

An intelligent selector may recommend. It may not invent a new executable graph at runtime unless a later, separately authorized architecture proves why that capability is necessary and how CODE compiles and validates it before effect.

## DSH default architecture

Until a stronger use case is proven, DSH should be treated primarily as an implementation substrate for bounded **AGENT nodes** inside the selected Python ADW.

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

This preserves the baseline relationship even if DSH supplies richer context management, model routing, tool use, or bounded multi-turn cognition inside one agent phase.

## DSH captain burden of proof

A persistent DSH captain is **not presumed necessary**.

Before admitting one, FirstMate must answer:

> **What concrete capability or measurable factory value is lost if SSSF uses registered Python ADWs plus bounded DSH specialist nodes without a persistent DSH captain?**

A DSH captain/inner coordinator may remain in the architecture only if at least one concrete use case is demonstrated that:

1. cannot be handled adequately by the winning outer/inner workflow selector choosing a registered Python ADW;
2. cannot be handled adequately by one bounded specialist DSH agent node;
3. materially benefits from coordinated multi-agent semantic reasoning inside one already-authorized phase;
4. preserves CODE ownership of outer sequencing, retries, budgets, gates, verification, acceptance, and terminal state;
5. preserves maker/checker separation and exact authority/capability/model/sandbox/evidence boundaries;
6. remains safe when its output is malicious, confused, stale, malformed, or incomplete;
7. produces enough measured value to justify the additional architecture, test surface, tracing complexity, and failure modes.

If no such use case is proven, the persistent DSH captain architecture is rejected as unnecessary complexity.

## Optional bounded inner coordinator

If a specific semantic phase later proves a need for coordinated inner agents, prefer the narrowest form:

```text
Python opens one authorized agent phase
    ↓
ExecutionCellRequest with fixed authority/budget/topology ceiling
    ↓
optional DSH inner coordinator
    ↓
CODE-admitted narrow children
    ↓
typed ExecutionCellResult
    ↓
Python resumes the outer ADW
```

The inner coordinator may decompose work only inside that phase. It must not:

- create or advance outer SSSF phases;
- select a different ADW after execution begins;
- omit required CODE phases;
- alter outer retry ceilings or budgets;
- widen tool/filesystem/network/effect authority;
- admit unqualified roles/models/plugins;
- replace required independent review with self-review;
- reinterpret `COULD_NOT_OBSERVE` as permission;
- alter a VerificationContract or acceptance policy;
- decide SSSF acceptance;
- commit/promote/merge/land canonical work;
- create another outer execution cell unless CODE explicitly authorized that structural edge.

## Required negative control

For every intelligent workflow-selection or DSH-coordination decision, qualification must answer:

> **If this agent returns adversarial, stale, malformed, or nonsensical output, can SSSF cross any execution boundary that deterministic CODE did not independently authorize?**

Any `yes` is a design failure.

Representative watched-reds include attempted workflow substitution, unregistered workflow ID, stale workflow generation, omitted required test/review phase, unauthorized model/role/capability, widened budget, changed acceptance obligation, CNO-to-PASS coercion, and direct promotion/landing claims.

## Observability and SQLite continuity

This decision preserves the baseline trace architecture.

Relevant workflow-selection and DSH events join the existing SSSF execution evidence spine:

```text
typed producer events
    ↓
raw durable JSONL/history
    +
existing SQLite query projection (`sssf.db`)
    ↓
UI / observability / reconstruction
```

Do not create a second authoritative DSH or workflow-selection database.

The trace should be able to reconstruct at least:

- request/task identity;
- selector owner (outer or inner);
- recommended workflow ID/generation;
- deterministic admission/refusal result;
- actual instantiated ADW identity;
- each Python phase and CODE transition;
- each DSH cell/inner-unit lineage where used;
- budgets/capability/effect policy identities;
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
6. attempts to prove a genuine use case for a DSH captain/inner coordinator under the burden above;
7. rejects persistent DSH captain architecture if that use case cannot be proven;
8. specifies typed selection/admission contracts and watched-red negative controls;
9. specifies JSONL/SQLite trace integration without a second state owner;
10. identifies any amendments required to `FUT-001`, the DSH implementation plan, ADRs, validators, or workflow catalog before implementation.

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

Before DSH progresses beyond the deterministic protocol/bounded-cell stages into persistent captain or arbitrary topology behavior, the outer-vs-inner ADW selection owner and the DSH-captain burden of proof above must be resolved and recorded.

**Default if unresolved:** retain baseline SSSF — registered Python ADWs connecting bounded specialized agents through CODE-owned seams.