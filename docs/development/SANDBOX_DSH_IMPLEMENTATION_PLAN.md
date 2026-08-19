# Sandbox → DSH Pre-Implementation Plan

## Status and authority

- **Planning status:** `SEQUENCED`, not `ACTIVE` except where a separately named increment has crossed the activation boundary.
- **Sandbox sequence:** B5/B6 in `ROADMAP.md`.
- **DSH sequence:** FUT-001 under `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`.
- **Operator sequence:** LAUNCH-1 → Docker commission → baseline PR/freeze → existing Wayfinder commission → DSH.
- **Activation boundary:** a named increment under `docs/development/INCREMENT_PROTOCOL.md`.
- **Purpose:** own the detailed execution contracts, stage gates, evidence requirements and exact operator→sandbox→DSH seams behind the concise roadmap.

This file does not claim that Docker, the launcher, Wayfinder commissioning or DSH is implemented. It is the pre-implementation specification.

## Governing value creators

SSSF must preserve three different value creators:

### ENGINEER — value and reserved authority

The Engineer/Captain owns:

- product intent and desired outcome;
- personal/product preference choices;
- new monetary expenditure;
- security/privacy exceptions;
- materially irreversible decisions;
- explicit changes in delegated authority.

The system should minimize Engineer interruption. Facts that code or agents can establish are not questions for the Engineer.

### AGENT — uncertainty reduction

Agents own bounded semantic work where judgment genuinely remains, including:

- investigation;
- interpretation of ambiguous evidence;
- design alternatives;
- code generation and repair inside a bounded assignment;
- semantic review;
- recommendations under uncertainty.

Agents do not become durable state machines merely because they can reason about state.

### CODE — state transition

Deterministic code owns every stable/checkable transition it can own honestly, including:

- sequencing;
- applicability;
- routing;
- budgets and retry ceilings;
- durable identities/state;
- three-valued observation folding;
- validation;
- acceptance;
- recovery decisions when their rules are known;
- promotion/landing;
- terminal state.

Optimization direction:

> **Minimize Engineer feedback. Use agents for irreducible uncertainty. Push stable/checkable behavior into code.**

This is the default answer to future ownership disputes unless a more specific accepted contract says otherwise.

## Governing chain

```text
Engineer intent / reserved decisions
        ↓
FirstMate semantic supervision / uncertainty reduction
        ↓
SSSF typed work + deterministic outer graph
        ↓
qualified AgentBackend + Docker SandboxProvider
        ↓
bounded DSH execution cell (after DSH activation)
        ↓
SSSF deterministic VerificationContracts
        ↓
assignment-distinct semantic review where required
        ↓
Browser Sol ruling where policy requires
        ↓
one-use landing authorization
        ↓
exact-main proof / disposition
```

Docker is an execution boundary, not an orchestrator. DSH is an inner execution coordinator, not the SSSF outer workflow engine. Wayfinder is an operator/intent connector, not a state authority.

## Cordis/DSH private-implementation research boundary

The DSH plan is informed by a source-level review of:

- repository: `dolphin-creator/cordis-python`;
- reviewed commit: `e610aca184bdd823c96ba76484921f9f40aec68d`;
- reviewed tree: `2d239a85266394b2f1099ea68f512e037eef35a5`;
- observed commit message: `v0.11.1: harden nested session context propagation`;
- package source at that commit still declares `__version__ = "0.11.0"`, so Git identity, not the human-facing version string, is authoritative for this research reference.

This is a **research/reference identity**, not an SSSF dependency, trust grant, production plugin source, or architectural substrate.

Governing rule:

> **Cordis concepts may remain private inside DSH; SSSF consumes typed execution-cell contracts and evidence, not Cordis abstractions.**

SSSF must not acquire public `Context`, `Fiber`, `Service`, `Effect`, plugin-reconciliation, or event-waterfall concepts merely because a DSH implementation uses them internally. DSH may use equivalent internal mechanisms when they improve bounded autonomy, but the outer SSSF contract remains implementation-independent.

The strongest extracted Cordis principles are requirements/proof inputs for the DSH stages below:

1. every reversible inner effect/resource has a lifecycle owner;
2. capability/resource availability is distinct from execution authority;
3. unauthorized capabilities are omitted from model-visible schemas where practical and authority is rechecked at final dispatch;
4. specialized workers use private, narrow registries rather than inheriting all parent tools;
5. delegation is structurally bounded and explicit before generic recursion is considered;
6. effective runtime composition is deterministic, content-addressed and provenance-aware;
7. durable historical evidence is distinct from the active model/context projection;
8. context budgeting and deterministic compaction are CODE concerns, not model discretion;
9. every autonomous inner unit terminates with typed evidence/manifest data;
10. inner retries/refinements remain descendants of one SSSF outer attempt;
11. optional internal implementations depend on stable contracts/capabilities rather than sibling implementation classes;
12. cooperative inner cleanup never substitutes for SSSF-owned external process/environment quiescence proof.

