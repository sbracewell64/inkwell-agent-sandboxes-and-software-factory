# Post-Baseline Roadmap

The order below deliberately separates concerns.

Planning-state semantics are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). A roadmap item may be `SEQUENCED` without being `ACTIVE`; activation begins only when a named increment enters the existing increment protocol.

Detailed pre-implementation contracts for the sandbox replacement and DSH live in [`SANDBOX_DSH_IMPLEMENTATION_PLAN.md`](SANDBOX_DSH_IMPLEMENTATION_PLAN.md). This roadmap is the sequencing index; the detailed plan owns stage-level inputs, outputs, proof gates, identities, evidence, failure semantics, and downstream unlocks.

## B1 — Baseline archive + documentation discovery

Goal:

Complete the B0 freeze and make `docs/README.md` a first-class agent entrypoint.

Acceptance:

- B0 harvested/teardown complete,
- immutable tag exists,
- fresh agents are pointed to the docs index,
- no execution behavior changes merely to add documentation discovery.

## B2 — Canonical repository ownership

Goal:

Ensure new sandboxes execute the SSSF source you are actually evolving.

Scope:

- create/use a remote repository you control,
- preserve upstream as a reference remote,
- make the FILL clone URL configurable instead of hard-coded,
- pin proof runs to exact commits.

Acceptance:

fresh sandbox clones the owned source and gate proves guest HEAD equals the requested commit.

## B3 — Windows host portability

Goal:

Turn the ad-hoc Windows compatibility overlay into supported, tested behavior.

Scope:

- CRLF normalization,
- portable temp-file creation,
- SSH first-host behavior,
- persistent PATH/bootstrap,
- host observability without external `sqlite3` if feasible.

Acceptance:

fresh Windows clone -> doctor -> mount -> teardown without manual source editing.

## B4 — Durable local/free agent roster and owned execution substrate

Goal:

Establish model/backend and process-execution contracts that later sandbox and DSH work can consume without inventing new terminal semantics.

This program includes the local/free roster qualification and the provider-neutral executor-supervisor / strict-adapter substrate. Production integration of a strict adapter remains a separate acceptance question; substrate existence is not permission to bypass current ADW semantics.

Acceptance needed by later stages:

- qualified model/backend identities for the roles actually used,
- typed-output correction behavior,
- permission enforcement,
- deterministic test/commit fixture,
- provider-neutral bounded process ownership,
- hard timeout/cancellation and cleanup/quiescence semantics,
- bounded evidence and three-valued terminal observation,
- exact source/build identity for the accepted execution-owner contract.

## B5 — Sandbox provider contract

Goal:

Extract and prove the semantic execution-environment contract currently supplied by exe.dev before replacing it.

Required sequence:

1. **SBX-0 — reference semantics inventory:** classify every current lifecycle/provider fact as required semantic, provider-specific mechanism, limitation, or obsolete artifact.
2. **SBX-1 — provider interface + lifecycle state:** define typed provider-neutral operations/facts while keeping lifecycle sequencing/retries in SSSF code.
3. **SBX-2 — exe.dev reference-adapter conformance:** prove the new contract against the current provider before implementing its replacement.

The provider contract must cover exact source/workspace identity, create/setup/readiness, bounded execution, inspection, exposure, extraction/harvest, credential/effect boundaries, destruction, and observable cleanup.

Acceptance:

- fake-provider controls exercise the complete contract including failure/CNO paths;
- exe.dev passes the provider-neutral conformance suite without moving SSSF workflow authority into the adapter;
- meaningful reference-provider semantic drift turns watched-red controls red;
- the accepted contract is sufficient to express the execution environment later required by DSH.

Do not begin replacement by editing exe.dev commands everywhere.

## B6 — Official Docker Sandboxes (`sbx`) implementation candidate

