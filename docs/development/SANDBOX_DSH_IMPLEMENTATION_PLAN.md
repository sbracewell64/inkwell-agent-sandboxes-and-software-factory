# Sandbox → DSH Pre-Implementation Plan

## Status and authority

- **Planning status:** `SEQUENCED`, not `ACTIVE`.
- **Sandbox sequence:** B5/B6 in `ROADMAP.md`.
- **DSH sequence:** FUT-001 under `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`.
- **Activation boundary:** a named increment under `docs/development/INCREMENT_PROTOCOL.md`.
- **Purpose:** own the detailed execution contracts, stage gates, evidence requirements and exact sandbox→DSH seam behind the concise roadmap.

This file does not claim that Docker or DSH is implemented. It is the pre-implementation specification.

## Governing chain

```text
Engineer intent / typed work
        ↓
SSSF deterministic outer graph
        ↓
qualified AgentBackend + proven SandboxProvider
        ↓
bounded DSH execution cell
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

The constitutional split is fixed:

> **SSSF code owns outer sequencing, applicability, source custody, budgets, retries, verification, reviewer policy, acceptance, landing/promotion, recovery decisions and terminal state. Agents/DSH own reasoning only inside explicitly authorized execution domains.**

Docker is an execution boundary, not an orchestrator. DSH is an inner execution coordinator, not the SSSF outer workflow engine.

---

# 1. Required pre-Docker substrate

Docker implementation must not begin until the stable reference SSSF has enough deterministic machinery to compare a replacement against known semantics.

## 1.1 AgentBackend and SandboxProvider are orthogonal

Do not combine model execution and environment custody into one abstraction.

### AgentBackend

`AgentBackend` answers: **how does one bounded reasoning assignment execute?**

The SSSF-owned semantic contract is equivalent to:

```text
execute(PhaseWorkEnvelope) -> PhaseExecutionResult
cancel(attempt_id)
attest_binding()
inspect_usage()
verify_quiescence()
```

A backend binding must expose every policy-relevant fact SSSF can actually observe or enforce, including as applicable:

- product/harness/backend identity;
- exact model identity;
- profile/effort identity or explicit CNO;
- attempt/session/process identity;
- exact supplied protocol/input identity;
- tool/capability boundary;
- terminal outcome;
- usage/cost source;
- cancellation and quiescence evidence.

Candidate implementations may include PiBackend, ClaudeProductBackend and CodexProductBackend. Host-native product CLIs remain host-custodied when their subscription/auth/settings identity depends on the host environment; moving such a product into a guest is a new binding, not equivalent execution by assumption.

### SandboxProvider

`SandboxProvider` answers: **what isolated execution world exists, and what is its observed state?**

It owns environment/provider mechanics only. It does not own lifecycle policy, retries, recovery choice, acceptance or promotion.

The target semantic surface is equivalent to:

```text
create(SandboxSpec)
exec(CommandSpec)
copy_in / copy_out       # only when the accepted source/evidence model needs them
inspect()
collect_artifacts()
export_git()
inspect_processes()
wait_quiescent()
stop()
destroy(authorization)
reconcile()
```

Use `reconcile`, not provider-owned autonomous `recover`: the provider reports actual state; SSSF code decides the next legal recovery action.

## 1.2 CommandSpec is typed authority

Any executable command relied upon as evidence binds at least:

- argv;
- cwd;
- environment references/allowlist;
- timeout;
- stdin mode;
- stdout/stderr policy and bounds;
- expected exit semantics;
- execution/attempt identity.

Unstructured shell prose is not authoritative command identity.

The B4-002 subprocess-supervisor substrate or its accepted successor owns the common process vocabulary: shell-free launch, closed stdin, bounded streams, monotonic timeout/cancellation, attempt accounting, descendant cleanup, typed three-valued terminal observation and quiescence. Docker and DSH must reuse/conform to that owner rather than create parallel supervisors.

## 1.3 Source authority and Source Broker

Source authority is:

```text
repository URL + exact commit SHA + exact tree SHA
```

A branch is convenience state only.

Evidence-bearing mutation/review workers never receive the credential-bearing canonical host checkout. The SSSF-owned **Source Broker** produces disposable, credential-free **full Git clones** at exact source identity. Prefer full clones over secondary worktrees for Docker worker custody.

Rules:

- canonical host checkout is no-worker-access;
- broker clone is clean at exact head/tree before use;
- ignored host secrets/config are not copied into the clone;
- Docker/worker remote/config mutations remain confined to the broker clone;
- broker clone persists until all export/evidence obligations are complete, then is disposable;
- any inability to prove clone/source identity is CNO/non-PASS.

## 1.4 Immutable cognition/input boundary

Evidence-bearing workers must not silently inherit mutable cross-sandbox cognition.

Required policy:

- shared mutable skills disabled where the selected provider/product supports such sharing;
- instructions/skills/protocols come from the pinned source commit, immutable worker template or another content-addressed SSSF artifact;
- worker template/toolchain identity is pinned once the mechanism is qualified;
- exact injected reviewer protocol/input bytes are recorded by the backend execution owner.

## 1.5 Verification and review are first-class contracts

Before the pre-Docker freeze, acceptance-critical verifier discovery and review transport must be code-owned.

Contract family:

```text
verification-contract/v1
review-envelope/v1
semantic-review-result/v1
ruling-envelope/v1
landing-authorization/v1
```

Exact names may change only through the normal architecture process; semantics must remain.

### VerificationContract / ProofObligation

Each acceptance-critical claim has one repository-owned contract identifying:

- stable claim/contract ID and version/digest;
- owning subsystem/increment and acceptance dimension;
- applicability inputs;
- required verifier(s);
- required worlds/platforms/real seams;
- positive/non-vacuity evidence;
- red calibration requirements;
- CNO policy;
- evidence locator/digest requirements;
- invalidation dependencies.

Deterministic code compiles exact changed surfaces + declared scope into the required contract set and risk profile. Agents/reviewers cannot choose which required verifiers to omit.

A required verifier that is absent, stale, skipped, wrong-head, unavailable, CNO where PASS is required, or missing required red calibration prevents landing.

### Real-seam law

Fixtures/mocks may calibrate a verifier. They do not prove a real OS/GitHub/runtime/custody boundary when the acceptance property concerns that real seam.

Examples requiring real-seam evidence where applicable:

- subprocess cancellation/quiescence;
- control request/ruling correlation;
- exact-head CI association;
- merge guard behavior;
- credential/environment refusal;
- sandbox/source custody;
- teardown/harvest ordering.

Unavailable required real-seam proof is CNO/non-PASS according to the contract; never substitute fixture success silently.

### Deterministic reviewer protocol binding

Entering semantic review deterministically resolves:

- reviewer role;
- assignment identity and maker separation;
- AgentBackend profile;
- reviewer protocol ID/ref/digest;
- exact protocol bytes or immutable locator;
- exact candidate head/tree;
- review-policy version.

The runner verifies and injects the protocol bytes into the actual reviewer invocation. Missing/mismatched/unreadable protocol means reviewer does not launch and the result is CNO/non-PASS. Model self-report that it read a skill is not proof.

### Typed review transport and causal invalidation

`ReviewEnvelope` compiles deterministic facts and a reviewer-facing claim→evidence index. `SemanticReviewResult` binds the exact envelope/head/tree/reviewer/backend/protocol/policy. Browser Sol transport is typed and correlated to one immutable request identity. `RulingEnvelope` binds the request plus exact candidate/envelope/policy.

Causal invalidation is code-owned:

- candidate head/tree movement invalidates exact-head verifier/review/ruling/landing artifacts;
- material base/applicability/compiler movement invalidates affected downstream artifacts;
- verifier-byte or VerificationContract changes invalidate affected results/calibration;
- reviewer role/backend/protocol/assignment changes invalidate semantic review;
- review-policy movement invalidates affected review/ruling/authorization.

The system re-enters the earliest correct state rather than relying on an agent to notice staleness.

### One-use landing

Browser Sol approval is not an indefinitely reusable PASS. Deterministic code creates a one-use `LandingAuthorization` only after the applicable RulingEnvelope and all local policy requirements are satisfied.

It binds repository/work identity, exact base/head/tree, ReviewEnvelope, RulingEnvelope and policy version. Immediately before mutation, applicability/merge guards re-run. Any movement destroys authorization. Successful landing consumes it exactly once. Exact resulting `main` receives post-merge proof before disposition.

Review cycle:

```text
CANDIDATE_READY
→ DETERMINISTIC_REVIEW_PREFLIGHT
→ SEMANTIC_REVIEW
→ BROWSER_SOL_REQUESTED   # when required
→ RULING_RECEIVED
→ LANDING_AUTHORIZED
→ MUTATION_TIME_RECHECK
→ LAND
→ POST_MERGE_EXACT_MAIN_PROOF
→ DISPOSITION
```

## 1.6 Stable pre-Docker freeze gate

Docker implementation waits until the reference baseline truthfully demonstrates:

1. separate AgentBackend and SandboxProvider seams;
2. typed CommandSpec/process ownership and quiescence;
3. exact repo+commit+tree source authority;
4. source/workspace/mutation custody;
5. first-class VerificationContracts + deterministic applicability;
6. deterministic semantic reviewer-protocol binding;
7. typed ReviewEnvelope/RulingEnvelope transport + causal invalidation;
8. one-use LandingAuthorization + exact-main post-merge proof;
9. one real ordinary engineering PR through the full accepted cycle without Captain transport;
10. no known SSSF defect hidden behind PASS/CNO wording.

A genuine external dependency may remain CNO only if the governing acceptance contract permits the freeze to retain it explicitly.

---

# 2. Shared identity and evidence spine

Do not create a new identity universe for every later feature.

Preferred hierarchy:

```text
run_id
  └─ adw_id
      └─ outer_attempt_id
          └─ execution_cell_id
              └─ inner_unit_id(kind=...)