---

# 1. Near-term commissioning sequence

The approved near-term target is a usable SSSF before DSH:

```text
current deterministic/control-plane qualification closure
        ↓
LAUNCH-1 — obvious one-click Windows entry into SSSF/FirstMate
        ↓
SBX-0 / SBX-1 — extract provider semantics and prove contract with fake
        ↓
SBX-2..8 — implement and qualify DockerSbxProvider
        ↓
BASELINE-PR — ordinary real PR through Docker-backed accepted path
        ↓
freeze post-Docker / pre-DSH baseline
        ↓
complete Captain's existing Wayfinder setup
        ↓
commission Captain → Wayfinder → FirstMate → SSSF transport
        ↓
DSH-0A / 0B / 1...
```

## Exe.dev retirement rule

`exe.dev` is leaving the target architecture because the operator subscription is expiring/possibly already unavailable.

Therefore:

- Docker is the **required** production sandbox implementation;
- no roadmap checkpoint requires continued exe.dev service availability;
- existing exe.dev code, documentation, tests and retained evidence remain useful reference material for SBX-0;
- if live exe.dev still works, an opportunistic conformance comparison may be recorded;
- if it is unavailable, record `EXTERNAL_DEPENDENCY` and continue Docker work from durable evidence;
- do not spend money or renew/add a service merely to satisfy a historical parity gate without Captain authorization.

---

# 2. Required pre-Docker substrate

Docker needs enough provider-independent SSSF machinery to be implemented and judged correctly. It does **not** need a live exe.dev real-PR demonstration first.

## 2.1 AgentBackend and SandboxProvider are orthogonal

### AgentBackend

`AgentBackend` answers: **how does one bounded reasoning assignment execute?**

Target semantic contract:

```text
execute(PhaseWorkEnvelope) -> PhaseExecutionResult
cancel(attempt_id)
attest_binding()
inspect_usage()
verify_quiescence()
```

Policy-relevant facts are explicit or CNO: product/backend, exact model/profile, attempt/session/process identity, exact supplied input/protocol identity, tool/capability boundary, terminal outcome, usage source and quiescence.

Host-native product CLIs remain host-custodied when moving their auth/settings into Docker would produce a different binding. A changed binding requires separate qualification.

### SandboxProvider

`SandboxProvider` answers: **what isolated execution world exists and what is its observed state?**

Target semantic surface:

```text
create(SandboxSpec)
exec(CommandSpec)
copy_in / copy_out       # only where required
inspect()
collect_artifacts()
export_git()
inspect_processes()
wait_quiescent()
stop()
destroy(authorization)
reconcile()
```

Provider adapters report/perform environment mechanics. SSSF code owns lifecycle sequence, retry/recovery policy, acceptance and promotion.

Use `reconcile`, not provider-owned autonomous recovery: provider reports facts; code decides the next legal transition.

## 2.2 CommandSpec is typed authority

Any command relied upon as evidence binds at least:

- argv;
- cwd;
- environment references/allowlist;
- timeout;
- stdin mode;
- stdout/stderr policy/bounds;
- expected exit semantics;
- execution/attempt identity.

Unstructured shell prose is not authoritative command identity.

The accepted B4-002 subprocess-supervisor semantics (or successor) own process launch, bounded streams, monotonic timeout/cancellation, attempt accounting, descendant cleanup, three-valued terminal observation and quiescence. Docker and DSH conform to this owner rather than create parallel supervisors.

## 2.3 Source authority and Source Broker

Source authority is:

```text
repository URL + exact commit SHA + exact tree SHA
```

A branch is convenience state only.

Evidence-bearing mutation/review workers never receive the credential-bearing canonical host checkout. The SSSF-owned Source Broker produces disposable, credential-free full Git clones at exact identity.

Rules:

- canonical host checkout is no-worker-access;
- broker clone is clean and exact before use;
- ignored host secrets/config are not copied;
- worker remote/config changes stay inside disposable clone;
- clone survives until export/evidence obligations complete;
- inability to prove identity is CNO/non-PASS.

## 2.4 Immutable cognition/input boundary

Evidence-bearing workers must not silently inherit mutable cross-sandbox cognition.

Operational instructions/protocols come from the pinned source commit, immutable worker template or another content-addressed SSSF artifact. Exact reviewer protocol/input identity is recorded by the execution owner.

FUT-011 may later strengthen how these instruction artifacts are qualified, but instruction governance is not a blocker for initial Docker lifecycle code unless an active instruction is itself acceptance-critical.

