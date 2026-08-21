# Awesome DSH Plugin — Research and Reuse Reference

Status: `PRESERVE`
Planning owner: Browser Sol
Candidate register: `FUT-002`

## Preserved source

Repository: `awesome-dsh-plugin/awesome-dsh-plugin`
Observed catalog head during this review: `399676833a6589fe740d6f1057e676d33621c2af` (2026-08-20)

The catalog is a discovery surface only. Listing proves neither security nor production eligibility. No plugin named here is authorized for installation into a trusted SSSF/FirstMate/DSH profile merely because it appears in the catalog or this document.

Before any candidate is admitted: pin exact source/build/dependency identity; run supply-chain/static review before package hooks; qualify in isolated Docker; run deterministic contract/lifecycle/negative tests; prove cleanup/quiescence; review capabilities/effects/network/credentials; and evaluate semantic utility separately from mechanical correctness. Every upgrade is a new candidate generation.

## Screening conclusion

The catalog is most useful when treated as a library of implementation experiments, not as a roadmap generator. The strongest near-term candidates are small implementations that fit existing DSH stages without taking over SSSF outer authority.

### A — immediate exploration candidates

#### 1. `1052326311/dsh-plan-lattice` — passive/auto continuity only

Reviewed head: `f9e3e245e629d1013e77dc10e67c06a4f1682a14`.

Why it matters:
- auto mode reconstructs approved native plan/Todo/delegated outcomes from the append-only DSH Session log;
- its native continuity projection explicitly avoids becoming a second planner or scheduler;
- Todo state is not incorrectly promoted across turns;
- the project carries unusually strong stale-basis, first-drift, crash/SIGKILL, and negative-result evidence.

Potential route: DSH-2 continuity/compaction resilience.

Constraint: evaluate **auto/passive mode only** first. Full-Lattice contracts/graphs/receipts/leases/gates overlap SSSF-owned workflow/authority and are not adopted by this preservation decision.

#### 2. `apheli0os/deepseek-harness-orchestrate` — static candidate DAG compiler

Reviewed head: `6a1863dfabafa565bf7af160ce60e2749f4bad17`.

Why it matters:
- model emits a bounded task DAG as data;
- code normalizes and validates every node/dependency before execution;
- duplicate IDs, missing/self/duplicate dependencies and cycles fail before any task starts;
- stable Kahn topological layering feeds the existing DSH workflow engine;
- model-authored strings remain data rather than executable orchestration source.

Potential route: DSH-4 first static inner workflow implementation/reference.

Required SSSF extensions before production use: authority/capability checks, read/write/effect/resource conflict semantics, exact source/workspace generation, budgets, output trust classes, failure-folding, and immutable graph-generation identity.

#### 3. `PerryLink/dsh-background-agents` — thin continuable-child layer

Reviewed head: `6be49a39e5a154ac5d79efb2c3990fa55f64882c`.

Why it matters:
- built on official continuable-subagent lifecycle rather than its own process orchestrator;
- child tool filters only remove capabilities; they cannot grant new ones;
- explicit child depth and per-parent child-count ceilings;
- provider/model override can be bound per child;
- status/results reconstruct from durable DSH state; interruption delegates lifecycle ownership to the official continuation manager.

Potential route: DSH-3 bounded long-lived/continuable children.

Initial scope must exclude team rooms, shared task boards and ambient peer messaging. Start with parent → child request/result/interrupt/list semantics and typed child result provenance only.

#### 4. `tancheng33/dsh-code-runtime-container` — inner Code Mode isolation

Reviewed head: `635a7ccd10f74010c4d249170a82cb4366203e1d`.

Why it matters:
- implements DSH's declared but otherwise missing `ctx.codeRuntime` container backend;
- fresh container per code run, no network by default, read-only rootfs, dropped capabilities, no-new-privileges, unprivileged user, CPU/memory/PID/wall/output ceilings;
- no host workspace mount by default; optional workspace mount defaults read-only;
- dispose-to-quiescence kills and awaits all in-flight containers;
- real-container hostile-program and isolation tests exist.

Potential route: DSH-0B inner Code Mode/runtime qualification.

Critical caveat: this cannot replace SSSF's outer Docker/SandboxProvider custody. Do not expose the host Docker socket to an untrusted DSH cell. Before considering literal reuse, determine whether the same isolation contract can run within the SSSF container model without Docker-in-Docker/socket authority. Its threat model and tests are valuable even if the implementation is not reused.

