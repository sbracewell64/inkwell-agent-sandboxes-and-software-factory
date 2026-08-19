# Sandbox → DSH Pre-Implementation Plan

## Status and authority

- **Planning status:** `SEQUENCED`, not `ACTIVE`.
- **Sandbox sequence:** existing roadmap B5/B6.
- **DSH sequence:** FUT-001, governed by `docs/decisions/ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`.
- **Purpose of this document:** own the implementation depth, contracts, proof gates, and exact sandbox→DSH seam behind the concise sequencing index in `ROADMAP.md`.
- **Activation boundary:** a named increment under `docs/development/INCREMENT_PROTOCOL.md`.

This document does not claim that the local sandbox replacement or DSH integration exists. It prepares the work so implementation can begin from explicit contracts rather than rediscovering architecture while coding.

`ROADMAP.md` remains the sequencing index. This document is the detailed plan. Architecture documents remain authoritative for accepted/current design facts, and executable code/tests/evidence outrank all planning prose.

## Governing objective

Build one deterministic execution chain:

```text
Engineer intent / typed work
        ↓
SSSF deterministic outer graph
        ↓
provider-neutral execution environment
        ↓
bounded DSH execution cell
        ↓
SSSF deterministic verification / independent review / acceptance
        ↓
Git harvest / promotion / landing under SSSF authority
```

The implementation must preserve the constitutional split:

> **SSSF code owns outer sequencing, source custody, budgets, retries, verification, acceptance, promotion, and terminal state. DSH may own substantial autonomy only inside an externally bounded execution cell.**

The sandbox is not an orchestrator. It supplies an isolated execution environment with observable lifecycle semantics. DSH is not an outer workflow engine. It consumes a bounded cell authorization inside that environment.

## Design constraints carried forward from current SSSF

The future implementation must reuse and converge existing contracts rather than creating parallel mechanisms.

### Source and lifecycle custody

The current lifecycle already establishes important invariants that a replacement provider must preserve:

- a durable `run_id` record exists before provider resources;
- source identity is an exact repository + commit, not a branch-name assumption;
- guest source is gated against the recorded source identity;
- the host provisioning credential never enters the guest;
- runtime credentials are disposable and bounded;
- evidence/artifact reads and Git harvest occur before destructive teardown;
- VM/container destruction is explicit and irreversible;
- implicit shell-session state is not lifecycle state.

### Process/terminal ownership

The B4-002 executor-supervisor work already defines the direction for native process ownership: shell-free launch, exact environment boundaries, closed stdin, monotonic timeout/cancellation, bounded streams, typed terminal outcomes, attempt accounting, descendant cleanup, and quiescence verification.

The sandbox provider and DSH adapter must **reuse or conform to this execution-owner vocabulary**. They must not introduce a second independent timeout/cancellation/process-tree authority merely because execution moved into a container or DSH.

If B4-002 is superseded before activation, use its accepted successor contract rather than its exact current implementation.

### Three-valued observation

Required observations remain explicit rather than Boolean:

- `PASS` / observed-good where a required positive fact was actually established;
- `FAIL` / observed-bad where a violating fact was actually established;
- `COULD_NOT_OBSERVE` where the required fact could not be established.

Absence, unavailable tooling, unreadable provider state, missing evidence, timeout while observing, or an unknown provider response must never become an implicit pass.

### Unit-level transparency without a transparency layer

Do not add an external observer whose job is to reconstruct what sandbox/DSH did after the fact when the owning code can emit the fact directly.

Prefer one hierarchical identity spine:

```text
run_id
  └─ adw_id
      └─ outer_attempt_id
          └─ execution_cell_id
              └─ inner_unit_id
```

`inner_unit_id` is typed by `kind` rather than creating a new unrelated identity system for each later feature. Example kinds may eventually include:

- model-turn;
- process;
- refinement;
- subagent;
- candidate;
- verifier-call;
- workflow-node;
- tool/external-effect unit.

Every relevant inner unit should carry its parent identity, timing, authority/budget attribution, and evidence references directly into the existing durable evidence/trace substrate where practical.

