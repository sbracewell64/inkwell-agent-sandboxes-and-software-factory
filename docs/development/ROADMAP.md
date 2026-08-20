# Post-Baseline Roadmap

This is the sequencing index for post-baseline SSSF evolution. Detailed sandbox and DSH contracts live in [`SANDBOX_DSH_IMPLEMENTATION_PLAN.md`](SANDBOX_DSH_IMPLEMENTATION_PLAN.md).

Planning-state semantics are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). A roadmap item may be `SEQUENCED` without being `ACTIVE`; implementation begins only when a named increment crosses the activation boundary under the increment protocol.

## Governing value-creator law

SSSF optimizes three distinct value creators rather than treating every problem as an agent problem:

- **ENGINEER owns VALUE and reserved AUTHORITY** — intent, desired product outcome, personal/product choices, new spend, security/privacy exceptions, and materially irreversible decisions.
- **AGENT owns UNCERTAINTY REDUCTION** — investigation, semantic judgment, design alternatives, bounded implementation/review work, and other reasoning that cannot be reduced honestly to deterministic rules.
- **CODE owns STATE TRANSITION** — sequencing, applicability, routing, budgets, retries, observation typing, persistence, validation, acceptance, recovery, promotion/landing, and terminal state wherever those rules can be made deterministic.

Optimization direction:

> **Minimize required engineer feedback. Use agents for irreducible judgment. Continuously push stable/checkable behavior into deterministic code.**

An agent must not become the outer state machine merely because it can reason about the state machine.

## Near-term approved commissioning order

The near-term operator goal is a usable SSSF before DSH:

```text
current B4/control-plane qualification closure
        ↓
LAUNCH-1 — one-click SSSF operator front door
        ↓
SBX-0/1 — provider semantics + contract
        ↓
DockerSbxProvider implementation/qualification (SBX-2..8)
        ↓
BASELINE-PR — one real ordinary PR through the Docker-backed accepted path
        ↓
post-Docker / pre-DSH immutable baseline
        ↓
commission the Captain's already-prepared Wayfinder connector
        ↓
DSH-0A → DSH-0B → DSH-1...
        ↓
future candidates as their unlocks are met
```

`exe.dev` is retiring from the target architecture. Its live availability is **not** a prerequisite for Docker and must not be allowed to block the roadmap. Existing exe.dev code, documentation and retained evidence remain useful historical/reference inputs when extracting provider-neutral semantics. If live exe.dev still works, an opportunistic comparison may be recorded; absence or expiry is `EXTERNAL_DEPENDENCY`, not a reason to defer Docker.

The Wayfinder named above is the Captain's **existing, partially configured Wayfinder setup** intended to connect Captain → FirstMate → SSSF. It is not the Matt Pocock Wayfinder reviewed under `FUT-013`, and this roadmap does not authorize installing another Wayfinder implementation.

---

## B1 — Baseline archive + documentation discovery

Goal: complete the original B0 freeze and make `docs/README.md` a first-class agent entrypoint.

Acceptance:

- B0 evidence/teardown complete;
- immutable proof identity exists;
- fresh agents are routed through the docs index;
- documentation discovery does not alter execution behavior.

## B2 — Canonical repository and source custody

Goal: ensure every execution environment runs the exact SSSF source being evolved.

Acceptance:

- canonical and upstream remote roles are explicit;
- repository + commit + tree identity is authoritative;
- execution source is gated against requested identity;
- mutable branch names are convenience state only.

## B3 — Windows/WSL operator portability

Goal: make the supported Windows/WSL operator path reproducible from a genuinely fresh state.

Acceptance includes line-ending, bootstrap/doctor, source, observability, launcher, lifecycle and teardown behavior without transient source edits. Any still-unobservable dimension remains CNO rather than being rounded into PASS.

## B4 — Deterministic execution / review / landing substrate

Goal: finish enough provider-neutral SSSF machinery that Docker does not have to invent workflow, review, process, or landing semantics.

Required stable seams:

### AgentBackend

One bounded reasoning assignment has a typed execution owner. Policy-relevant backend/product/model/profile/attempt/tool/terminal/usage/quiescence facts are explicit or CNO.

The accepted B4-002 subprocess-supervisor contract (or successor) owns shell-free process launch, bounded streams, timeout/cancellation, attempt accounting, descendant cleanup, three-valued terminal observation and quiescence. Docker and DSH must not create a second process supervisor.

### CommandSpec

Acceptance-relevant commands bind typed argv, cwd, environment references/allowlist, timeout, stdin mode, stdout/stderr policy, expected exits and execution identity. Shell prose is not command authority.

