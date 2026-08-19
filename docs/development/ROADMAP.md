# Post-Baseline Roadmap

This is the sequencing index for post-baseline SSSF evolution. Detailed sandbox and DSH contracts live in [`SANDBOX_DSH_IMPLEMENTATION_PLAN.md`](SANDBOX_DSH_IMPLEMENTATION_PLAN.md).

Planning-state semantics are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). A roadmap item may be `SEQUENCED` without being `ACTIVE`; implementation begins only when a named increment crosses the activation boundary under the increment protocol.

## B1 — Baseline archive + documentation discovery

Goal: complete the original B0 freeze and make `docs/README.md` a first-class agent entrypoint.

Acceptance:

- B0 evidence/teardown complete;
- immutable proof identity exists;
- fresh agents are routed through the docs index;
- documentation discovery does not alter execution behavior.

## B2 — Canonical repository and source custody

Goal: ensure every sandbox executes the SSSF source actually being evolved.

Acceptance:

- canonical and upstream remote roles are explicit;
- exact repository + commit identity is recorded;
- guest source is gated against the requested identity;
- mutable branch names are never source authority.

## B3 — Windows host portability

Goal: make the supported Windows/WSL operator path reproducible from a genuinely fresh host state.

Acceptance includes line-ending, bootstrap/doctor, source, observability, lifecycle and teardown behavior without transient source edits. Any still-unobservable dimension remains CNO rather than being rounded into PASS.

## B4 — Pre-Docker deterministic execution and acceptance substrate

Goal: finish the reference SSSF so sandbox replacement does not have to invent execution, review, or landing semantics.

The stable pre-Docker baseline must establish **orthogonal execution seams**:

### AgentBackend

`AgentBackend` owns how one bounded reasoning assignment is invoked. Its SSSF-owned contract is equivalent to:

- `execute(PhaseWorkEnvelope) -> PhaseExecutionResult`;
- `cancel(attempt_id)`;
- `attest_binding()`;
- `inspect_usage()`;
- `verify_quiescence()`.

Backend identity must expose the SSSF-observable binding facts required by policy: backend/product, model, profile/effort where observable or enforceable, exact supplied protocol/input identity, attempt identity, terminal result, usage source, and quiescence. Host-native Codex/Claude product authentication remains host-custodied when moving it into a guest would change the identity being qualified.

The merged B4-002 subprocess-supervisor substrate (or its accepted successor) supplies the common process vocabulary: typed argv, closed stdin, bounded output, timeout/cancellation, attempt accounting, descendant cleanup, three-valued terminal observation, and quiescence. Do not create a second process supervisor for Docker or DSH.

### Typed CommandSpec

Any provider/backend command identity used as authority must bind at least argv, cwd, environment references, timeout, stdin mode, stdout/stderr policy, and expected-exit semantics. Unstructured shell text is not the authoritative command identity.

### Verification and review substrate

Before the stable pre-Docker freeze, acceptance-critical claims must be machine-discoverable rather than reconstructed from prose.

Required contract family:

- `verification-contract/v1` (or equivalent project-owned ProofObligation registry);
- `review-envelope/v1`;
- `semantic-review-result/v1`;
- `ruling-envelope/v1`;
- `landing-authorization/v1`.

Required laws:

- deterministic code maps exact changed surfaces/scope to required VerificationContracts and risk profiles;
- required verifier absence, staleness, skip, CNO-under-PASS-policy, wrong-head evidence, or missing required red calibration is non-PASS;
- fixture/calibration evidence is distinct from real-seam proof for OS/GitHub/runtime/custody/cancellation/teardown properties;
- semantic review binds the exact reviewer role/backend and exact reviewer-protocol bytes/digest before launch; the reviewer does not discover its own governing skill;
- maker/reviewer assignment independence is explicit;
- ReviewEnvelope and review/ruling artifacts are exact-head/tree/content-addressed and carry causal invalidation dependencies;
- candidate/base/contract/verifier/reviewer-policy movement invalidates only the affected downstream artifacts and re-enters the earliest correct review state;
- Browser Sol request/ruling transport is typed and correlated to one ReviewEnvelope identity;
- an applicable ruling does not itself become an indefinitely reusable PASS: deterministic code mints a one-use LandingAuthorization only after all local requirements are satisfied;
- immediately before landing, mutation-time applicability is rechecked; any bound movement destroys the authorization;
- exact resulting `main` receives post-merge proof before disposition.