This identity spine is an architectural target, not permission to redesign accepted trace schemas before the owning increment is activated.

---

# Part I — Sandbox program

## Sandbox end-state

The sandbox layer exposes a provider-neutral **Execution Environment Contract**. SSSF code owns lifecycle sequencing; provider adapters implement bounded operations.

A successful environment supplies at least:

- isolated disposable workspace identity;
- exact source repository/commit identity;
- declared writable/mounted surfaces;
- guest toolchain/readiness facts;
- a bounded process-execution primitive compatible with the SSSF execution-owner contract;
- hard timeout/cancel/kill semantics;
- resource ceilings;
- external-effect/network policy;
- port/exposure facts;
- evidence/log/artifact extraction;
- Git harvest;
- provider state inspection;
- explicit destruction;
- proof of terminal quiescence and cleanup.

The provider adapter does **not** own:

- the outer work graph;
- lifecycle phase sequencing;
- retry policy;
- acceptance;
- source selection;
- promotion/landing;
- interpretation of agent results.

## SBX-0 — Reference semantics inventory

**Goal:** extract the semantic contract from the current exe.dev lifecycle before designing the replacement API.

Inventory each current lifecycle fact as one of:

- required provider-neutral semantic;
- exe.dev-specific mechanism;
- current limitation;
- historical artifact that should not survive.

Cover at least:

- create and provider resource identity;
- exact source/fill;
- setup/readiness;
- process execution entry;
- observe/readback;
- app/factory port exposure;
- spend/resource observation;
- artifacts and Git harvest;
- runtime credential lifecycle;
- state inspection/recovery;
- destroy and post-destroy gate.

**Required output:** a machine-readable or validator-readable operation/fact inventory with one owner per fact. Do not create a generic metadata framework if existing run-record/schema mechanisms can own it.

**Exit gate:** every provider-specific command used by lifecycle code is accounted for, and no proposed provider-neutral operation exists only because it is aesthetically convenient.

## SBX-1 — Provider interface and lifecycle state contract

**Goal:** define the smallest provider boundary that can express current semantics and the required future DSH execution environment.

Recommended operation families:

1. `create`
2. `source` / exact fill
3. `setup` / readiness
4. `execute` / bounded process entry
5. `inspect`
6. `expose` / resolve ports where required
7. `extract` / artifacts + evidence
8. `harvest_git`
9. `destroy`

The API may combine operations when implementation evidence shows the split is artificial; semantics matter more than method count.

Each operation must declare:

- exact inputs;
- returned typed facts;
- provider resource identity;
- idempotency/replay behavior;
- observable failure classes;
- CNO conditions;
- what durable state is written and by whom;
- what operation can safely be retried;
- what operation is irreversible.

**Important:** adapter methods report provider facts. The host lifecycle code decides sequencing and retries.

**Exit gate:** a fake provider can exercise all contract branches, including failures, without exe.dev or Docker.

## SBX-2 — exe.dev reference-adapter conformance

**Goal:** pass the current provider through the new contract before replacing it.

This stage is deliberately behavior-preserving. It proves the abstraction describes a system we already understand.

Required proof includes:

- same source identity and guest-head gates;
- same credential boundary;
- same lifecycle ordering;
- same harvest-before-destroy invariant;
- same observable port/readiness behavior;
- same or stricter error/CNO typing;
- no lifecycle sequencing moved into the adapter.

**Exit gate:** reference-adapter contract tests pass against exe.dev, with watched-red controls showing meaningful semantic drift is detectable.

## SBX-3 — Minimal local Docker provider

**Goal:** implement the smallest local/free provider that can complete a provider-neutral lifecycle without live agent inference.

First qualification fixture should use deterministic code only:

```text
create
→ exact source materialization
→ setup/readiness
→ run deterministic command
→ retain bounded evidence
→ harvest a known Git change/artifact
→ destroy
→ prove cleanup
```

Do not begin with DSH, a coding agent, multiple containers, or a full application deployment. Prove the environment first.

Required properties:

- no ambient host source mutation;
- exact source commit in guest;
- explicit mount/write policy;
- reproducible base image/toolchain identity;
- bounded process execution;
- explicit resource identity;
- no Docker socket or equivalent host-control capability in the guest unless a later separately governed capability proves a need;
- deterministic cleanup.