## 2.5 Verification / semantic review / landing contracts

Acceptance-critical obligations are code-discoverable and exact-head bound.

Target semantics include:

```text
verification-contract/v1
review-envelope/v1
semantic-review-result/v1
ruling-envelope/v1
landing-authorization/v1
```

Required properties:

- deterministic applicability determines required verifier obligations;
- absent/stale/skipped/wrong-head/CNO-under-PASS-policy evidence is non-PASS;
- fixtures calibrate but do not replace required real-seam proof;
- reviewer assignment and protocol identity are explicit;
- maker/reviewer separation is explicit where policy requires it;
- Browser Sol transport binds exact request/candidate/envelope identity;
- rulings do not become timeless PASS artifacts;
- deterministic code mints one-use landing authority only after all applicable requirements hold;
- mutation-time movement invalidates authorization;
- exact resulting main receives post-merge proof.

## 2.6 Docker-readiness gate

Before Docker mutation work begins, the accepted/current SSSF must be stable enough to judge the Docker increment:

1. AgentBackend and SandboxProvider authority are distinct;
2. process/CommandSpec ownership and quiescence semantics are defined;
3. exact source identity/custody is defined;
4. three-valued verification/review semantics are adequate for Docker evidence;
5. landing/provenance rules needed by the Docker PR are operational or explicitly bounded in the increment;
6. no known defect would make Docker evidence materially untrustworthy.

**Not required before Docker:**

- a live exe.dev provider;
- exe.dev parity proof;
- a real ordinary PR through exe.dev;
- DSH;
- Wayfinder commissioning.

The real ordinary PR commission moves to the accepted Docker path before DSH.

---

# 3. LAUNCH-1 — operator-facing SSSF front door

## Purpose

Give the Captain one obvious action that starts/enters the intended FirstMate→SSSF operating context.

The repository already has lower-level engineering commands such as `just local cc`; those remain useful. LAUNCH-1 is a thin operator transport surface over the accepted authority chain, not a new orchestrator.

## Required behavior

- one-click/double-click friendly on the supported Windows path;
- resolves/enters the canonical SSSF repository rather than relying on the current shell directory;
- invokes the existing FirstMate/SSSF entry mechanism using local configuration rather than embedding credentials;
- prints/records enough identity to diagnose wrong repo/path/config;
- fails visibly/actionably rather than opening a misleading idle shell;
- owns no planning state, workflow sequencing, retries, acceptance or landing;
- smallest practical implementation: script/shortcut wrapper before GUI framework;
- removable without altering SSSF engineering semantics.

## Acceptance

Positive control: from the supported Windows operator state, the launcher reaches the intended FirstMate/SSSF context and the session can identify the canonical repository and current high-level status.

Negative controls include wrong/missing repo path, missing launch dependency, malformed local configuration and accidental credential embedding.

The launcher may land before Docker and must label uncommissioned downstream capabilities honestly.

---

# 4. Shared identity and evidence spine

Avoid a new identity namespace for every future feature.

Preferred hierarchy:

```text
run_id
  └─ adw_id
      └─ outer_attempt_id
          └─ execution_cell_id
              └─ inner_unit_id(kind=...)
```

Possible inner-unit kinds include process, model-turn, refinement, subagent, candidate, verifier-call, workflow-node and external-effect unit.

Each relevant unit carries parent identity, timing, authority/budget attribution and evidence refs. Prefer owner-emitted durable facts over a transparency daemon reconstructing activity from prose.

Three-valued observation is exhaustive: PASS/observed-good, FAIL/observed-bad, COULD_NOT_OBSERVE. Missing state is never implicit success.

DSH inner attribution must be explicit wherever the execution protocol can bind it. Do not make temporal proximity or mutable "last active worker" state authoritative for parentage. Every independently reportable inner unit should carry explicit `inner_unit_id`, `parent_unit_id`, `execution_cell_id` and `outer_attempt_id` or an exact equivalent mapping.

Durable execution evidence and active model context are different owners:

```text
append-only / immutable evidence history
                ≠
current model-visible working projection
```

Compaction, summarization, checkpointing or context rotation may change the active projection. They must not rewrite historical evidence to make the projection look like the complete history.

---

# 5. Docker sandbox program

## SBX-0 — Reference semantics inventory

Inventory the current sandbox lifecycle from canonical code, docs, tests and retained evidence.

Classify every relevant fact as:

- required provider-neutral semantic;
- exe.dev-specific mechanism;
- current limitation;
- obsolete/historical artifact.