The currently commissioned replacement candidate is the official Docker Sandboxes `sbx` product, not an unreviewed generic Docker-container wrapper. Implement it only after B5 proves the provider abstraction and the pre-Docker baseline gate is satisfied. If direct feasibility evidence shows that official `sbx` cannot satisfy the accepted contract, record that observation and route the narrow replacement decision through the planning/control process before substituting a different Docker mechanism.

Implementation remains gated by the stable pre-Docker baseline/unattended-PR checkpoint governed through the current baseline commission. Read-only feasibility inspection may occur before that gate; provider mutation/default-switch work may not.

Required sequence:

1. **SBX-3 — minimal deterministic Docker Sandboxes lifecycle:** exact source -> setup -> deterministic command -> evidence/harvest -> destroy, with no live agent required. Use the SSSF-owned source-broker/disposable-clone boundary rather than exposing the canonical host checkout to a worker.
2. **SBX-4 — security/credential/network/effect boundary:** minimum mounts, no host control-plane credentials or Docker control socket in guest, explicit runtime secret/effect/network policy, mutable shared-skill inheritance disabled for evidence-bearing workers, and pinned template/tool identity where the product supports it.
3. **SBX-5 — failure recovery/cancellation/quiescence:** interruption at every lifecycle boundary, identity-bound retry/reconciliation, harvest-before-destroy, typed cleanup uncertainty, and provider state reported to SSSF rather than provider-owned autonomous recovery policy.
4. **SBX-6 — observability + identity integration:** join `run_id`, provider resource, source, ADWs, future execution cells, process outcomes, evidence, and harvest without a second trace authority.
5. **SBX-7 — parallel/resource isolation:** multiple sandboxes without collisions in ports, networks, mounts, workspaces, secrets, evidence, Git harvest, or resource accounting; SSSF deterministic code owns admission, DAG dependencies, write/resource locks, retries, cancellation, backpressure, and result folding.
6. **SBX-8 — portability/conformance/default switch:** compare exe.dev and official Docker Sandboxes on shared semantics, prove the supported Windows/WSL path and one real bounded contribution, then and only then consider changing the default provider and freezing a post-Docker/pre-DSH baseline.

Acceptance must preserve:

- host isolation and explicit mounts,
- disposable/reproducible state,
- exact source custody including repository + commit + tree identity,
- canonical host checkout as no-worker-access for mutation/review workers,
- guest toolchain/readiness,
- no host provisioning/control credential or uncontrolled auth-home material in guest,
- bounded runtime secret/effects,
- application + observability access,
- bounded process execution using the accepted execution-owner vocabulary,
- Git/evidence harvest before irreversible destruction,
- crash recovery/reconciliation,
- forced termination and provable quiescence,
- deterministic cleanup of provider resources,
- independent maker/checker sandbox/evidence identity where review policy requires it.

## B7 — Host observability and unattended lifecycle readiness

Goal:

Make accepted sandbox/ADW state reliably inspectable and recoverable from the Windows host without model narration and without creating a parallel observability authority.

Build on SBX-6 rather than duplicating it. This stage proves the supervisory/operator behavior around the accepted trace/run-record facts: recovery after supervisor restart, bounded readback, clear CNO when state cannot be observed, and no mutation from read-only inspection.

## B8 — Broader ADW/agent qualification

Qualify scout/reviewer/documenter and additional ADWs with explicit fixtures as needed by downstream use.

Do not block DSH protocol work on roles DSH-0/1 do not need. Product-subagent and maker/checker stages later require the relevant backend/role contracts to be independently known.

## FUT-003 — FirstMate planning-transition awareness

**Planning state: `ACTIVE`.**

Architecture is governed by `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`.

Purpose:

remove routine Captain relay between Browser-Sol-managed SSSF planning promotions and FirstMate without allowing planning prose to become execution authority.

Implementation is split so each side can be proved and rolled back independently:

1. `FP-001` — SSSF producer: append-only typed planning-event feed, bootstrap snapshot, deterministic validator, exact planning-source provenance, and retained evidence.
2. `FM-FP-001` — FirstMate consumer: one authenticated custom-check adapter on the existing `fm-watch` cadence, private offset/prefix-hash cursor, ordered deduplicated handling, and mechanical state classification.