## SBX-4 — Security, credential, network, and external-effect boundary

**Goal:** prove the local provider cannot accidentally widen authority merely because it runs on the Captain's machine.

Required controls:

- host filesystem isolation is explicit, with minimum mounts;
- provisioning/control-plane credentials remain host-only;
- guest runtime secrets are explicit, scoped, revocable/retirable, and never evidence payloads;
- no credential inheritance from ambient host environment;
- no implicit Docker daemon/control socket access in guest;
- network posture is explicit (`none`, bounded/default, or allowlisted policy as later required), never inferred from container defaults;
- external effects are attributable to the execution environment/cell when observable;
- secrets are not placed in argv, durable trace, artifact manifests, or planning/control records.

A missing ability to observe or enforce an intended network/effect boundary is CNO, not permission.

## SBX-5 — Failure recovery, cancellation, and quiescence

**Goal:** make every lifecycle phase recoverable or safely terminal.

Exercise interruption/crash at each material boundary:

- before/after provider resource creation;
- source/fill;
- setup;
- execution start and mid-execution;
- observe/extract;
- Git harvest;
- credential retirement;
- destroy;
- post-destroy gate.

Required behavior:

- durable state lets a later process determine what was attempted;
- retries are identity-bound and do not create silent duplicate resources;
- destroy is idempotent where provider semantics permit;
- evidence is never destroyed before the lifecycle has either harvested it or explicitly recorded why it could not;
- timeout/cancel converges on the shared execution-owner terminal vocabulary;
- provider workloads, child processes, ports, mounts/volumes, and networks are proven quiescent/retired to the degree the platform can observe;
- inability to prove cleanup is CNO/non-clean, never success.

## SBX-6 — Observability and identity integration

**Goal:** make the host able to reason about a running or terminated environment without relying on a model narrative.

Join at minimum:

- `run_id` ↔ provider resource identity;
- source repository/commit;
- environment status;
- ADW identities created inside the run;
- future execution-cell identities;
- bounded process/terminal observations;
- evidence/artifact/harvest references;
- resource/cost observations where available.

Prefer direct writes by lifecycle/runtime owners into the accepted trace/run-record substrate. Do not add a second authoritative observability database merely for Docker/DSH.

Read-only inspection must remain observably distinct from triage/archive mutations or lifecycle state transitions.

## SBX-7 — Parallel sandbox and resource isolation

**Goal:** qualify concurrency before DSH needs parallel children/candidates.

Prove multiple independent environments can coexist without collision in:

- names/IDs;
- source/workspaces;
- ports;
- networks;
- mounts/volumes;
- process ownership;
- environment variables/secrets;
- evidence directories;
- Git harvest targets;
- CPU/memory/time ceilings where the provider supports them.

Exercise one sandbox failing or being destroyed while siblings remain healthy.

Aggregate host resource pressure must be observable enough for deterministic admission/refusal. Do not let a DSH subagent scheduler become the first component to discover that sandbox parallelism is unsafe.

## SBX-8 — Portability, conformance, and provider switch

**Goal:** prove the Docker/local provider is a valid replacement rather than merely a successful demo.

Required comparison:

- exe.dev reference adapter vs local provider against the same provider contract;
- Linux-host behavior where applicable;
- Windows/WSL operator path where supported;
- clean-clone bootstrap and doctor;
- source/evidence/harvest equivalence on shared semantic claims;
- provider-specific differences explicitly classified, never hidden behind a generic PASS.

Only after this stage may the default provider change or exe.dev become optional/retired. Keep the reference adapter as a regression oracle if its maintenance cost remains justified.

## Sandbox acceptance gate for real DSH

Real DSH execution may begin only when an accepted sandbox environment can provide the following facts for the exact candidate being qualified:

1. exact source/workspace identity;
2. explicit writable/mounted scope;
3. bounded process execution;
4. timeout/cancel/kill semantics;
5. resource ceilings;
6. external-effect/network policy;
7. evidence/artifact extraction;
8. durable identity/trace join;
9. Git harvest without promotion authority;
10. forceable termination plus provider/process quiescence proof.