#### 5. `timwhitez/dsh-self-evolving` — DSH-8 only

Reviewed head: `4eb3bb4058dce4330ecbfc2b96e9c2bdabb71677`.

Why it matters:
- treats generated candidates as untrusted;
- proposer sandbox is network/credential constrained;
- deterministic build and one-shot real Loader admission precede evaluation;
- evaluator/scorer/split/model route/safety policy remain outside candidate authority;
- journal-before-external-action plus crash reconciliation;
- provenance pinning, hash-chain lineage, replay controls and explicit non-claims around sealed/SOTA evidence;
- normative safety spec keeps controller, verifier, sealed data, credentials and Docker socket outside candidate reach.

Potential route: DSH-8 governed self-evolution research/candidate implementation.

This is explicitly deferred until DSH-8. It does not authorize self-modification or automatic promotion in current SSSF.

### B — high-value reference implementations, not state/authority owners

#### `bpc-oss/dsh-verification`

Observed head: `1afaf79aceaf02f9d83804a12f4d31e936152377`.

Useful ideas:
- server-minted contract identity and authoritative source-basis hashing;
- model proposals are not authoritative contracts;
- user correction re-bases and invalidates prior evidence;
- missing acceptance verdict is failure; need-human remains blocked;
- server-stamped tool evidence and append-only replay.

Why not adopt as authority: SSSF already owns acceptance. Current strong enforcement also depends on a GoalTransitionGuard seam that has required rc-version reapplication/restoration. Use its code/tests as evidence-contract research; do not create competing acceptance truth.

#### `victorzhong0110/dsh-outcome-loop`

Useful ideas:
- mechanical verification and user disposition are independent axes;
- `unknown`, `stale`, `failed`, `passed`, and conflicting/inconclusive evidence remain distinct;
- infrastructure failure never becomes task failure or success;
- realpath workspace confinement and opt-in active checks;
- structured facts only, with data minimization.

Why not adopt as authority: its outcome ledger would duplicate SSSF canonical evidence/acceptance state. Reuse semantics and tests, not ownership.

#### `february2015/dsh-taskswarm`

Useful ideas:
- dependency waves;
- isolated Git worktree lanes;
- fixed plan after batch start;
- crash salvage and retained lane state;
- independent review and peer-failure containment.

Why not adopt: it is explicitly a project-level orchestrator with its own supervisor, integration branch, state and merger. That competes with FirstMate/SSSF outer workflow authority.

#### `jiezeng2004-design/dsh-requirements-alignment`

Useful idea: a child cannot authorize a direction change; it returns a typed drift candidate and the parent resolves authority. Durable drift decisions survive resume/fork/compaction.

Why not adopt: its sidecar becomes canonical intent state and its default drift protocol routes to the user. SSSF already owns the WorkPackage/requirement ledger and Browser-Sol/Captain authority routing.

#### `fuhefei/dsh-sentinel`

Useful ideas: durable condition watches, lease-owned single duty runner, at-least-once internal wake delivery, explicit pending-wakeup bounds.

Why not adopt now: resident heartbeat/watch ownership belongs to CODE outside the agent; SSSF/FirstMate already have watch/automation surfaces. Use as a condition-wakeup implementation reference only if a bounded DSH inner wait later needs it.

### C — reviewed but not recommended as architecture candidates

- `JohnXu22786/file-planning` / trailmap: clean state machine and tests, but `.trail/map.json` explicitly becomes a second workflow source of truth.
- `Punky971210/dsh-punky-swarm`: useful gate examples, but defaults complex tasks toward a cluster, carries extensive role/document/process choreography, lacks durable resume in its stated scope, and is AGPL-3.0.
- `EvilIrving/dsh-proof`: read-only verifier pattern is useful, but verifier failure/missing structured output degrades to "no objection" (fail-open), and mutable deny lists can miss new mutating tools.
- `PerryLink/dsh-doublecheck`: useful red/green/replay-derived gate ideas, but the full package mixes user interrogation, workflow sequencing, workspace spec/report artifacts and tool-name gate lists that conflict with SSSF ownership.
- `82c86b8z86-stack/dsh-engineering-workflow`: skill-driven five-phase SOP; useful corpus, not runtime authority. It moves requirements questioning, plan approval, TDD sequencing, subagent execution and finishing into a prompt/preset layer.
- `alib8b8/dsh-plugin-aflare`: deterministic YAML workflow/WAL/Saga ideas are interesting, but it introduces an external workflow binary and another workflow authority; AGPL licensing also makes direct dependency less attractive.