Required ordering:

```text
ADR-0005 / planning lifecycle
        -> FP-001 producer contract + validator
        -> FM-FP-001 consumer against producer fixtures
        -> rebase each side onto its settled acceptance surface
        -> independent validation/review
        -> live enablement
        -> PROVEN only after accepted immutable source identities agree
```

The producer may be implemented while other SSSF PRE_CERTIFICATION work remains open, but it must not merge or claim trusted-system status in violation of those constraints.

The consumer may be implemented while FirstMate watcher-related work remains open, but it must not be enabled against the production planning source until it has been rebased and requalified against the settled watcher/test surface.

Bootstrap rule:

- the first `PLANNING_EVENTS.jsonl` record is a non-actionable synchronization snapshot;
- it establishes the initial cursor/current planning states and cannot create work;
- later records are ordered transitions whose `source_commit` points to the already-existing authoritative planning commit;
- only a later `to: ACTIVE` transition is eligible for normal FirstMate intake, and even then the named increment/docs must be fetched and admitted normally.

Acceptance for `FP-001`:

- valid feed passes non-vacuously;
- malformed JSON, duplicate IDs, illegal state edges, invalid paths, missing full commit identity, and invalid `ACTIVE` bindings fail closed;
- bootstrap snapshot is unique and mechanically non-actionable;
- historical feed replacement/truncation is detectable by the consumer continuity contract.

Acceptance for `FM-FP-001`:

- no new event means silence;
- registered-check tampering is rejected by existing trust machinery;
- offset/prefix mismatch refuses without cursor advancement;
- duplicate/malformed/stale events cannot create duplicate or stale effects;
- all non-`ACTIVE` states are awareness-only;
- bootstrap synchronization creates no work;
- `ACTIVE` is intake eligibility, not direct execution authority;
- retirement of the check/cursor restores the pre-bridge behavior without modifying SSSF planning truth.

## FUT-001 — Bounded autonomous DSH execution cells

**Planning state: `SEQUENCED`, not `ACTIVE`.**

The governing architecture is `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`; stage-level contracts are in [`SANDBOX_DSH_IMPLEMENTATION_PLAN.md`](SANDBOX_DSH_IMPLEMENTATION_PLAN.md).

Target:

```text
SSSF deterministic outer graph
        -> proven sandbox execution environment
        -> bounded autonomous DSH execution cell
        -> deterministic SSSF verification / independent review / acceptance
```

### Preconditions for real DSH

Production-value DSH execution requires:

1. deterministic SSSF real-work acceptance/landing baseline;
2. accepted sandbox execution-environment contract and official Docker Sandboxes custody path (or an explicitly re-decided equivalent after failed feasibility);
3. accepted execution-owner terminal/cancellation/quiescence contract (B4-002 or successor);
4. exact source/workspace and mutation/permission custody;
5. typed evidence/three-valued observation;
6. required backend/model identities qualified for the stage being exercised.

Mock protocol work may start earlier; real DSH claims may not.

### DSH-0A — Protocol + mock executor

Define and prove `ExecutionCellRequest` / `ExecutionCellResult`, identity propagation, budgets, authority-negative controls, result/evidence contract, cancellation semantics, and CNO handling with a deterministic mock.

This can precede final Docker qualification and earns **protocol proof only**. It is a separate future increment/commission from the sandbox migration; DSH work is not implicitly authorized inside the current Docker commission. Activation still requires the planning lifecycle to move the named DSH-0A increment to `ACTIVE` after its upstream contracts are stable enough to bind.

### DSH-0B — Real sandbox execution-cell custody

Run the mock cell through the accepted sandbox and execution-owner path. Prove source/workspace custody, external budget enforcement, timeout/cancel, evidence survival, Git harvest without promotion authority, and zero surviving processes/children.