A mock DSH protocol can be developed earlier. A real DSH production-value claim cannot.

---

# Part II — DSH program

## Stable execution-cell protocol

Before enabling a DSH feature, SSSF needs a stable request/result boundary.

### ExecutionCellRequest — minimum semantic fields

The exact schema belongs to its implementation increment, but the contract must cover:

- `execution_cell_id`;
- parent `run_id`, `adw_id`, and `outer_attempt_id`;
- objective and role;
- exact source/workspace identity;
- write/capability/tool authority;
- model/backend policy;
- resource budget;
- wall-time budget;
- token/cost budget where enforceable;
- external-effect/network policy;
- maker/checker independence policy;
- evidence contract;
- expected result schema;
- cancellation handle/identity.

Budgets and authority are inputs owned outside DSH. DSH may spend within them; it cannot enlarge them.

### ExecutionCellResult — minimum semantic fields

Return enough for SSSF to decide what to verify, without storing an acceptance verdict from DSH:

- exact cell/parent identities;
- terminal state and reason;
- typed result/envelope;
- observed source/workspace/mutation facts as applicable;
- usage/cost observations and their source;
- child/inner-unit summary;
- evidence refs/digests;
- external-effect observations;
- cancellation/timeout facts;
- cleanup/quiescence evidence;
- CNO reasons for required facts that could not be observed.

DSH must never return an authoritative SSSF `accepted=true` field. Acceptance is re-derived by SSSF.

## DSH-0A — Protocol and mock executor

**May begin before final Docker qualification.**

Prove the request/result schemas and outer-authority boundary using a deterministic mock DSH executor.

Controls must establish:

- exact identity propagation;
- authority/capability rejection;
- budget bounds;
- result-schema enforcement;
- stale/wrong-source refusal;
- no commit/promotion/outer-graph authority;
- typed CNO rather than missing results;
- attributable evidence;
- cancellation request semantics.

This stage earns protocol confidence only, not evidence that DSH itself is qualified.

## DSH-0B — Execution-cell custody in the real sandbox

**Requires the real sandbox acceptance gate above.**

Run the same mock cell through the actual sandbox and SSSF execution-owner path.

Prove:

- cell identity joins sandbox/ADW/attempt identities;
- environment and process budgets are externally enforced;
- forced timeout/cancellation reaches terminal state;
- evidence survives cell/process failure;
- no processes/children remain after closure;
- source/workspace is unchanged except for explicitly authorized mutations;
- SSSF can harvest results without granting DSH Git promotion authority.

DSH-0B is the seam proof. Do not skip from a schema test directly to a live autonomous DSH worker.

## DSH-1 — Real multi-turn single-agent cell

Admit one exact DSH version/build and one qualified backend/model combination.

Deliberately exclude at first:

- DSH subagents;
- parallel candidates;
- autonomous refinement loops;
- DSH workflows/goals;
- optional plugins;
- self-evolution.

Prove:

- exact DSH/build/dependency identity;
- backend/model/effort identity;
- bounded tools/capabilities;
- source/workspace integrity;
- typed output;
- usage/cost attribution where observable;
- raw/structured evidence custody;
- external-effect adherence;
- hard timeout/cancel;
- quiescence;
- deterministic SSSF verification of the returned candidate.

Compare against the pre-DSH SSSF baseline on the same qualification fixture. DSH must earn value rather than merely run successfully.

## DSH-2 — Bounded autonomous refinement

Qualify internal iteration/Ralph-style repair inside **one outer attempt**.

Required distinctions:

```text
outer_attempt_id = one SSSF attempt
execution_cell_id = one bounded DSH domain
inner_unit_id(kind=refinement) = many possible iterations
```

Measure against DSH-1:

- deterministic final acceptance rate;
- first-result acceptance;
- inner repair count;
- outer retries avoided/added;
- wall time;
- generation tokens/cost;
- defect rate;
- independent review burden.

Code outside the verifier/model owns maximum refinement rounds and all hard budgets.