Cover resource identity, exact source/fill, setup/readiness, process entry, exposure/ports, resource/spend facts where relevant, evidence/Git harvest, runtime-secret lifecycle, state inspection/reconciliation, destroy and post-destroy observation.

Live exe.dev calls are not required.

**Exit:** complete machine/validator-readable semantics inventory with one owner per fact and no material current provider behavior unclassified.

## SBX-1 — SandboxProvider contract + deterministic fake

Define the minimum typed contract: `SandboxSpec`, `CommandSpec`, returned fact types, idempotency, retry safety, irreversible operations, durable-state owner, failure classes and CNO semantics.

`SandboxSpec` binds at least run/attempt identity, exact source repo/commit/tree, role/profile, clone/workspace mode, resource bounds, immutable template identity, network/effect policy identity, secret references, cognition/shared-instruction policy and evidence root.

**Exit:** deterministic fake provider exercises every success/failure/CNO contract branch without external sandbox service.

## SBX-2 — Docker feasibility and adapter contract binding

Use direct Docker feasibility evidence to bind the selected implementation to SBX-1.

Tasks include:

- verify the exact Docker/Sandbox tooling actually available on supported Windows/WSL;
- identify required CLI/API/build identities;
- map every SBX-1 operation to the selected Docker mechanism;
- prove no hidden provider-owned workflow/recovery authority is introduced;
- establish deterministic fixture harness and failure/CNO mapping.

If exe.dev happens to be available, the same semantic fixture may be run against it as supplemental historical comparison. Failure/unavailability does not block this stage.

**Exit:** Docker adapter contract is executable against deterministic fixtures and no required semantic is left as an unowned guess.

## SBX-3 — Minimal deterministic Docker lifecycle

First real fixture uses deterministic code only:

```text
create
→ exact broker source clone
→ setup/readiness
→ exec(CommandSpec)
→ bounded evidence
→ known artifact/Git export
→ quiescence
→ destroy
→ authoritative residual-state check
```

No live coding agent or DSH.

**Exit:** exact source, deterministic command/evidence/export and cleanup are proven on real Docker seams.

## SBX-4 — Security / credential / network / cognition boundary

Prove:

- source broker + canonical checkout no-worker-access;
- minimum explicit mounts/writes;
- no host control-plane credentials/auth homes in guest;
- no uncontrolled Docker socket/control capability in guest;
- runtime secrets explicit/scoped and absent from argv/evidence;
- network/effect policy explicit;
- shared mutable instruction inheritance disabled for evidence-bearing workers where appropriate;
- worker template/toolchain identity pinned after feasibility.

Missing enforcement/observability is CNO, not permission.

## SBX-5 — Cancellation / reconciliation / quiescence

Interrupt before/after create, source, setup, execution, observation/extraction, Git harvest, secret retirement, destroy and post-destroy check.

Required behavior:

- durable identity supports later reconciliation;
- retry does not silently duplicate resources;
- provider reports actual state; SSSF decides recovery;
- evidence/harvest precedes irreversible destroy;
- cancellation converges on accepted process-owner semantics;
- inability to prove provider/process cleanup is non-clean CNO.

## SBX-6 — Observability + identity integration

Join run/provider/source/ADW/process/evidence/harvest/future-cell identity through existing accepted owners. No second authoritative Docker/DSH observability DB.

Read-only observation remains distinct from triage/lifecycle mutation.

## SBX-7 — Deterministic parallelism and reviewer isolation

Executable parallel work remains an SSSF-owned WorkNode DAG or accepted equivalent binding dependencies, role, source, expected writes, resource locks, AgentBackend profile, SandboxProvider profile and verification/acceptance obligations.

SSSF owns max parallelism, queueing, admission/backpressure, retry, cancellation, collection and aggregate result folding.

Prove two genuinely overlapping Docker sandboxes, peer survival when another fails/cancels, capacity behavior, deterministic result collection and complete cleanup.

Maker/checker identities and evidence roots remain distinct.

## SBX-8 — Docker commission and post-Docker/pre-DSH baseline

No live exe.dev parity requirement.

Required real commission:

1. complete SandboxProvider conformance on the supported Docker/Windows/WSL path;
2. real source/security/cancellation/quiescence/evidence proofs required by the active contracts;
3. one **ordinary completed baseline engineering PR** run through the Docker-backed accepted SSSF path without Captain transport;
4. exact review/ruling/landing behavior as applicable;
5. exact resulting main proof;
6. clean teardown/reconciliation;
7. LAUNCH-1 can enter the commissioned environment without owning workflow authority.

Then:

- freeze an immutable **post-Docker / pre-DSH baseline**;
- make Docker the only accepted/default sandbox provider;
- retain exe.dev material only as historical/reference evidence until deliberate cleanup retires it.

This baseline is the comparison point for DSH value claims.