```

Possible inner-unit kinds include process, model-turn, refinement, subagent, candidate, verifier-call, workflow-node and external-effect unit.

Each relevant unit carries parent identity, timing, authority/budget attribution and evidence refs. Prefer the owning code emitting typed durable facts directly into accepted trace/evidence owners rather than adding a separate monitor that reconstructs activity from prose.

Three-valued observation remains exhaustive: `PASS`/observed-good, `FAIL`/observed-bad, `COULD_NOT_OBSERVE`. Missing state is never implicit success.

---

# 3. Sandbox program

## SBX-0 — Reference semantics inventory

Goal: inventory current exe.dev lifecycle semantics before designing the replacement API.

Classify each lifecycle fact as:

- required provider-neutral semantic;
- provider-specific mechanism;
- current limitation;
- obsolete/historical artifact.

Cover create/resource identity, exact source/fill, setup/readiness, process entry, observe/ports, spend/resource facts, artifacts/Git harvest, runtime-secret lifecycle, state inspection/reconciliation, destroy/post-destroy gate.

**Exit:** complete machine/validator-readable inventory with one owner per fact; no provider command is unaccounted for.

## SBX-1 — SandboxProvider contract

Define the minimum contract described in §1.1, including `SandboxSpec`, `CommandSpec`, returned fact types, idempotency, retry safety, irreversibility, durable-state owner, failure classes and CNO conditions.

`SandboxSpec` binds at least run/attempt identity, source repo/commit/tree, role/execution profile, clone/workspace mode, resource bounds, immutable template identity, network-policy identity, secret references, shared-skills policy and evidence root.

**Exit:** deterministic fake provider exercises every success/failure/CNO branch without exe.dev or Docker.

## SBX-2 — ExeDevProvider conformance

Refactor proven exe.dev behavior behind the provider interface without semantic change.

Prove source gates, credential boundary, lifecycle ordering, readiness/exposure, harvest-before-destroy, typed errors/CNO and SSSF-owned recovery/sequence.

**Exit:** reference provider passes provider-neutral conformance; watched-red semantic drift is detected.

## SBX-3 — Minimal DockerSbxProvider lifecycle

Use official Docker Sandboxes `sbx` unless direct feasibility evidence causes a separately ruled replacement.

First fixture is deterministic code only:

```text
create
→ broker exact source clone
→ setup/readiness
→ exec(CommandSpec)
→ bounded evidence
→ known artifact/Git export
→ quiescence
→ destroy
→ authoritative residual-state check
```

No live coding agent or DSH yet.

**Exit:** exact source, deterministic command/evidence/harvest and authoritative cleanup all proven.

## SBX-4 — Security / credential / network / cognition boundary

Prove:

- source broker + canonical checkout no-worker-access;
- minimum explicit mounts/writes;
- no host provisioning/control credential or auth-home inheritance;
- no uncontrolled Docker socket/control capability in guest;
- runtime secrets explicit/scoped and absent from argv/evidence;
- network/effect policy explicit, versioned/content-addressed where practical;
- shared mutable skill inheritance disabled for evidence-bearing workers;
- immutable worker template/toolchain identity pinned after feasibility.

Missing enforcement/observability is CNO, not permission.

## SBX-5 — Cancellation / reconciliation / quiescence

Interrupt before/after create, source, setup, execution, observe/extract, Git harvest, secret retirement, destroy and post-destroy gate.

Required behavior:

- durable identity lets a later process reconcile what exists;
- retry cannot create silent duplicate resources;
- provider reports state; SSSF decides recovery;
- evidence/harvest obligations precede irreversible destroy;
- cancellation converges on shared execution-owner semantics;
- inability to prove process/provider cleanup is non-clean CNO.

## SBX-6 — Observability + identity integration

Join run/provider/source/ADW/process/evidence/harvest/future-cell identities through accepted run/trace/evidence owners. No second authoritative observability DB for Docker/DSH.

Read-only inspection remains distinct from triage/archive/lifecycle mutation.

## SBX-7 — Deterministic parallelism and reviewer isolation

Represent executable parallel work as SSSF-owned `WorkNode` DAGs binding at least:

- node_id / dependencies;
- role;
- source commit/tree;
- expected write set;
- resource locks;
- AgentBackend profile;
- SandboxProvider profile;
- deterministic-gate manifest;
- acceptance manifest.

Concurrency allowed only when dependency/write/resource constraints permit and a qualified target exists. SSSF owns max parallelism, queueing, admission, retry, cancellation, backpressure, collection order and aggregate result folding.

Prove two genuine overlapping sandboxes, peer survival when one FAILs/cancels, duplicate/run-id refusal, capacity backpressure, deterministic collection and complete cleanup.

Maker/checker use distinct sandbox/attempt/session/process/evidence identities. Checker input is original spec + exact candidate + deterministic evidence, not maker hidden conversation.

## SBX-8 — Parity, default switch, pre-DSH freeze

Run the same semantic provider fixtures through ExeDevProvider and DockerSbxProvider. Require contract parity, not identical implementation. Prove supported Windows/WSL path and one real bounded engineering PR through the Docker-backed path without Captain transport.

Only then switch the default/demote exe.dev and freeze an immutable post-Docker/pre-DSH baseline.

---

# 4. Sandbox gate for real DSH

Real DSH needs an accepted environment that proves for the exact candidate:

1. exact source/workspace identity;
2. explicit write/mount scope;
3. typed bounded process execution;
4. timeout/cancel/kill semantics;
5. resource ceilings;
6. explicit network/effect policy;
7. evidence/artifact extraction;
8. durable identity/trace join;
9. Git harvest without promotion authority;
10. forceable termination + provider/process quiescence;
11. qualified AgentBackend binding for the stage;
12. accepted VerificationContract/review/landing substrate.

Mock DSH protocol design can precede this gate. Real DSH value claims cannot.

---

# 5. DSH execution-cell protocol

## ExecutionCellRequest

Minimum semantics:

- execution_cell_id + parent run/adw/outer-attempt identities;
- objective/role;
- exact source/workspace identity;
- selected qualified `agent_backend_profile` and allowed backend set;
- write/tool/capability authority;
- time/resource/token/cost ceilings;
- external-effect/network policy;
- maker/checker policy;
- applicable VerificationContract/review-policy references;
- evidence contract;
- expected result schema;
- cancellation identity.

DSH may spend within externally fixed authority/budgets. It cannot enlarge them or redefine the backend binding.

## ExecutionCellResult

Return observed facts, never SSSF acceptance authority:

- exact cell/parent identities;
- terminal state/reason;
- typed result/envelope;
- source/workspace/mutation facts as applicable;
- AgentBackend execution/binding evidence;
- usage/cost observations + source;
- child/inner-unit summary;
- evidence refs/digests;
- external-effect observations;
- cancellation/timeout facts;
- cleanup/quiescence evidence;
- CNO reasons.

DSH never returns authoritative `accepted=true`. SSSF re-derives verification/review/acceptance.

---

# 6. DSH qualification sequence

## DSH-0A — Protocol + deterministic mock

Prove request/result identity, authority rejection, budgets, result schema, wrong/stale source refusal, no commit/promotion/outer-graph authority, typed CNO, evidence attribution and cancellation semantics.

This is protocol proof only and is not implicit authority to begin DSH inside the Docker commission.

## DSH-0B — Real sandbox custody seam

Run the mock through accepted SandboxProvider + AgentBackend/process-owner path. Prove identity joins, external budget enforcement, timeout/cancel, evidence survival, authorized mutation only, Git harvest without promotion authority and zero surviving children/processes.

Do not skip from schema proof to live autonomous DSH.

## DSH-1 — Real multi-turn single-agent cell

Admit one exact DSH build/dependency identity and one qualified AgentBackend/model profile. Exclude subagents, autonomous refinement, workflows/goals, optional plugins and self-evolution.

Prove bounded tools/effects, source integrity, typed output, usage/evidence, hard timeout/cancel, quiescence and deterministic SSSF verification/review. Compare on the same fixture with the pre-DSH baseline; successful execution alone is not value.

**Unlock:** FUT-007 and early FUT-008 schema evaluation become eligible.

## DSH-2 — Bounded autonomous refinement

Permit internal repair/refinement inside one outer attempt with externally fixed iteration/time/token/cost ceilings. Measure deterministic acceptance, first-result acceptance, inner repair burden, outer retries, latency/cost/defects and reviewer burden versus DSH-1.

**Unlock:** FUT-005 and serial FUT-006.

## DSH-3 — Child/subagent lineage + parallelism

Requires SBX-7. Qualify one child, serial children, then parallel children. Every child gets equal-or-narrower authority; aggregate budget is externally enforced. Prove lineage, per-child binding/evidence, cancellation propagation and quiescence.

**Unlock:** parallel FUT-006 and governed hierarchical FUT-008.

## DSH-4 — Inner workflows/goals

Qualify inner DSH workflows/goal graphs as descendants of one SSSF outer attempt. They cannot create/advance outer attempts/phases, alter budgets, decide acceptance or land/promote.

## DSH-5 — Richer capabilities

Evaluate compaction, MCP, LSP/code intelligence, code mode, long/background workers, persistent terminal mechanisms and selected plugins/built-ins one at a time. Consult the preserved Awesome DSH Plugin research source before designing new post-DSH capability.

Each candidate requires exact source/dependencies, authority containment, cancellation/quiescence, evidence attribution, resource/effect boundaries, measured net value and rollback.

## DSH-6 — Product subagents / maker-checker

Use Claude/Codex/DeepSeek product workers only through qualified AgentBackend contracts. DSH calling multiple models does not establish review independence; SSSF reviewer policy, assignment identity and exact reviewer-protocol binding remain authoritative.

Same-model self-verification is optimization, not independent review.

## DSH-7 — Adaptive inner orchestration

Permit DSH to choose how to spend a fixed cell budget among admitted refinement/delegation/critic/tool/compaction/candidate actions. It cannot choose its budget, backend authority or outer authority.

Probabilistic-verifier observations participate only after their FUT candidates independently pass qualification.

## DSH-8 — Governed self-evolution

After immutable generation identity, evidence, rollback, security/dependency review, independent review and SSSF-owned promotion are proven, a running generation may propose immutable candidate generations. No production generation silently rewrites its own prompt/skill/workflow/plugin/memory/config authority.

---

# 7. Downstream unlock map

An unlock means eligible for formal evaluation, not `DECIDED`, `SEQUENCED` or `ACTIVE`.

| Proven prerequisite | Newly eligible evaluation |
|---|---|
| SBX-0..2 | Docker provider implementation |
| SBX-3..6 + accepted pre-Docker review substrate | DSH-0B custody after DSH activation |
| SBX-7 | DSH-3 parallel children/candidates |
| DSH-0A | execution-cell protocol refinement |
| DSH-1 | FUT-007; early FUT-008 schema |
| DSH-2 | FUT-005; serial FUT-006 |
| DSH-3 | parallel FUT-006; hierarchical FUT-008 |
| DSH-5 | selected Awesome DSH Plugin candidates |
| DSH-8 prerequisites | governed self-evolution candidates |

FUT-008-style identity/provenance fundamentals influence base execution-cell evidence from DSH-0, but FUT-008 itself remains a candidate until evaluated. Probabilistic verifier evidence is advisory and can never override deterministic FAIL or narrow CNO.

---

# 8. Qualification discipline for every stage

Each activated increment defines as applicable:

1. exact source/build/dependency identities;
2. positive non-vacuity control;
3. watched-red defect controls;
4. failure/CNO behavior;
5. authority-negative controls;
6. interruption/cancellation controls;
7. quiescence/cleanup controls;
8. source/workspace integrity;
9. VerificationContract applicability and evidence bindings;
10. real-seam proof where the property concerns a real seam;
11. reviewer-protocol/assignment binding where semantic review is required;
12. security/effect/network controls;
13. resource/time/token/cost accounting where observable;
14. rollback/retirement;
15. baseline/net-complexity comparison;
16. exact-head review, landing authorization and post-merge proof under policy.

A changed shared contract requalifies every materially affected consumer; old exact-head evidence never transfers by assertion.

---

# 9. Activation readiness

## Sandbox

SBX-0/1 can become `ACTIVE` only after the stable pre-Docker baseline gate permits new sandbox work and the named increment has bounded acceptance. Docker provider implementation itself remains blocked until the full B4/pre-Docker freeze checkpoint is satisfied.

Start with semantics/contract/reference conformance, not provider-command replacement.

## DSH

FUT-001 remains `SEQUENCED`, not `ACTIVE`. DSH-0A is a separate future activation from Docker and is not authorized merely because its protocol could be mocked early. Real DSH beyond 0A additionally requires the post-Docker/pre-DSH substrate, accepted SandboxProvider/AgentBackend/review contracts and normal planning activation.

---

# 10. Non-goals

Do not:

- make Herdr, a model, Docker, DSH or a provider the outer SSSF authority;
- conflate AgentBackend with SandboxProvider;
- expose canonical host checkout or host auth homes to mutation/review workers;
- create provider-owned recovery policy;
- create a second process supervisor or second authoritative trace DB when accepted owners already exist;
- let reviewer/model discover its own required protocol/verification obligations;
- treat Browser Sol prose approval as timeless landing permission;
- hide multiple model/verifier operations behind one opaque event;
- implement DSH plugins/verifier candidates before their gates;
- implement self-evolution before immutable promotion/rollback is proven.