### Verification / semantic review / landing

Acceptance-critical obligations are code-discoverable and exact-head bound. The target contract family includes the semantics of:

- `verification-contract/v1`;
- `review-envelope/v1`;
- `semantic-review-result/v1`;
- `ruling-envelope/v1`;
- one-use `landing-authorization/v1`.

Required laws:

- deterministic code determines applicable verifier obligations;
- absent/stale/skipped/wrong-head/CNO-under-PASS-policy evidence is non-PASS;
- fixture calibration is distinct from real-seam proof;
- maker/reviewer independence is explicit;
- reviewer protocol/input identity is deterministically bound before launch;
- Browser Sol rulings bind exact request/envelope/candidate identity;
- local code mints one-use landing authority only when all requirements hold;
- mutation-time movement invalidates landing authority;
- exact resulting `main` receives post-merge proof.

### Docker-readiness gate

Docker may begin once the provider-independent contract owners needed to implement and judge it are sufficiently stable and the named Docker increment has bounded acceptance.

**A real end-to-end engineering PR is no longer a pre-Docker prerequisite.** If the retiring exe.dev path cannot supply that real seam, Docker must not be blocked waiting for it. The real PR commission is performed on the Docker-backed path before DSH.

Required before Docker mutation work:

- separate AgentBackend and SandboxProvider authority;
- typed CommandSpec/process ownership and quiescence semantics;
- exact source identity and source/workspace custody;
- three-valued verification/review semantics adequate to judge Docker work;
- no known defect that would make Docker qualification evidence materially untrustworthy.

---

## LAUNCH-1 — Operator-facing SSSF launch surface

**Planning state: `ACTIVE`. Named increment `sssf-launch-1` is `WORKING` from exact base/head `bee9296a4c94b1dc3da6991acd1755a91fa681eb` on local branch `fm/sssf-launch-1`; no implementation checkpoint is credited until normal increment evidence is produced.**

Goal: give the Captain one obvious launch action for SSSF without creating a new orchestrator.

The repository already has engineering front doors such as `just local cc`; LAUNCH-1 wraps the accepted operator path rather than replacing its authority.

Required properties:

- Windows-friendly one-click/double-click entry;
- opens/enters the correct canonical SSSF context and hands control to the existing FirstMate/SSSF authority chain;
- no credentials embedded in launcher bytes or arguments;
- repository/path/config identity is observable and failures are actionable;
- launcher is transport only: it owns no planning state, retries, acceptance or engineering workflow;
- smallest practical implementation; no GUI framework unless a demonstrated need appears;
- reversible removal restores the prior command-line entry path.

The launcher may land before Docker. It must not imply that Docker, Wayfinder or DSH is already commissioned.

---

## B5 — SandboxProvider contract with Docker as the required implementation target

`SandboxProvider` is distinct from `AgentBackend`. It reports environment/provider facts and performs bounded environment operations; SSSF code owns sequencing, retries/recovery decisions, acceptance and promotion.

### SBX-0 — Reference semantics inventory

**Planning state: `ACTIVE`, not exited or `PROVEN`. Named increment `sssf-sbx-0` crossed activation from exact base/head `bee9296a4c94b1dc3da6991acd1755a91fa681eb`. Its durable semantics-handoff implementation is now landed on canonical SSSF history through PR #21 / merge `aa0dcc5e66a41284cdb2f28ca4c235bec7c623d6`; that landed handoff does not by itself establish the SBX-0 lifecycle exit, SBX-1 activation, or SBX-2 readiness.**

Inventory current sandbox lifecycle semantics from canonical code, docs, tests and retained evidence. Classify each fact as:

- required provider-neutral semantic;
- exe.dev-specific mechanism;
- current limitation;
- obsolete/historical artifact.

Live exe.dev access is optional evidence only.

### SBX-1 — SandboxProvider + lifecycle-state contract

**Planning state: `SEQUENCED`, not `ACTIVE`. The SBX-0 durable handoff is landed and therefore is no longer an unresolved blocker. Provider-neutral SandboxProvider contract/fake implementation bytes are also landed through PR #18 / merge `b902cdcecd65c8ba03031875297d31e990f12c11`, with implementation-status reconciliation through PR #22 / merge `991d3a64f1b96a8b9637f97060d692af3518228f`. Those landed bytes do not establish SBX-1 activation, acceptance, certification, real-provider proof, Windows-host qualification, or SBX-2 unlock.**