---

# 6. WAYFINDER-1 — commission the existing operator connector

## Identity

This is the Captain's already-prepared/partially configured Wayfinder setup. It is **not** the Matt Pocock Wayfinder repository reviewed under FUT-013 and must not be silently replaced by it.

## Purpose

```text
Captain
   ↓
existing Wayfinder
   ↓
FirstMate
   ↓
SSSF typed planning/work/execution surfaces
```

Wayfinder improves Engineer ergonomics and intent/decision transport. It does not become SSSF engineering state authority.

## Ownership

- Engineer/Captain supplies value intent and reserved decisions through Wayfinder.
- Wayfinder transports/indexes the interaction as configured.
- FirstMate performs supervision, fact gathering, classification and work progression.
- Browser Sol resolves delegated material engineering judgment.
- SSSF code owns admitted execution state and acceptance.

## Commissioning requirements

- complete existing setup rather than introducing a new Wayfinder implementation;
- bind the correct FirstMate/SSSF project identity;
- establish typed/durable pointers where possible rather than conversational-memory-only linkage;
- facts the system can observe are not routed to the Captain as questions;
- reversible engineering ambiguity stays in FirstMate/Browser Sol;
- Captain-only questions stay explicit;
- no duplicate roadmap/increment/PR truth is created;
- rollback removes the connector without changing SSSF state.

WAYFINDER-1 is commissioned after SBX-8/post-Docker baseline and before real DSH activation.

---

# 7. DSH gate and execution-cell protocol

Real DSH requires the accepted Docker baseline plus WAYFINDER-1 commission.

The environment must already prove exact source/workspace identity, write/mount scope, typed bounded process execution, timeout/cancel/kill, resource ceilings, network/effect policy, evidence extraction, durable identity/trace join, Git harvest without promotion authority, provider/process quiescence, qualified AgentBackend binding and accepted verification/review/landing semantics.

## 7.1 Private-runtime boundary

DSH may internally use Cordis-style contexts, fibers/effects, services, scoped events, dependency reconciliation, private tool registries or equivalent mechanisms. Those remain implementation detail.

The public SSSF↔DSH seam should stay small:

```text
ExecutionCellRequest
        ↓
opaque qualified DSH generation
        ↓
ExecutionCellResult + typed inner evidence
```

Do not add SSSF-visible Cordis abstractions merely to mirror an internal implementation.

## 7.2 Effective runtime identity and provenance

The cell must bind the **effective runtime actually authorized**, not merely a package/version label.

At minimum, where applicable:

- exact DSH source/build identity;
- dependency/lock identity;
- effective profile/composition digest;
- capability-policy digest;
- instruction/prompt/protocol digest(s);
- backend/model policy identity;
- plugin/capability generation identities admitted to the cell;
- provenance showing which authoritative layer supplied policy-relevant effective values.

Use full cryptographic digests for proof identity. A shortened display fingerprint may exist for UI convenience but is not authoritative evidence.

Configuration provenance should fall out of deterministic composition where possible; do not create a separate provenance service merely to explain values code can already attribute while composing them.

## 7.3 Capability availability is not authority

Model/tool design must distinguish:

```text
resource/capability exists
        ≠
principal/cell may use it
```

`ExecutionCellRequest` therefore distinguishes available capability seams/backends from admitted authority. A mounted plugin, available executable, MCP server, browser, filesystem or subagent factory is not authorization by existence.

Prefer two gates for model-facing capabilities:

1. omit unauthorized tools/capabilities from the model-visible schema/context where practical;
2. recheck current authority immediately before actual dispatch/effect.

The second check is the authority boundary. Stale model context, forged tool calls or a policy change after schema construction must not bypass it.

## 7.4 Inner lifecycle/effect ownership

Every reversible resource created inside a cell should have one lifecycle owner, including as applicable:

- tool/listener registrations;
- child workers;
- provider/network/browser clients;
- MCP/LSP connections;
- temporary files/workspaces;
- background tasks;
- internal processes;
- internal plugin/capability mounts;
- context/session projections.

Cooperative cleanup should unwind all owned resources even if one cleanup fails; cleanup failures remain evidence.

This is **not** terminal authority. SSSF's accepted process owner + Docker provider independently enforce timeout/cancel/kill and prove descendant/environment quiescence after DSH cooperative cleanup.

## ExecutionCellRequest

Minimum semantics:

- execution_cell_id + parent run/adw/outer-attempt identities;
- objective/role;
- exact source/workspace identity;
- selected qualified AgentBackend profile/allowed set;
- effective DSH/runtime/config/policy/instruction identities;
- available capability seams/backends;
- write/tool/capability authority;
- explicit allowed delegation edges/depth where children are admitted;
- time/resource/token/cost/iteration/child ceilings;
- effect/network policy;
- maker/checker policy;
- applicable VerificationContract/review-policy references;
- evidence contract;
- expected result schema;
- cancellation identity.