Do not skip this seam proof.

### DSH-1 — Real multi-turn single-agent cell

Admit one exact DSH build plus one qualified backend/model. Exclude subagents, autonomous refinement, workflows, plugins, and self-evolution. Prove identity, bounded tools/effects, usage/evidence, hard termination/quiescence, and deterministic SSSF verification. Compare against the pre-DSH baseline.

### DSH-2 — Bounded autonomous refinement

Qualify internal iteration/Ralph-style repair inside one SSSF outer attempt with externally fixed iteration/time/token/cost ceilings. Measure actual deterministic acceptance value over DSH-1.

**Unlock, not automatic promotion:** FUT-005 and serial FUT-006 become eligible for formal evaluation.

### DSH-3 — Child/subagent lineage + parallelism

Qualify one child, then serial children, then parallel children. Requires SBX-7. Prove parent/child lineage, equal-or-narrower authority, aggregate budgets, cancellation propagation, attributable evidence, and quiescence.

**Unlock:** parallel FUT-006 and production-grade hierarchical FUT-008 evaluation become eligible.

### DSH-4 — Inner workflows and goals

Qualify DSH workflows/goal-driven execution while preserving one outer attempt and denying outer graph, retry, acceptance, promotion, or budget authority.

### DSH-5 — Richer capabilities

Evaluate compaction, MCP, LSP/code intelligence, code mode, long/background workers, persistent terminal mechanisms, and selected plugin/built-in capabilities one at a time. Consult the preserved Awesome DSH Plugin catalog before designing a new post-DSH harness capability.

### DSH-6 — Product subagents and maker/checker boundaries

Qualify Claude/Codex/DeepSeek product workers only after the applicable execution contracts are independently known. Same-model self-verification is optimization, not independent review; SSSF owns the independence policy.

### DSH-7 — Adaptive inner orchestration

Permit DSH to choose how to spend a fixed cell budget across admitted refinement/delegation/critic/tool/compaction/candidate actions. DSH still cannot enlarge its budget or outer authority.

### DSH-8 — Governed self-evolution

Only after identity/evidence/rollback/promotion contracts are proven, permit immutable running generations to propose immutable candidate generations for isolated SSSF-owned qualification and promotion/rejection. No silent self-rewrite of production authority.

## DSH downstream candidate gating

An unlock makes a candidate eligible for evaluation only:

- DSH-1: FUT-007 and early FUT-008 evidence-schema evaluation;
- DSH-2: FUT-005 and serial FUT-006;
- DSH-3: parallel FUT-006 and governed hierarchical FUT-008;
- DSH-5: selected Awesome DSH Plugin catalog capabilities, one at a time;
- later governed-evolution prerequisites: self-evolution candidates.

Production use of probabilistic-verifier candidates requires a qualified governed verifier-evidence substrate. Probabilistic scores remain advisory and cannot override deterministic `FAIL` or narrow `COULD_NOT_OBSERVE`.

## Long-range admission rule

Every sandbox/DSH stage must preserve:

- SSSF ownership of outer work graph and terminal state;
- source/workspace custody;
- external resource/time/token/cost ceilings;
- explicit external-effect/network policy;
- deterministic verification and acceptance;
- maker/checker policy;
- commit/promotion authority outside DSH;
- forceable termination and provable quiescence;
- attributable evidence using the shared identity spine rather than hidden model-proxy activity.

Later stages do not automatically activate because earlier stages pass. Each stage must show measured value relative to the last qualified baseline and pass normal candidate/increment evidence gates.

## Rule

Do not begin the sandbox replacement by editing exe.dev commands everywhere. First inventory semantics, define the provider contract, prove it against exe.dev, then implement the currently selected official Docker Sandboxes `sbx` candidate.

Do not begin production DSH adoption by replacing the SSSF outer graph. Prove the execution-cell protocol, then custody in the real sandbox, then progressively increase inner autonomy as evidence permits.