**Downstream unlock:** once DSH-2 is proven, FUT-005 (verifier-guided progress/refinement) and serial FUT-006 (Best-of-N) become eligible for formal evaluation. They do not automatically become sequenced.

## DSH-3 — Child/subagent lineage and parallelism

First qualify one child, then multiple serial children, then parallel children.

Requires SBX-7 parallel/resource isolation.

Every child must inherit a strictly equal-or-narrower authority set and contribute to aggregate cell ceilings.

Required evidence:

- parent/child lineage;
- model/backend identity per child;
- child tool/effect authority;
- per-child and aggregate budget use;
- child outputs/evidence;
- cancellation propagation;
- no surviving children/processes at cell closure.

**Downstream unlock:** parallel FUT-006 and production-grade hierarchical FUT-008 evaluation become eligible only after this stage's lineage and aggregate-budget proofs.

## DSH-4 — Inner workflows and goals

Qualify DSH workflows, `tool-workflow`, and goal-driven inner execution.

An inner graph may be sophisticated, but it remains one descendant domain of the SSSF outer attempt. It cannot:

- create another SSSF outer attempt;
- advance an SSSF phase;
- decide acceptance;
- commit/promote/land;
- alter its own external budget/authority.

Workflow-node activity uses the same `inner_unit_id` lineage rather than a second trace universe.

## DSH-5 — Richer engineering capabilities

Evaluate capabilities one at a time against the last accepted baseline, including where justified:

- compaction;
- MCP;
- LSP/code intelligence;
- code mode;
- long-running/background workers;
- persistent terminal mechanisms;
- selected DSH plugins or built-in equivalents.

Before designing a new post-DSH capability, consult the preserved Awesome DSH Plugin catalog research reference. Catalog inclusion never implies admission.

Each capability must prove:

- exact source/build/dependency identity;
- authority containment;
- lifecycle/cancellation/quiescence;
- evidence attribution;
- resource/effect boundaries;
- measurable value over the prior baseline;
- rollback/retirement.

## DSH-6 — Product subagents and maker/checker boundaries

Qualify use of Claude/Codex/DeepSeek or other product agents as bounded inner workers only after their underlying execution contracts are independently known.

A DSH ability to call two models does not by itself establish independent review. SSSF owns the independence policy and may require a separate cell/process/credential/context boundary.

Same-model self-verification is optimization, not maker/checker independence.

## DSH-7 — Adaptive inner orchestration

Permit DSH to choose dynamically, within the fixed cell authorization, whether to:

- refine;
- delegate;
- invoke an admitted critic/verifier;
- choose among admitted tools;
- compact;
- explore an alternative candidate;
- return early.

The adaptive policy may choose how to spend a budget. It cannot choose its budget or outer authority.

By this stage, probabilistic-verifier observations may participate only if the applicable FUT candidates have separately passed their own promotion/qualification gates.

## DSH-8 — Governed self-evolution

Research persistent improvement only after all preceding identity, evidence, rollback, independence, and promotion mechanisms are proven.

Allowed shape:

```text
immutable running generation
    → proposes immutable candidate generation
    → isolated deterministic evaluation
    → negative controls
    → security/dependency review
    → independent semantic review where required
    → SSSF-owned promotion or rejection
```

A production DSH generation never silently changes its own persistent prompt, skill, workflow, plugin, memory authority, or production configuration.

---

# Shared evidence and architecture-unit discipline

## One fact, one owner

For every new sandbox/DSH architectural fact, identify exactly one executable or machine-readable owner where practical. Documentation explains the contract and rationale; it should not become a second state store.

For each material architecture unit record at least:

- purpose/problem;
- owner;
- inputs;
- outputs;
- state;
- authority gained/denied;
- identity/parent relationship;
- budget/effect boundary;
- verifier;
- watched-red/negative control;
- evidence surface;
- rollback/retirement;
- documentation/ADR reference when architectural.

Do this in the smallest existing appropriate schema/record. Do not create a universal architecture registry unless repeated implementation evidence shows the existing surfaces cannot express these facts without duplication.

## Direct evidence emission

Prefer:

```text
owning code performs state transition
        + emits typed durable fact
```

over:

```text
owning code performs opaque activity
        → separate monitor observes it
        → monitor guesses durable fact
```

This is especially important for DSH inner units. DSH/adapters should emit machine-readable lifecycle/evidence facts at the seam; an external transparency process should not be required to infer them from terminal text.

---

# Downstream unlock map

An **unlock** means a preserved/candidate idea becomes eligible for formal evaluation. It does not mean `DECIDED`, `SEQUENCED`, or `ACTIVE`.

| Proven prerequisite | Newly eligible evaluation |
|---|---|
| SBX-0..2 | local-provider implementation can begin |
| SBX-3..6 | real DSH-0B custody qualification |
| SBX-7 | DSH-3 parallel child/candidate qualification |
| DSH-0A | typed ExecutionCell/criteria/evidence protocol refinement |
| DSH-1 | FUT-007 criteria-decomposition evaluation; early FUT-008 evidence-schema evaluation |
| DSH-2 | FUT-005 verifier-guided refinement; serial FUT-006 Best-of-N |
| DSH-3 | parallel FUT-006; governed hierarchical FUT-008 production qualification |
| DSH-5 | selected Awesome-DSH-plugin/catalog capabilities, one candidate at a time |
| DSH-8 prerequisites | governed self-evolution candidates |

FUT-008-style provenance/evidence fundamentals should influence the base execution-cell evidence design from DSH-0, but FUT-008 itself remains a candidate until evaluated. Production use of FUT-005/FUT-006/FUT-007 requires a qualified governed verifier-evidence substrate.

---

# Qualification rules for every stage

No stage advances merely because the happy path ran.

Each activated increment must define, as applicable:

1. exact source/build/dependency identities;
2. positive non-vacuity control;
3. watched-red defect controls;
4. failure and CNO behavior;
5. authority-negative controls (what the component must be unable to do);
6. interruption/cancellation controls;
7. quiescence/cleanup controls;
8. source/workspace integrity controls;
9. evidence/provenance bindings;
10. security/external-effect controls;
11. resource/time/token/cost accounting where observable;
12. rollback/retirement path;
13. baseline comparison and net-complexity justification;
14. independent review and normal SSSF acceptance/proof requirements.

A later stage invalidates no earlier proof automatically, but any changed shared contract must requalify all materially affected consumers.

# Readiness to activate sandbox implementation

The sandbox plan may move from planning to an `ACTIVE` increment only when:

- current PRE_CERTIFICATION/serialized work permits a new sandbox increment;
- the accepted current source/lifecycle/security/evidence documents are reconciled enough to serve as the reference contract;
- B4-002 or its successor terminal/cancellation contract has a usable exact candidate identity;
- SBX-0 scope and acceptance criteria can be stated without depending on unresolved product preference;
- implementation can occur in an isolated branch/worktree with normal proof gates.

Activation should begin at SBX-0/SBX-1, not by replacing exe.dev commands.

# Readiness to activate DSH implementation

DSH protocol work may become `ACTIVE` at DSH-0A when:

- ADR-0004 remains applicable to then-current SSSF;
- the execution-cell request/result authority model has no unresolved Captain-only product choice;
- the accepted evidence/identity terminology is stable enough to avoid inventing parallel types;
- a mock DSH adapter can be built without implying real DSH qualification.

Real DSH work beyond DSH-0A additionally requires the sandbox acceptance gate and a qualified execution-owner/process contract.

# Explicit non-goals before activation

Do not:

- replace the SSSF outer ADW graph with DSH;
- place DSH inside SSSF merely as a hidden model proxy;
- make the sandbox provider own orchestration/retry/acceptance;
- introduce a second process supervisor if the accepted B4-002 successor can own the job;
- introduce a second authoritative trace/evidence database solely for sandbox/DSH;
- hide multiple model generations/verifier calls behind one apparent model event;
- grant Docker/guest processes host control-plane credentials;
- enable plugin marketplace or automatic plugin updates;
- implement probabilistic-verifier candidates before their DSH gates;
- begin governed self-evolution before immutable-generation promotion/rollback is proven.