The review-cycle state machine is code-owned:

```text
CANDIDATE_READY
→ DETERMINISTIC_REVIEW_PREFLIGHT
→ SEMANTIC_REVIEW
→ BROWSER_SOL_REQUESTED (when policy requires)
→ RULING_RECEIVED
→ LANDING_AUTHORIZED
→ MUTATION_TIME_RECHECK
→ LAND
→ POST_MERGE_EXACT_MAIN_PROOF
→ DISPOSITION
```

### Pre-Docker freeze checkpoint

Before Docker provider implementation begins, the reference baseline must truthfully demonstrate:

- separate AgentBackend and SandboxProvider laws;
- exact source repository + commit + tree authority;
- typed execution/process ownership and quiescence;
- first-class VerificationContracts and deterministic applicability;
- deterministically bound semantic-review protocol;
- typed review/ruling transport and one-use landing authorization;
- one real ordinary PR traversing the full accepted cycle without Captain transport;
- no unresolved known SSSF defect hidden as CNO/PASS.

A genuine external dependency may remain CNO if the governing acceptance policy permits the freeze to retain it; it may not be silently narrowed.

## B5 — SandboxProvider contract

Goal: extract and prove the semantic execution-environment contract currently supplied by exe.dev before replacing it.

`SandboxProvider` is distinct from `AgentBackend`. It reports environment/provider facts and performs bounded environment operations; SSSF code owns workflow sequencing, retry/recovery decisions, acceptance and promotion.

Required sequence:

1. **SBX-0 — reference semantics inventory:** classify every current lifecycle/provider fact as required semantic, provider-specific mechanism, limitation, or obsolete artifact.
2. **SBX-1 — SandboxProvider + lifecycle-state contract:** define typed provider operations and state, including typed `exec(CommandSpec)` and `reconcile` (provider reports actual state; SSSF decides recovery).
3. **SBX-2 — ExeDevProvider reference conformance:** refactor already-proven exe.dev behavior behind the interface without semantic weakening and run the complete provider-neutral conformance suite.

The provider contract must cover at least:

- `create(spec)`;
- typed `exec(CommandSpec)`;
- source/copy-in/copy-out as required;
- `inspect`;
- artifact/evidence collection;
- Git export/harvest;
- process inspection and `wait_quiescent`;
- stop;
- destroy with explicit authorization;
- `reconcile`.

Acceptance:

- fake-provider controls exercise every contract branch including failure/CNO;
- ExeDevProvider passes the same declared semantics used as the reference oracle;
- lifecycle/retry authority remains in SSSF code;
- meaningful provider drift turns watched-red controls red;
- the contract is sufficient for the later DSH execution environment without containing DSH concepts.

## B6 — Official Docker Sandboxes (`sbx`) implementation candidate

The currently selected replacement candidate is the official Docker Sandboxes `sbx` product. Implementation remains gated by the B4 stable pre-Docker freeze. Read-only feasibility inspection may occur earlier; provider mutation/default-switch work may not.

Required sequence:

1. **SBX-3 — minimal deterministic lifecycle:** exact source → setup → deterministic command → evidence/Git harvest → destroy; no live agent required.
2. **SBX-4 — source/security/credential/network/cognition boundary:** SSSF-owned source broker, minimum mounts, no host control-plane credentials or Docker control socket in guest, explicit network/effect policy, mutable cross-sandbox shared skills disabled for evidence-bearing workers, pinned template/tool identities.
3. **SBX-5 — cancellation/reconciliation/quiescence:** interrupt every lifecycle boundary; identity-bound retry; harvest-before-destroy; typed cleanup uncertainty; provider reports state and SSSF owns recovery.
4. **SBX-6 — observability + identity integration:** join run/provider/source/ADW/process/evidence/harvest/future-cell identities without a second trace authority.
5. **SBX-7 — bounded deterministic concurrency:** SSSF-owned WorkNode DAG, dependency/write/resource locks, admission/backpressure, isolated makers/checkers, independent results and cleanup; first prove two genuinely overlapping sandboxes.
6. **SBX-8 — provider parity/default switch:** compare ExeDevProvider and DockerSbxProvider on shared semantics, prove supported Windows/WSL operation and one real bounded contribution, then and only then switch the default and freeze a post-Docker/pre-DSH baseline.