Define the minimum typed provider interface, state owner, CNO/failure semantics, irreversibility rules, reconciliation contract and fake-provider conformance suite.

Provider operations must be sufficient for create, typed exec, inspect, evidence/artifact extraction, Git harvest/export, process/quiescence inspection, stop, destroy authorization and reconciliation. Provider reports actual state; SSSF code decides recovery.

### SBX-2 — Docker feasibility + contract binding

Bind the selected Docker implementation to the SBX-1 contract using direct feasibility evidence. Build the adapter/conformance harness against Docker itself.

If exe.dev remains available, the same semantic fixtures may be run against it as an additional comparison. **No live ExeDevProvider pass is required to proceed.** Historical exe.dev behavior is not a second production provider requirement.

---

## B6 — DockerSbxProvider implementation and commission

Docker is the only intended production sandbox provider.

### SBX-3 — Minimal deterministic lifecycle

Prove exact source → setup/readiness → deterministic `CommandSpec` → bounded evidence/Git export → quiescence → destroy → residual-state check. No live coding agent or DSH required.

### SBX-4 — Source/security/credential/network/cognition boundary

Prove source-broker custody, minimum mounts, no host control-plane credentials/auth homes or uncontrolled Docker socket in the guest, explicit runtime secret/effect/network policy, and pinned instruction/template/tool identities for evidence-bearing workers.

### SBX-5 — Cancellation/reconciliation/quiescence

Interrupt every lifecycle boundary. Durable identity must allow a later process to reconcile what exists. Retry cannot silently duplicate resources. Evidence/harvest precedes irreversible destroy. Cleanup uncertainty remains CNO/non-clean.

### SBX-6 — Observability + identity integration

Join run/provider/source/ADW/process/evidence/harvest/future-cell identities through existing accepted owners. No second authoritative Docker/DSH trace store.

### SBX-7 — Bounded deterministic concurrency

SSSF code owns WorkNode dependencies, write/resource locks, admission/backpressure, max parallelism, retry/cancel, deterministic result collection and aggregate acceptance. Prove at least two genuinely overlapping isolated Docker sandboxes and complete cleanup.

Maker/checker identity and evidence remain distinct.

### SBX-8 — Docker commissioning / pre-DSH freeze

No exe.dev parity gate is required.

Prove:

- supported Windows/WSL Docker operation;
- complete SandboxProvider conformance against the accepted contract;
- source/security/cancellation/quiescence/evidence requirements on real Docker seams;
- one real bounded ordinary engineering PR through the Docker-backed path without Captain transport;
- exact post-merge proof;
- clean teardown/reconciliation;
- operator launcher can reach the commissioned path without acquiring workflow authority.

Then switch/freeze the accepted default as Docker-only and retain exe.dev solely as historical reference code/evidence until deliberate retirement removes it.

The resulting exact identity is the **post-Docker / pre-DSH baseline**.

---

## WAYFINDER-1 — Commission the Captain's existing Wayfinder connector

**Planning state: `SEQUENCED` after the post-Docker/pre-DSH baseline; not `ACTIVE` yet.**

Purpose:

```text
Captain
   ↓
existing Wayfinder
   ↓
FirstMate
   ↓
SSSF typed work / planning / execution surfaces
```

Wayfinder is an engineer/intent transport and decision interface. It is not SSSF's source of engineering state and does not replace FirstMate, Browser Sol, the SSSF planning lifecycle, increments, Git/PR evidence, or deterministic acceptance.

Commissioning must preserve:

- Engineer-owned choices remain with the Captain;
- observable facts are investigated automatically rather than asked of the Captain;
- reversible engineering ambiguity is handled by FirstMate/Browser Sol under delegated authority;
- typed work identity crosses the connector without relying on conversational memory;
- no duplicate planning truth is created;
- existing local Wayfinder setup is completed rather than replaced by the Matt Pocock research implementation from FUT-013.

Wayfinder commissioning occurs **after** the baseline Docker PR/freeze and **before** real DSH activation.

---

## FUT-003 — FirstMate planning-transition awareness

**Planning state: `ACTIVE`, not `PROVEN`.**

Governing architecture: `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`.

Implementation remains split into SSSF `FP-001` producer and FirstMate `FM-FP-001` consumer. Only `ACTIVE` transitions may enter normal intake, and even then exact referenced source must pass ordinary admission. Live enablement requires accepted exact producer/consumer identities, compatibility and rollback proof.

---

## FUT-001 — Bounded autonomous DSH execution cells

**Planning state: `SEQUENCED`, not `ACTIVE`.**