## Candidate-qualification toolbox

These are potentially useful earlier than the workflow candidates because they help make third-party plugin evaluation safe and reproducible.

### `iiwish/dsh-testkit`

Reviewed head: `27607d18f9d05ce262be197aa9f74cffbbf59cbd`.

Candidate use: deterministic real-host lifecycle qualification. Packs the plugin, installs beside an exact DSH version in disposable Docker, boots/registers/exercises/uninstalls/reboots and checks residue/repeatability. Unsupported observer/version states remain explicit instead of false pass.

### `BotonJ/dsh-windtunnel`

Reviewed head: `c5b8f9604bca5c6d336d3b5a4ba2f4f26417ead9`.

Candidate use: deterministic contract regression. A scripted LLM adapter drives the real agent/tool/event pipeline without API/network, covering load, schema/render, malformed inputs, cancellation, concurrent re-entry, crash isolation and negative tests. It explicitly does not claim real-model utility.

### `chouyong/dsh-effect-doctor`

Reviewed head: `a138e421fd97bbc55796ef379fc22abcc47d3da2`.

Candidate use: Cordis lifecycle/quiescence evidence. Verifies supported Cordis-managed resources return to baseline after mount/exercise/unmount/settle; unsupported runtime observation surfaces return `UNVERIFIABLE_*` rather than PASS. It does not cover arbitrary JS/native/process leakage, so it complements rather than replaces SSSF process/Docker quiescence proof.

### `Darren-Tang/dsh-provenance`

Reviewed head: `0ccbbfb45b33ee755849ac787f73283dd0f96569`.

Candidate use: pre-install supply-chain provenance. Checks immutable pinning, registry digest, install hooks, available SLSA metadata and source/artifact correspondence before package hooks execute; bounded in-memory archive parsing and allowlisted egress. A comparison that verified nothing is reported as such, never rounded to clean.

### `BiBoyang/dsh-eval-harness`

Candidate use: semantic/behavioral profile regression after deterministic lifecycle checks. Runs real headless agents in isolated per-case workspaces, asserts trace/tool/output/token behavior, compares a reviewed baseline in CI, and uses LLM judging only after structural assertions pass. This is closer to DSH behavior qualification than Testkit/Windtunnel and should be a later layer, not a replacement for deterministic tests.

## Security/capability references worth carrying into DSH

### `sashankh/dsh-taintguard`

Strong corroborating reference for AgentDojo findings. Its own AgentDojo measurement reports content-pattern detection as weak while origin tainting catches the ingress class but is too coarse; unconditional credential-to-egress refusal is the strongest control. Preserve the design lesson: provenance and structural effect mediation matter more than prompt-injection phrase detection. Do not adopt per-agent sticky taint as the final security architecture.

### `leaforbook/dsh-mcp-lazy`

Strong DSH-5 reference for progressive tool-schema disclosure. It hides compatible MCP schemas per session, activates only the needed MCP, and leaves original execution/permissions/lifecycle with the owning MCP. Uncertain compatibility fails open to normal visibility rather than breaking capability. SSSF should preserve the principle but CODE must still retain exact remote/local provenance, credentials, effects and authority.

## Skills review

Skills are candidates only where they encode irreducible semantic judgment. They must not become outer sequencing, retry or acceptance authority.

### Aegis (`GanyuanRan/Aegis`)

Most interesting individual skill: `systematic-debugging`.

Useful semantics:
- reproduce/isolate before repair;
- identify canonical owner rather than patching consumers;
- one hypothesis/falsifier at a time;
- explicit patch-shape and change-necessity analysis;
- minimal repair means smallest sufficient owner-level repair, not smallest textual diff;
- proportional verification and explicit retirement of temporary/fallback paths.

Potential use: DSH-1/2 semantic debugging profile experiment, preferably simplified and qualified against a no-skill baseline. Do not install the whole Aegis methodology as another workflow layer.

Other Aegis skills worth later isolated comparison: `first-principles-review`, `anti-entropy-governance`, `receiving-code-review` / `requesting-code-review`. Planning/execution/parallel sequencing skills should remain subordinate to CODE.