### Source-broker constitution

Evidence-bearing mutation/review workers must not receive the credential-bearing canonical host checkout. The SSSF-owned source broker creates disposable, credential-free **full Git clones** bound to exact repository + commit + tree. Prefer these full clones over secondary worktrees for Docker worker custody. Canonical host checkout is no-worker-access.

Any Docker-induced Git remote/config mutation is confined to the disposable broker clone. Worker instructions/skills come from the pinned source commit, immutable worker template or another content-addressed SSSF artifact; mutable shared skill inheritance is disabled.

### Parallel scheduler law

Docker supplies isolation only. SSSF owns parallel semantics. A WorkNode must bind at least node identity, dependencies, role, source SHA/tree, expected write set, resource locks, AgentBackend profile, SandboxProvider profile, deterministic gate manifest and acceptance manifest.

A node runs only when dependencies and locks allow it and a qualified target exists. Maximum parallelism, queueing, retry, cancellation, backpressure, deterministic result collection and aggregate acceptance are code-owned. One child FAIL/CNO cannot disappear inside an overall PASS.

Maker/checker isolation requires distinct sandbox, attempt, process/session and evidence-root identity; checker authority comes from original request/spec + exact candidate + deterministic evidence, not hidden maker conversation.

## B7 — Host observability and unattended lifecycle readiness

Goal: make accepted sandbox/ADW state inspectable and recoverable from the Windows host without model narration or a parallel observability authority. Build on SBX-6 and the accepted run/trace owners; read-only inspection must remain distinct from triage/lifecycle mutation.

## B8 — Broader ADW/AgentBackend qualification

Qualify additional roles/backends only as downstream stages require them. Do not block DSH protocol design on roles DSH-0/1 do not need; later product-subagent/maker-checker stages require their applicable backend and review contracts to be independently proven.

## FUT-003 — FirstMate planning-transition awareness

**Planning state: `ACTIVE`, not `PROVEN`.**

Governing architecture: `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`.

Split implementation:

1. `FP-001` — SSSF typed planning-event producer.
2. `FM-FP-001` — FirstMate consumer through the existing authenticated custom-check/watch path.

Current acceptance boundary:

- producer/foundation remain isolated draft candidates under PRE_CERTIFICATION;
- FirstMate consumer must match the exact current producer wire contract, rebase/requalify against current FirstMate main, and publish exact-head attestation;
- initial synchronization is non-actionable;
- all non-`ACTIVE` transitions are awareness-only;
- `ACTIVE` is ordinary-intake eligibility, not direct execution authority;
- live enablement waits for accepted producer/foundation identities plus cross-repository exact-head compatibility and rollback proof.

`FUT-003` becomes `PROVEN` only after accepted immutable producer and consumer identities, exact compatibility, retained evidence, applicable independent review, safe live enablement and reconciled documentation all agree.

## FUT-001 — Bounded autonomous DSH execution cells

**Planning state: `SEQUENCED`, not `ACTIVE`.**

Governing architecture: `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md` plus [`SANDBOX_DSH_IMPLEMENTATION_PLAN.md`](SANDBOX_DSH_IMPLEMENTATION_PLAN.md).

Target:

```text
SSSF deterministic outer graph
        ↓
qualified AgentBackend + proven SandboxProvider environment
        ↓
bounded DSH execution cell
        ↓
SSSF VerificationContracts / semantic review / acceptance
        ↓
one-use landing + exact-main proof
```

DSH does not become a second model-transport authority. A cell selects/uses only AgentBackend profiles already authorized by the outer SSSF policy; DSH may coordinate within the cell but cannot redefine backend binding, source authority, budgets, required verification, acceptance or promotion.

### DSH-0A — protocol + mock executor

Define/prove `ExecutionCellRequest` / `ExecutionCellResult`, identity, authority-negative controls, budgets, result/evidence schema, cancellation and CNO with a deterministic mock. This earns protocol proof only. It is not part of the Docker commission and does not activate real DSH.

### DSH-0B — real sandbox custody seam