Real DSH activation follows the post-Docker baseline **and WAYFINDER-1 commissioning**.

Target:

```text
SSSF deterministic outer graph
        ↓
qualified AgentBackend + Docker SandboxProvider
        ↓
bounded DSH execution cell
        ↓
SSSF deterministic verification / independent review / acceptance
        ↓
one-use landing + exact-main proof
```

### DSH-0A — Protocol + deterministic mock

Define/prove `ExecutionCellRequest` / `ExecutionCellResult`, parent identity, budgets, authority-negative controls, result/evidence schema, cancellation and CNO. This is protocol proof only.

### DSH-0B — Real Docker custody seam

Run the mock cell through the accepted Docker SandboxProvider + AgentBackend/process-owner path. Prove source/workspace custody, external budgets, timeout/cancel, evidence survival, Git harvest without promotion authority and zero surviving processes/children.

### DSH-1 — Real multi-turn single-agent cell

Admit one exact DSH build/dependency identity plus one qualified backend/model profile. Exclude subagents, autonomous refinement, workflows/plugins and self-evolution. Measure value against the post-Docker/pre-DSH baseline.

**Unlock:** FUT-007 and early FUT-008 schema evaluation.

### DSH-2 — Bounded autonomous refinement

Qualify inner repair/refinement inside one outer attempt under fixed code-owned ceilings.

**Unlock:** FUT-005 and serial FUT-006.

### DSH-3 — Child/subagent lineage + parallelism

Requires SBX-7. Qualify one child, serial children, then parallel children with narrower/equal authority, aggregate budgets, lineage, cancellation propagation and quiescence.

**Unlock:** parallel FUT-006 and hierarchical FUT-008.

### DSH-4 — Inner workflows/goals

DSH may own complex inner graphs, but cannot create/advance outer attempts/phases, change budgets, decide acceptance or promote/land.

### DSH-5 — Richer capabilities

Evaluate compaction, MCP, LSP/code intelligence, code mode, long/background workers, terminal mechanisms and selected plugins/built-ins one at a time. Consult FUT-002 before designing a new post-DSH capability.

### DSH-6 — Product subagents / maker-checker

Use Claude/Codex/DeepSeek product workers only through qualified AgentBackend contracts. Multiple models do not themselves establish independent review.

### DSH-7 — Adaptive inner orchestration

Permit DSH to choose how to spend a fixed execution-cell budget among already-admitted inner actions. It cannot enlarge budget or authority.

### DSH-8 — Governed self-evolution

Only immutable candidate generations may be proposed. SSSF-owned isolated qualification, independent review, rollback and promotion decide production generation changes.

---

## Downstream candidate unlocks

An unlock means eligible for evaluation, never automatic promotion:

- DSH-1 → FUT-007 + early FUT-008 schema evaluation;
- DSH-2 → FUT-005 + serial FUT-006;
- DSH-3 → parallel FUT-006 + hierarchical FUT-008;
- DSH-5 → selected FUT-002 plugin candidates;
- roadmap checkpoints → promotion opportunities for FUT-009..012 when they demonstrably simplify or harden the active architecture;
- instruction-heavy FirstMate/DSH stages → re-evaluate FUT-011 using FUT-013's preserved instruction-testing evidence.

Probabilistic verifier output remains advisory inner-cell evidence and cannot override deterministic FAIL or narrow CNO.

---

## Long-range admission law

Every activated stage preserves:

- the three value creators and their authority split;
- SSSF code ownership of outer state transition, applicability, retries, acceptance, landing and terminal state;
- exact source/workspace custody;
- explicit resource/time/token/cost/effect/network ceilings;
- qualified AgentBackend and Docker SandboxProvider identities;
- three-valued observation;
- maker/checker policy and deterministic reviewer-protocol binding;
- forceable termination and provable quiescence;
- attributable evidence through the shared identity spine;
- exact-head / exact-main proof.

Each stage requires a named increment, exact candidate identity, non-vacuity and watched-red controls, real-seam evidence where required, independent review under policy, rollback, and measured net value over the last accepted baseline.

## Rules

Do not block Docker on retiring exe.dev availability. Extract semantics from durable evidence; use live exe.dev only if opportunistically available.

Do not make Docker an orchestrator. Docker owns environment mechanics only; SSSF code owns scheduling/recovery/acceptance.

Do not make DSH the outer graph or a hidden model proxy.

Do not make Wayfinder a second SSSF planning/state authority.

Do not ask the Engineer for facts that code or agents can establish, and do not ask the Agent to own state transitions that deterministic code can own.