### Praxis (`JohnXu22786/skill-framework`)

Clean static `ctx.skills` provider and good Agent Skills implementation/reference. Candidate semantic skills: `fault-isolation`, `feedback-assimilation`, and review-oriented skills. `completion-proof` contains sound evidence discipline, but it is guidance only; SSSF CODE remains terminal authority. Planning/execution/task-splitting skills should not own workflow.

### `hackerFish/awesome-dsh-skills`

Useful as a small skill-quality corpus: format validator aligned with official rules, isolated DSH_HOME load smoke, and explicit rejection of unverified “magic prompts.” Individual skills are conventional. More useful for FUT-011 skill qualification/adapter testing than as a DSH roadmap feature.

### Keel (`JohnXu22786/spec-driven`)

Useful deterministic spec/assumption/audit validation ideas, but the full Anchor→Spec→Probe→Build→Audit workflow creates artifact and process ceremony that overlaps the authoritative WorkPackage/requirement model. Reference only.

## Roadmap implications

No current roadmap stage or FUT state is changed by this screening. `FUT-002` remains `PRESERVE`; `FUT-001` remains the sequenced DSH architecture.

When DSH implementation begins, the proposed evaluation order is:

1. establish the qualification toolbox (`dsh-provenance`/equivalent → Testkit → Windtunnel → effect/quiescence checks);
2. DSH-0B: compare/adapt `dsh-code-runtime-container` isolation semantics inside SSSF-owned Docker custody;
3. DSH-2: evaluate Plan Lattice **auto/passive continuity only**;
4. DSH-3: evaluate `dsh-background-agents` **thin bg child surface only**;
5. DSH-4: evaluate `dsh-tool-orchestrate` as the static candidate-DAG compiler and add SSSF authority/effect/resource semantics;
6. DSH-5+: evaluate lazy MCP/tool disclosure and code-intelligence implementations as corresponding seams become active;
7. DSH-6+: use verification/outcome-loop implementations as reference/evaluation profiles, never outer acceptance truth;
8. DSH-8: evaluate `dsh-self-evolving` against the existing governed self-evolution contract and fresh-frontier promotion rules.

## Required pre-DSH catalog revisit

This 2026-08-20 screening is a **snapshot**, not the final DSH plugin selection. The catalog and DSH itself are both moving quickly, while SSSF's own Docker custody, ExecutionCell contract, evidence model, capability policy, and qualification machinery will be materially more concrete by the time DSH commissioning approaches.

Therefore, before the first real DSH implementation increment is activated—not merely before production landing—Browser Sol must perform a fresh review of `awesome-dsh-plugin/awesome-dsh-plugin` and relevant candidate repositories.

The revisit must:

1. inspect the then-current catalog head and compare it with the preserved 2026-08-20 snapshot;
2. identify new plugins, replacements, abandoned candidates, material redesigns, and newly available official DSH seams;
3. reassess the shortlist against the **then-current SSSF architecture**, especially Docker/SandboxProvider custody, WorkPackage/ExecutionCell identity, capability/effect admission, budgets, evidence and quiescence contracts;
4. re-check the Skills and Workflow & Automation categories rather than assuming today's candidates remain best-in-class;
5. re-check adjacent Security & Permissions, Development & Runtime, Tools & Capabilities, Git & Code Review, Sessions & Messages, Memory, and Models & Providers areas when they touch an active DSH stage;
6. preserve new findings before implementation and route them through the normal planning lifecycle; discovery alone never activates work;
7. re-pin every selected candidate to exact source/build/dependency identity and re-run the full qualification stack—an old review or an older qualified release does not qualify a newer plugin generation.

This revisit should occur **after the pre-DSH Docker baseline/freeze and existing Wayfinder commissioning are sufficiently concrete to evaluate real integration boundaries, but before DSH-0A/0B implementation choices are treated as settled**. It is an architecture checkpoint, not a calendar reminder and not a second backlog.

If the catalog has materially evolved, today's shortlist may be revised, replaced, split, or rejected. The preservation objective is to retain useful evidence and avoid rediscovery, not to create attachment to specific community implementations.

Governing invariant:

> Community plugins may supply implementations inside a bounded DSH phase. They never inherit SSSF workflow, source, authority, security, evidence, acceptance, or promotion ownership merely by being useful or installable.