After SBX acceptance, run the mock cell through the accepted SandboxProvider + AgentBackend/process-owner path. Prove source/workspace custody, external budget enforcement, timeout/cancel, evidence survival, Git harvest without promotion authority and zero surviving processes/children.

### DSH-1 — real multi-turn single-agent cell

Admit one exact DSH build plus one qualified backend/model profile. Exclude subagents, autonomous refinement, workflows, plugins and self-evolution. Prove identity, bounded tools/effects, evidence/usage, hard termination/quiescence and deterministic SSSF verification; compare against the pre-DSH baseline.

### DSH-2 — bounded autonomous refinement

Qualify internal repair/refinement inside one SSSF outer attempt with externally fixed iteration/time/token/cost ceilings. Measure actual acceptance value over DSH-1.

**Unlock only:** FUT-005 and serial FUT-006 become eligible for formal evaluation.

### DSH-3 — child/subagent lineage + parallelism

Requires SBX-7. Qualify one child, serial children, then parallel children. Prove equal-or-narrower authority, parent/child evidence lineage, aggregate budgets, cancellation propagation and quiescence.

**Unlock:** parallel FUT-006 and governed hierarchical FUT-008 evaluation.

### DSH-4 — inner workflows/goals

Qualify DSH workflows and goal-driven inner graphs while preserving one outer SSSF attempt. Inner graphs cannot create outer attempts, advance phases, change budgets, decide acceptance or promote/land.

### DSH-5 — richer capabilities

Evaluate compaction, MCP, LSP/code intelligence, code mode, long/background workers, persistent terminal mechanisms and selected plugin/built-in capabilities one at a time. Consult the preserved Awesome DSH Plugin research source before designing a new post-DSH capability.

### DSH-6 — product subagents / maker-checker boundaries

Use Claude/Codex/DeepSeek product workers only after their AgentBackend contracts are independently qualified. DSH calling multiple models is not itself proof of reviewer independence; SSSF review policy and reviewer-protocol binding remain authoritative.

### DSH-7 — adaptive inner orchestration

Permit DSH to choose how to spend a fixed cell budget across admitted refinement/delegation/critic/tool/compaction/candidate actions. It cannot enlarge the budget or outer authority.

### DSH-8 — governed self-evolution

Only after immutable generation identity, evidence, rollback, independent review and promotion contracts are proven may a running generation propose immutable candidate generations for isolated SSSF qualification. No silent self-rewrite of production authority.

## DSH downstream unlocks

An unlock means **eligible for evaluation**, never automatic promotion:

- DSH-1 → FUT-007 + early FUT-008 schema evaluation;
- DSH-2 → FUT-005 + serial FUT-006;
- DSH-3 → parallel FUT-006 + hierarchical FUT-008;
- DSH-5 → selected Awesome DSH Plugin candidates, one at a time;
- later evolution prerequisites → governed self-evolution candidates.

Probabilistic verifier output remains advisory inner-cell evidence. It cannot override deterministic `FAIL` or narrow `COULD_NOT_OBSERVE`.

## Long-range admission law

Every sandbox/DSH stage preserves:

- SSSF ownership of outer work graph, applicability, retries, acceptance, landing and terminal state;
- exact source/workspace custody;
- explicit time/resource/token/cost/effect/network ceilings;
- qualified AgentBackend binding and SandboxProvider custody;
- first-class VerificationContracts and risk/applicability compilation;
- maker/checker policy and deterministic reviewer-protocol binding;
- typed ReviewEnvelope/RulingEnvelope/LandingAuthorization invalidation;
- forceable termination and provable quiescence;
- attributable evidence through the shared identity spine;
- exact-main post-merge proof.

Later stages do not activate merely because earlier stages pass. Each stage requires a named increment, exact candidate identity, red-capable controls, real-seam evidence where required, independent review under policy, and measured value over the last accepted baseline.

## Rules

Do not replace exe.dev by editing provider commands everywhere. Inventory semantics → define SandboxProvider → prove ExeDevProvider → implement DockerSbxProvider.

Do not make Docker an orchestrator. Docker owns environment mechanics only; SSSF owns scheduling and recovery.

Do not make DSH the SSSF outer graph or a hidden model proxy. Prove protocol → real custody seam → single-agent value → progressively larger inner autonomy.