DSH may spend inside the fixed authorization but cannot enlarge it.

## ExecutionCellResult

Return observed facts, never SSSF acceptance authority:

- exact identities;
- effective runtime/config/policy digests actually used;
- terminal state/reason;
- typed result/envelope;
- source/workspace/mutation facts;
- backend binding/execution evidence;
- usage/cost observations, including exact-vs-estimated provenance where applicable;
- child/inner-unit summary with explicit parent bindings;
- per-inner-unit terminal manifests/evidence refs as required;
- context/compaction actions and historical-coverage refs where relevant;
- evidence refs/digests;
- effect/cleanup observations;
- cancellation/timeout facts;
- cleanup/quiescence;
- CNO reasons.

DSH never returns authoritative `accepted=true`; SSSF derives acceptance.

Child/research/verifier outputs carry provenance and a trust/authority class. A useful child result is data/evidence, not automatically instruction or execution authority.

---

# 8. DSH qualification sequence

## DSH-0A — Protocol + deterministic mock

After WAYFINDER-1, prove request/result identity, authority rejection, budgets, result schema, stale/wrong-source refusal, no outer graph/commit/promotion authority, typed CNO, evidence attribution and cancellation using a deterministic mock.

Also prove the protocol can represent, without Cordis-specific public nouns:

- full effective runtime/config/policy/instruction digests;
- policy-relevant configuration provenance;
- capability availability separately from granted authority;
- explicit parent/child/inner-unit identity;
- allowed delegation edges/depth;
- lifecycle/effect evidence classes;
- durable-history versus active-projection identity;
- per-inner-unit typed terminal manifests;
- exact-vs-estimated usage provenance.

Negative controls include:

- capability exists but authority is absent;
- stale/forged tool request cannot gain authority;
- changed effective configuration without changed digest is rejected;
- child identity without valid parent/cell binding is rejected;
- inner unit attempts to claim outer acceptance/promotion authority;
- shortened/display-only fingerprints are insufficient where full proof digest is required.

Protocol proof does not authorize real autonomous DSH.

## DSH-0B — Real Docker custody seam

Run the mock through accepted Docker SandboxProvider + AgentBackend/process-owner path.

Prove:

- identity joins across run → ADW → outer attempt → cell → inner unit;
- effective runtime/config/policy identity survives into evidence;
- external budget enforcement;
- timeout/cancel;
- evidence survival;
- authorized mutation only;
- Git harvest without promotion authority;
- cooperative DSH cleanup is observable;
- SSSF process custody independently kills/cleans residual descendants;
- Docker provider independently proves environment/resource quiescence;
- zero surviving processes/children/resources at a clean terminal state.

A DSH/Cordis-style `close()`/dispose success, immediate-child `process.kill()`, empty internal registry or missing process is **not** sufficient quiescence proof by itself.

## DSH-1 — Real multi-turn single-agent cell

Admit one exact DSH build/dependency identity and one qualified backend/model profile. Exclude subagents, autonomous refinement, workflows/goals, optional plugins and self-evolution.

Require:

- bounded private model-visible tool registry;
- capability/resource existence separated from cell authority;
- unauthorized tool omission where practical plus dispatch-time reauthorization;
- deterministic effective runtime/config/policy fingerprinting using full proof digests;
- deterministic context-window budgeting owned by code;
- durable append-only/history evidence distinct from active model/context projection;
- any compaction/checkpoint transformation recorded without rewriting historical truth;
- exact model-visible request/event attribution where retained by the evidence contract;
- typed terminal inner-unit manifest containing source/mutation/tool/usage/context/result/failure/cleanup facts;
- bounded tools/effects, source integrity, typed output, hard timeout/cancel, quiescence and deterministic SSSF verification/review.

Compare against the post-Docker/pre-DSH baseline.

Do not initially grant DSH authority to commit/promote/land candidate Git state. Prefer dirty/disposable candidate workspace + SSSF-owned harvest/promotion until a later explicit need is proven.

**Unlock:** FUT-007 and early FUT-008 schema evaluation.

## DSH-2 — Bounded autonomous refinement

Permit internal repair/refinement inside one outer attempt with externally fixed iteration/time/token/cost ceilings. Measure deterministic acceptance, outer retries, latency/cost/defects and reviewer burden against DSH-1.

Add typed inner-attempt/refinement evidence:

- inner attempt/iteration identity;
- failure class;
- retryable/non-retryable classification;
- deterministic retry reason/policy identity;
- remaining inner budget;
- policy/gate changes between attempts;
- terminal manifest per material attempt or a lossless indexed summary under the evidence contract.

Evaluate cheap CODE-owned loop guards before adding semantic loop observers, including:

- duplicate identical tool-call suppression within one model response;
- configurable per-turn/tool/action ceilings;
- repeated identical read-only-call suppression while no relevant state changed;
- invalidation of stale read suppression after writes/state changes;
- empty-success guards such as no required change/no usable final result.

These are DSH inner controls. They never mint another SSSF `outer_attempt_id`.

**Unlock:** FUT-005 and serial FUT-006.

## DSH-3 — Child/subagent lineage + parallelism

Requires SBX-7. Qualify one child, serial children, then parallel children. Every child gets equal-or-narrower authority; aggregate budgets are externally enforced. Prove lineage, per-child evidence, cancellation propagation and quiescence.

Start with **typed structural delegation edges**, not a generic recursive worker graph. Example:

```text
builder → research
builder → critic
research → none
critic   → none
```

Required properties:

- each child receives a private, narrow tool/capability registry appropriate to its role;
- parent tool visibility is not inherited by default;
- child authority is equal-or-narrower and dispatch-time enforced;
- `inner_unit_id`, `parent_unit_id`, `execution_cell_id` and outer-attempt binding are explicit rather than inferred from temporal order;
- child results cross boundaries with provenance/trust classification and do not become instructions by default;
- asymmetric one-way delegation is preferred when it bounds recursion more strongly than policy prose;
- generic recursive spawning requires a separately demonstrated need plus externally fixed depth/child/aggregate budgets;
- cancellation propagates through the declared child graph and external SSSF/Docker custody still proves quiescence.

**Unlock:** parallel FUT-006 and hierarchical FUT-008.

## DSH-4 — Inner workflows/goals

Qualify inner DSH workflows/goal graphs as descendants of one SSSF outer attempt. They cannot create/advance outer attempts/phases, alter budgets, decide acceptance or land/promote.

Workflow nodes should reuse the same inner-unit identity/evidence model rather than introduce a separate workflow trace authority. Dependency/service reconciliation may be used internally, but DSH does not become SSSF's outer recovery engine.

## DSH-5 — Richer capabilities

Evaluate compaction, MCP, LSP/code intelligence, code mode, long/background workers, persistent terminal mechanisms and selected plugins/built-ins one at a time. Consult FUT-002 before designing new post-DSH capabilities.

Cordis-Python-derived evaluation requirements become explicit here:

- optional implementations depend on stable capability/service contracts rather than sibling implementation classes where a real replaceable seam exists;
- every mounted/internal capability has one lifecycle owner and reversible cleanup path where possible;
- a new plugin/capability must not expand outer authority;
- runtime composition/effective configuration remains content-addressed and provenance-aware;
- newly visible model tools are separately qualified for visibility, authority and dispatch behavior;
- context compaction changes active projection, never historical evidence;
- background/persistent facilities remain subject to SSSF-owned hard termination and quiescence;
- no capability is promoted merely because Cordis-Python or the Awesome DSH Plugin catalog demonstrates an implementation.

Prefer deep, replaceable internal modules over atomizing trivial helpers into plugins. One concrete implementation does not by itself justify a new architectural seam; require real variation or a distinct reason to change.

## DSH-6 — Product subagents / maker-checker

Use Claude/Codex/DeepSeek product workers only through qualified AgentBackend contracts. Multiple models do not establish review independence by themselves.

A reviewer/checker should receive its own private capability registry and exact review protocol/input identity rather than inheriting the maker's complete tools/context. Same-model self-verification remains optimization, not independent review.

FUT-011/FUT-013 instruction qualification ideas become especially relevant here for operational worker/reviewer prompts.

## DSH-7 — Adaptive inner orchestration

Permit DSH to choose how to spend one fixed execution-cell budget among already admitted refinement/delegation/critic/tool/compaction/candidate actions. It cannot choose its own outer budget or authority.

Adaptive choice is bounded to **admitted action classes and structural delegation edges**. It may not dynamically create a new authority class, widen policy, add an unqualified plugin, create an unbounded recursive worker graph or reinterpret CNO as permission.

Probabilistic verifier observations participate only after their FUT candidates pass qualification.

## DSH-8 — Governed self-evolution

A running immutable generation may propose immutable candidate prompt/skill/workflow/plugin/memory/config generations only after evidence, rollback, security/dependency review, independent review and SSSF-owned promotion are proven. No silent production self-rewrite.

Self-extension occurs in a candidate/disposable workspace with the same capability, evidence and promotion boundaries as any other DSH output. A running generation may propose its successor; it does not authorize the successor.

---

# 9. Downstream unlock map

An unlock means eligible for evaluation, not automatic promotion.

| Proven prerequisite | Newly eligible evaluation |
|---|---|
| Docker-readiness gate | SBX-0/1 and Docker implementation increments |
| SBX-3..6 | real Docker-backed execution/environment integration |
| SBX-7 | DSH-3 parallel children/candidates after DSH activation |
| SBX-8 + BASELINE-PR + immutable pre-DSH freeze | WAYFINDER-1 |
| WAYFINDER-1 | DSH-0A activation eligibility |
| DSH-1 | FUT-007; early FUT-008 schema |
| DSH-2 | FUT-005; serial FUT-006 |
| DSH-3 | parallel FUT-006; hierarchical FUT-008 |
| DSH-5 | selected FUT-002 plugin candidates |
| instruction-heavy stages | FUT-011 promotion opportunities using FUT-013 evidence |
| architecture complexity/drift checkpoints | FUT-009/FUT-010/FUT-012 promotion opportunities |

FUT-008-style identity/provenance fundamentals may influence base cell evidence before FUT-008 itself is promoted. Probabilistic verifier evidence remains advisory and cannot override deterministic FAIL or narrow CNO.

The reviewed Cordis-Python source is a stage-local research input, not an unlock or prerequisite of its own. Reinspect the then-current source and exact Git identity before copying/adapting implementation code or relying on a specific behavior that may have changed after `e610aca184bdd823c96ba76484921f9f40aec68d`.

---

# 10. Qualification discipline

Each activated increment defines as applicable:

1. exact source/build/dependency identities;
2. positive non-vacuity control;
3. watched-red defect controls;
4. failure/CNO behavior;
5. authority-negative controls;
6. interruption/cancellation controls;
7. quiescence/cleanup controls;
8. source/workspace integrity;
9. VerificationContract applicability/evidence bindings;
10. real-seam proof where the property concerns a real seam;
11. reviewer-protocol/assignment binding where semantic review is required;
12. security/effect/network controls;
13. resource/time/token/cost accounting where observable;
14. rollback/retirement;
15. baseline/net-complexity comparison;
16. exact-head review, landing authorization and post-merge proof under policy;
17. effective runtime/config/policy/instruction full-digest identity where DSH behavior depends on composition;
18. capability-availability versus execution-authority separation;
19. model-visible schema filtering plus dispatch-time authority recheck where model tools are involved;
20. explicit inner parent/child lineage rather than temporal inference;
21. lifecycle ownership for reversible inner resources plus recorded cleanup failures;
22. durable-history versus active-context-projection separation for compaction/checkpoint features;
23. typed inner-unit terminal manifest/evidence completeness;
24. external SSSF/process/Docker quiescence proof independent of DSH cooperative cleanup;
25. structural delegation-depth/edge controls where children are admitted;
26. deterministic loop/retry controls before semantic monitoring when the property is mechanically enforceable.

A changed shared contract requalifies materially affected consumers. Old exact-head evidence never transfers by assertion.

## Non-goals

Do not:

- block Docker on retiring exe.dev availability;
- renew/add paid sandbox service without Captain authority;
- make Docker, DSH, a model or a provider the outer SSSF authority;
- conflate AgentBackend with SandboxProvider;
- expose canonical host checkout or host auth homes to sandbox workers;
- create provider-owned recovery policy;
- create a second process supervisor or second authoritative trace DB when owners already exist;
- let a reviewer/model discover its own acceptance obligations;
- treat Browser Sol prose approval as timeless landing permission;
- hide multiple inner operations behind one opaque event;
- make Wayfinder a second planning/state authority;
- replace the Captain's existing Wayfinder with the Matt Pocock research implementation;
- implement DSH plugins/verifier candidates before their gates;
- implement self-evolution before immutable promotion/rollback is proven;
- ask the Engineer for facts the system can establish;
- ask an Agent to own a deterministic state transition that Code can own;
- expose Cordis `Context`/`Fiber`/`Service`/`Effect`/plugin vocabulary as SSSF architecture merely because DSH uses it internally;
- treat a mounted capability/plugin/resource as execution authority;
- rely on model-visible tool hiding without a dispatch-time authority check;
- infer authoritative worker parentage from mutable last-seen/session timing when explicit identity can be carried;
- rewrite durable history because the active model projection was compacted;
- accept immediate-child `process.kill()`, an internal `close()`/dispose result or an empty child registry as proof of process/environment quiescence;
- allow a DSH/Cordis internal Git commit/branch operation to become SSSF promotion or landing authority;
- adopt a Cordis-Python implementation merely because the reference repository contains it without fresh exact-source/security/qualification review.
