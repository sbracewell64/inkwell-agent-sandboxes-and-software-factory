# Post-Baseline Roadmap

This is the sequencing index for post-baseline SSSF evolution. Detailed sandbox and DSH contracts live in [`SANDBOX_DSH_IMPLEMENTATION_PLAN.md`](SANDBOX_DSH_IMPLEMENTATION_PLAN.md).

Planning-state semantics are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). A roadmap item may be `SEQUENCED` without being `ACTIVE`; implementation begins only when a named increment crosses the activation boundary under the increment protocol.

Prose order in this document is a human projection. The authoritative dependency representation is the typed block under [Machine-readable dependency graph](#machine-readable-dependency-graph). Where prose ordering and a typed edge disagree, the typed edge governs, and accidental serialization by prose order is not a dependency.

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
WAYFINDER-0 — configure/commission the Captain's already-prepared Wayfinder transport
        ↓
WAYFINDER-1 — deterministic transport + identity smoke  →  WAYFINDER_TECHNICAL_GATE
        ↓
     [branch]
       A: WAYFINDER-POC-1 executable → run Poker School Phase A → full product commissioning verdict
       B: WAYFINDER-POC-1 Captain/source blocked → typed hold on the POC only; DSH may continue
        ↓
DSH-0A → DSH-0B → DSH-1...
        ↓
future candidates as their unlocks are met
```

The Docker-first ordering above is unchanged by that branch: `SBX-2..8 → BASELINE-PR → post-Docker/pre-DSH baseline` remains a hard chain, and the Wayfinder gate is still entered only after the baseline is frozen.

`exe.dev` is retiring from the target architecture. Its live availability is **not** a prerequisite for Docker and must not be allowed to block the roadmap. Existing exe.dev code, documentation and retained evidence remain useful historical/reference inputs when extracting provider-neutral semantics. If live exe.dev still works, an opportunistic comparison may be recorded; absence or expiry is `EXTERNAL_DEPENDENCY`, not a reason to defer Docker.

The Wayfinder named above is the Captain's **existing, partially configured Wayfinder setup** intended to connect Captain → FirstMate → SSSF. It is not the Matt Pocock Wayfinder reviewed under `FUT-013`, and this roadmap does not authorize installing another Wayfinder implementation.

---

## Dependency-cone continuation law

Registered from control #35 `SOL-FM-SSSF-DEPENDENCY-CONE-CONTINUATION-001` (Captain-authorized). The law governs how a blocked item propagates. It authorizes no prerequisite bypass.

> A blocked roadmap item blocks only the work whose safety, correctness, applicability, evidence, or explicit prerequisite contract materially depends on that item. Independent reversible work that remains fully qualified and within delegated authority continues. Captain absence, external dependency, or one blocked project must not globally serialize an otherwise dependency-safe roadmap.

Decision procedure:

```text
BLOCKED ITEM
   |
   +-- does the blocker materially affect downstream safety / correctness /
   |   applicability / evidence / an explicit prerequisite contract?
   |         yes -> block that dependency cone
   |
   +-- no -> is the candidate downstream work independently reversible,
             qualified, evidence-bearing, and within delegated authority?
                   yes -> continue
                   no  -> hold only that work
```

Blocker classes and their exact blocking scope:

| Class | Blocks |
|---|---|
| `CAPTAIN_REQUIRED` | only tasks that actually require the reserved Captain decision |
| `EXTERNAL_DEPENDENCY` | only tasks materially dependent on the unavailable provider/tool/quota/credential/host capability |
| `BROWSER_SOL` | nothing on its own; material engineering judgment routes to the control plane while dependency-safe work continues |
| `SELF_HANDLE` | nothing; work continues under ordinary FirstMate authority |

Hard-gate preservation:

- a prerequisite that establishes security, source custody, execution containment, acceptance applicability, provider/runtime compatibility, exact identity, evidence integrity or boundedness keeps blocking everything that materially consumes that property;
- a gate may be reclassified from hard to soft only by explicit architecture/planning authority, never by inference from Captain absence;
- Captain absence never broadens authority, and silence is not approval;
- tests, validators, maker/checker separation, expected-head protection, provenance, immutable proof, security/privacy, cost rules, boundedness and acceptance remain mandatory;
- a blocked item must expose its exact dependency-cone scope and reason, and a status projection must not read as globally stalled while independent executable nodes remain.

### Required fixtures for this law

Both cases are recorded here because #35's acceptance requires one of each and they must stay reconstructable.

**F-SOFT — a blocked item where independent work continues.** `POKER-SCHOOL-SOURCE-CUSTODY-v1` is unsatisfied and Captain-owned: no representative source video is observed. `WAYFINDER-POC-1` is therefore held and `WAYFINDER_PRODUCT_COMMISSIONING` is `BLOCKED`. The blocker is non-technical and does not invalidate `WAYFINDER-0/1` transport correctness, so the cone is exactly `{WAYFINDER-POC-1}`. `DSH-0A → DSH-0B → DSH-1…` remain eligible once `WAYFINDER_TECHNICAL_GATE = PASS`.

**F-HARD — a true hard gate where downstream correctly remains blocked.** `SBX-4` establishes source/security/credential/network containment custody. `AL-1` and `DSH-0B` materially consume that custody, so both remain blocked while `SBX-4` is unqualified. Captain absence, schedule pressure, and the fact that `AL-1` is only an experiment do not soften that edge.

---

## Machine-readable dependency graph

This block is the authoritative typed dependency representation for the items below. It is a projection of this document's own sections — it is not a second planning owner, a status store, or a scheduler, and it holds no lifecycle state that the owning section does not already state.

`observed_at` values are planning-time observations, never proofs. Every axis below is `CNO`, `BLOCKED` or unevaluated; nothing in this block marks any item `ACTIVE`, `PROVEN`, `QUALIFIED`, accepted, commissioned or runtime-effective.

This block is enforced, not merely declared: `docs/validation/check_planning_dependency_graph.py` runs it in the offline gate. The properties it proves and their watched-red controls are documented in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md#the-graphs-validator).

```yaml
schema: planning-dependency-graph/v1
owner: docs/development/ROADMAP.md
registered_by: canonical-planning-reconciliation-batch-20260826
authority:
  - "control #6 comment 5418574266 — WAYFINDER-0/1/POC-1 roadmap amendment"
  - "control #6 comment 5418915210 — hard pre-DSH vs conditionally nonserializing POC"
  - "control #33 + comment 5418916312 — WAYFINDER-POC-1 commission and gate revision"
  - "SOL-FM-SSSF-WAYFINDER-POC-1-SUCCESS-SEMANTICS-20260826 — three-axis status model"
  - "control #34 SOL-FM-SSSF-AGENT-LIGHTNING-SBX-POC-001"
  - "control #35 SOL-FM-SSSF-DEPENDENCY-CONE-CONTINUATION-001"
  - "control #36 SOL-FM-SSSF-AI-NATIVE-SDLC-TRANSFER-LAWS-001"
  - "SOL-FM-SSSF-CANONICAL-PLANNING-RECONCILIATION-BATCH-20260826"

edge_kinds:
  HARD_PREREQUISITE: >
    `to` materially consumes a safety, correctness, applicability, evidence, custody or
    contract property that `from` establishes. `to` stays blocked until `from` is
    observed-good. CNO does not satisfy a hard prerequisite.
  NONSERIALIZING_COMMISSIONING: >
    `from` is mandatory before `to` may be marked full-commissioning PASS, but a
    BLOCKED/INCOMPLETE `from` whose blocker is Captain, source or otherwise
    non-technical does not block `to`'s dependency cone.
  SOFT_UNLOCK: >
    `from` makes `to` eligible for evaluation. Eligibility is never automatic promotion.
  REOPENS_ON_DEFECT: >
    a defect found in `from` that is material to `to` re-opens `to`'s dependency cone
    and holds it until the defect is resolved.
  CONSTRAINS_DESIGN: >
    `from` dictates a design choice in `to` without blocking `to`'s start.

endpoint_resolution: >
  An edge endpoint resolves, in order, to an id in `nodes`, a name in `status_axes`, or a
  `FUT-nnn` id in docs/development/FUTURE_CANDIDATES.md. An endpoint that resolves to none
  of those is a graph defect, not a new item.

nodes:
  - id: LAUNCH-1
    owner: "docs/development/ROADMAP.md#launch-1--operator-facing-sssf-launch-surface"
    planning_state: ACTIVE
  - id: SBX-0
    owner: "docs/development/ROADMAP.md#sbx-0--reference-semantics-inventory"
    planning_state: ACTIVE
  - id: SBX-1
    owner: "docs/development/ROADMAP.md#sbx-1--sandboxprovider--lifecycle-state-contract"
    planning_state: SEQUENCED
  - id: SBX-2
    owner: "docs/development/ROADMAP.md#sbx-2--docker-feasibility--contract-binding"
    planning_state: SEQUENCED
  - id: SBX-3
    owner: "docs/development/ROADMAP.md#sbx-3--minimal-deterministic-lifecycle"
    planning_state: SEQUENCED
  - id: SBX-4
    owner: "docs/development/ROADMAP.md#sbx-4--sourcesecuritycredentialnetworkcognition-boundary"
    planning_state: SEQUENCED
  - id: SBX-5
    owner: "docs/development/ROADMAP.md#sbx-5--cancellationreconciliationquiescence"
    planning_state: SEQUENCED
  - id: SBX-6
    owner: "docs/development/ROADMAP.md#sbx-6--observability--identity-integration"
    planning_state: SEQUENCED
  - id: SBX-7
    owner: "docs/development/ROADMAP.md#sbx-7--bounded-deterministic-concurrency"
    planning_state: SEQUENCED
  - id: SBX-8
    owner: "docs/development/ROADMAP.md#sbx-8--docker-commissioning--pre-dsh-freeze"
    planning_state: SEQUENCED
  - id: BOUND-1
    owner: docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md
    planning_state: SEQUENCED
    note: >
      Activation eligibility is governed by the existing predicate
      BOUND1-ACTIVATION-PREDECESSOR-v1 in that document. This graph references that
      predicate and does not restate, widen or re-qualify it.
  - id: BASELINE-PR
    owner: "docs/development/ROADMAP.md#sbx-8--docker-commissioning--pre-dsh-freeze"
    planning_state: SEQUENCED
    note: obligation owned by the SBX-8 section; not a separate roadmap item
  - id: POST-DOCKER-BASELINE
    owner: "docs/development/ROADMAP.md#sbx-8--docker-commissioning--pre-dsh-freeze"
    planning_state: SEQUENCED
    note: the immutable post-Docker / pre-DSH baseline identity
  - id: WAYFINDER-0
    owner: "docs/development/ROADMAP.md#wayfinder-0--configure-the-captains-existing-wayfinder-transport"
    planning_state: SEQUENCED
  - id: WAYFINDER-1
    owner: "docs/development/ROADMAP.md#wayfinder-1--deterministic-transport--identity-smoke"
    planning_state: SEQUENCED
  - id: WAYFINDER-POC-1
    owner: "docs/development/ROADMAP.md#wayfinder-poc-1--poker-school-phase-a-product-commissioning-poc"
    register_entry: "docs/development/FUTURE_CANDIDATES.md#fut-014--poker-school-phase-a-wayfinder-product-commissioning-poc"
    planning_state: SEQUENCED
  - id: AL-1
    owner: "docs/development/ROADMAP.md#al-1--agent-lightning-gated-sandbox-optimization-poc"
    register_entry: "docs/development/FUTURE_CANDIDATES.md#fut-015--agent-lightning-gated-sandbox-optimization-poc"
    planning_state: SEQUENCED
    scheduling_window:
      after: SBX-4
      before: SBX-8
    not_a_predecessor_of: [SBX-7, SBX-8, BASELINE-PR, WAYFINDER-0, DSH-0A]
  - id: SDLC-L1
    owner: "docs/development/ROADMAP.md#sdlc-l1--authorization-gate-hooks"
    planning_state: SEQUENCED
  - id: SDLC-L2
    owner: "docs/development/ROADMAP.md#sdlc-l2--evaluator-immutability"
    planning_state: SEQUENCED
  - id: SDLC-L3
    owner: "docs/development/ROADMAP.md#sdlc-l3--configuration-regression-evals"
    planning_state: SEQUENCED
  - id: SDLC-L4
    owner: "docs/development/ROADMAP.md#sdlc-l4--task-contract-deviation-control"
    planning_state: SEQUENCED
  - id: CB-1
    owner: "docs/development/ROADMAP.md#cb-1--deterministic-control-band-maintenance-loop"
    register_entry: "docs/development/FUTURE_CANDIDATES.md#fut-016--deterministic-control-band-maintenance-loop"
    planning_state: CANDIDATE
    disposition: ROADMAP_CANDIDATE_ONLY
  - id: FUT-003
    owner: "docs/development/ROADMAP.md#fut-003--firstmate-planning-transition-awareness"
    planning_state: ACTIVE
  - id: FUT-001
    owner: "docs/development/ROADMAP.md#fut-001--bounded-autonomous-dsh-execution-cells"
    planning_state: SEQUENCED
  - id: DSH-0A
    owner: "docs/development/ROADMAP.md#dsh-0a--protocol--deterministic-mock"
    planning_state: SEQUENCED
  - id: DSH-0B
    owner: "docs/development/ROADMAP.md#dsh-0b--real-docker-custody-seam"
    planning_state: SEQUENCED
  - id: DSH-1
    owner: "docs/development/ROADMAP.md#dsh-1--real-multi-turn-single-agent-cell"
    planning_state: SEQUENCED
  - id: DSH-2
    owner: "docs/development/ROADMAP.md#dsh-2--bounded-autonomous-refinement"
    planning_state: SEQUENCED
  - id: DSH-3
    owner: "docs/development/ROADMAP.md#dsh-3--childsubagent-lineage--parallelism"
    planning_state: SEQUENCED

edges:
  - from: SBX-0
    to: SBX-1
    kind: HARD_PREREQUISITE
  - from: SBX-1
    to: SBX-2
    kind: HARD_PREREQUISITE
  - from: BOUND-1
    to: SBX-2
    kind: HARD_PREREQUISITE
    why: >
      BOUND-1 must be complete and qualified before SBX-2 activation
  - from: SBX-2
    to: SBX-3
    kind: HARD_PREREQUISITE
  - from: SBX-3
    to: SBX-4
    kind: HARD_PREREQUISITE
  - from: SBX-4
    to: SBX-5
    kind: HARD_PREREQUISITE
  - from: SBX-5
    to: SBX-6
    kind: HARD_PREREQUISITE
  - from: SBX-6
    to: SBX-7
    kind: HARD_PREREQUISITE
  - from: SBX-7
    to: SBX-8
    kind: HARD_PREREQUISITE
  - from: SBX-8
    to: BASELINE-PR
    kind: HARD_PREREQUISITE
  - from: BASELINE-PR
    to: POST-DOCKER-BASELINE
    kind: HARD_PREREQUISITE
  - from: POST-DOCKER-BASELINE
    to: WAYFINDER-0
    kind: HARD_PREREQUISITE
  - from: WAYFINDER-0
    to: WAYFINDER-1
    kind: HARD_PREREQUISITE
  - from: WAYFINDER-1
    to: DSH-0A
    kind: HARD_PREREQUISITE
    why: >
      DSH eligibility depends on WAYFINDER_TECHNICAL_GATE=PASS, never on Poker
      School availability
  - from: WAYFINDER-1
    to: WAYFINDER-POC-1
    kind: HARD_PREREQUISITE
  - from: WAYFINDER-POC-1
    to: WAYFINDER_PRODUCT_COMMISSIONING
    kind: NONSERIALIZING_COMMISSIONING
    why: >
      mandatory before full product/fog-of-war commissioning may be marked PASS; a
      Captain/source blocker yields BLOCKED or INCOMPLETE without serializing DSH
  - from: WAYFINDER-POC-1
    to: DSH-0A
    kind: REOPENS_ON_DEFECT
    why: >
      a Wayfinder transport/identity/supervision defect material to downstream
      unattended operation re-opens the affected DSH cone
  - from: DSH-0A
    to: DSH-0B
    kind: HARD_PREREQUISITE
  - from: DSH-0B
    to: DSH-1
    kind: HARD_PREREQUISITE
  - from: DSH-1
    to: DSH-2
    kind: HARD_PREREQUISITE
  - from: DSH-2
    to: DSH-3
    kind: HARD_PREREQUISITE
  - from: SBX-7
    to: DSH-3
    kind: HARD_PREREQUISITE
  - from: SBX-3
    to: AL-1
    kind: HARD_PREREQUISITE
  - from: SBX-4
    to: AL-1
    kind: HARD_PREREQUISITE
  - from: SBX-5
    to: AL-1
    kind: HARD_PREREQUISITE
  - from: SBX-6
    to: AL-1
    kind: HARD_PREREQUISITE
  - from: BOUND-1
    to: AL-1
    kind: HARD_PREREQUISITE
  - from: SDLC-L2
    to: AL-1
    kind: CONSTRAINS_DESIGN
    why: >
      AL-1's protected surfaces are SDLC-L2's applies_to list; the refusal half is
      the mechanism AL-1 needs for benchmark/scorer and held-out custody
  - from: BOUND-1
    to: SDLC-L1
    kind: CONSTRAINS_DESIGN
  - from: BOUND-1
    to: SDLC-L2
    kind: CONSTRAINS_DESIGN
  - from: BOUND-1
    to: SDLC-L3
    kind: CONSTRAINS_DESIGN
  - from: BOUND-1
    to: SDLC-L4
    kind: CONSTRAINS_DESIGN
  - from: DSH-1
    to: FUT-007
    kind: SOFT_UNLOCK
  - from: DSH-1
    to: FUT-008
    kind: SOFT_UNLOCK
    scope: early-schema-evaluation
  - from: DSH-2
    to: FUT-005
    kind: SOFT_UNLOCK
  - from: DSH-2
    to: FUT-006
    kind: SOFT_UNLOCK
    scope: serial
  - from: DSH-3
    to: FUT-006
    kind: SOFT_UNLOCK
    scope: parallel
  - from: DSH-3
    to: FUT-008
    kind: SOFT_UNLOCK
    scope: hierarchical
independent_nodes:
  - id: LAUNCH-1
    why: "may land before Docker; it must not imply Docker, Wayfinder or DSH is commissioned"
  - id: FUT-003
    why: "no Docker/Wayfinder/DSH prerequisite; bounded by its own acceptance boundary"
  - id: SDLC-L1
    why: "extends already-landed authorization owners; no roadmap-node prerequisite"
  - id: SDLC-L2
    why: "extends the ADW permission owner; no roadmap-node prerequisite"
  - id: SDLC-L4
    why: "extends the task/increment lineage owners; no roadmap-node prerequisite"

status_axes:
  POKER_SCHOOL_PHASE_A:
    values: [PASS, INCOMPLETE, BLOCKED]
    observed_at_registration: BLOCKED
    blocker: POKER-SCHOOL-SOURCE-CUSTODY-v1
  WAYFINDER_TECHNICAL_GATE:
    values: [PASS, FAIL, CNO]
    observed_at_registration: CNO
    why: >
      none of P1..P5 in WAYFINDER-TECHNICAL-GATE-v1 is observed-good; the gate has not
      been evaluated, which is could-not-observe, not FAIL and not PASS
  WAYFINDER_PRODUCT_COMMISSIONING:
    values: [PASS, INCOMPLETE, BLOCKED, FAIL, CNO]
    observed_at_registration: BLOCKED
    blocker: POKER-SCHOOL-SOURCE-CUSTODY-v1

superseded_status_owners:
  - field: wayfinder_verdict
    source: "control #33 body, vocabulary [PASS, FAIL, CNO]"
    disposition: INPUT_LINEAGE_ONLY
    rule: >
      Superseded as a single all-purpose status by the Captain-authorized two-axis
      Wayfinder model plus POKER_SCHOOL_PHASE_A. Its historical wording is preserved as
      input lineage in the WAYFINDER-POC-1 section. No competing current verdict owner
      is maintained, and nothing may be projected from it.

predicates:
  WAYFINDER-TECHNICAL-GATE-v1:
    projects: WAYFINDER_TECHNICAL_GATE
    class: SELF_HANDLE
    pass_requires_all:
      - id: P1
        axis: >
          SBX-8 Docker commissioning accepted
      - id: P2
        axis: >
          a real Docker-backed BASELINE-PR proven
      - id: P3
        axis: >
          the immutable post-Docker/pre-DSH baseline frozen
      - id: P4
        axis: >
          WAYFINDER-0: the Captain's existing Wayfinder transport is configured or
          commissionable
      - id: P5
        axis: >
          WAYFINDER-1: a deterministic transport + identity smoke PASSES, proving
          Captain -> Wayfinder -> FirstMate attribution and the return path
    unobservable_axis_yields: CNO
    recheck: >
      re-observe each axis against the then-current canonical SSSF main and accepted
      owners; a planning-time observation is never a perpetual pin.

  POKER-SCHOOL-SOURCE-CUSTODY-v1:
    class: CAPTAIN_REQUIRED
    owner: Captain
    gates:
      - WAYFINDER-POC-1
    dependency_cone:
      - WAYFINDER-POC-1
      - WAYFINDER_PRODUCT_COMMISSIONING
    does_not_gate:
      - WAYFINDER-0
      - WAYFINDER-1
      - DSH-0A
      - DSH-0B
      - DSH-1
      - SBX-2
      - SBX-8
      - AL-1
    axes:
      - id: A1
        axis: >
          at least one representative poker training video is present at the
          commissioning-owner-decided source location; the seed names
          E:\Poker-School\source-videos\
        observed_at_registration: ABSENT
        evidence: >
          E:\Poker-School does not exist; E:\Poker holds notes, documents and PNGs and
          zero video files at depth <= 3.
      - id: A2
        axis: >
          the execution-host workspace question is answered: is E:\Poker-School binding
          as a location or illustrative, and if binding does it bind only the
          human-facing artifacts or the working/cache artifacts too?
        observed_at_registration: UNANSWERED
        evidence: >
          workspace layout is SELF_HANDLE; only the binding-location question is
          Captain or commissioning-owner authority.
    recheck: >
      re-observe the source location and the answer state of A2 immediately before any
      Phase A execution attempt. No source video may be invented, and no cloud or paid
      substitute is authorized.
    non_serialization_rule: >
      A1/A2 unsatisfied yields POKER_SCHOOL_PHASE_A=BLOCKED and
      WAYFINDER_PRODUCT_COMMISSIONING=BLOCKED/INCOMPLETE with the exact blocker retained.
      It does not make WAYFINDER_TECHNICAL_GATE non-PASS and does not hold DSH.

  AGENT-LIGHTNING-POC-ELIGIBILITY-v1:
    class: SELF_HANDLE
    gates:
      - AL-1
    requires_all:
      - id: G1
        axis: >
          SBX-3 real deterministic Docker lifecycle sufficiently qualified
      - id: G2
        axis: >
          SBX-4 source/security/credential/network boundary qualified
      - id: G3
        axis: >
          sufficient SBX-5 cancellation/quiescence/recovery to contain failed optimizer
          runs
      - id: G4
        axis: >
          sufficient SBX-6 exact run/source/evidence harvesting to reconstruct the
          experiment
      - id: G5
        axis: >
          BOUND-1 applicable bounds active
      - id: G6
        axis: >
          the experiment is scheduled before SBX-8 final commissioning so it can still
          expose substrate defects
    unobservable_axis_yields: CNO
    recheck: >
      re-observe upstream microsoft/agent-lightning identity and the SBX acceptance
      state immediately before execution; the pinned v1.0.1 reference is planning
      evidence, not a runtime pin.
    registration_is_not:
      - execution
      - admission
      - spend authorization
      - containment proof

  SDLC-L3-RUNTIME-GATE-v1:
    class: EXTERNAL_DEPENDENCY
    gates:
      - SDLC-L3
    gate_scope: >
      runtime configuration gating only
    does_not_gate_scope: >
      SDLC-L3 deterministic validators, fixtures and schema work
    requires_all:
      - id: E1
        axis: >
          control #30 CRP owns immutable candidate/effective config release identity and
          transactional activation
      - id: E2
        axis: >
          control #31 HQC owns applicability/completeness verification without
          duplicating the eval runner
      - id: E3
        axis: >
          control #32 EIL supplies the recurrence/incident corpus
    unobservable_axis_yields: CNO
    unresolved_semantics_rule: >
      #31 HQC and #32 EIL are planning commissions whose Browser Sol review is not
      complete. They are referenced here as pending dependencies only. No HQC or EIL
      architecture is pre-decided, activated or registered by this graph.
```

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

## AL-1 — Agent Lightning gated sandbox optimization POC

**Planning state: `SEQUENCED`, not `ACTIVE`, not admitted, not executed.** Registered from control #34 `SOL-FM-SSSF-AGENT-LIGHTNING-SBX-POC-001` (Captain-authorized). Candidate register entry: `FUT-015`. **This registration is a planning position only. It is not execution, not admission of Agent Lightning into SSSF, not a spend authorization, and not evidence of containment.**

Scheduling window: **after `SBX-4`, before `SBX-8`** — late enough that canonical SSSF can be proven untouchable and experiment evidence can be harvested, early enough that the experiment can still expose substrate defects. `AL-1` is **not** a predecessor of `SBX-7`, `SBX-8`, `BASELINE-PR`, `WAYFINDER-0` or `DSH-0A`; it must never delay prerequisite sandbox correctness merely to run early.

Eligibility predicate `AGENT-LIGHTNING-POC-ELIGIBILITY-v1`, all axes required, any unobservable axis yielding `CNO`:

| Axis | Requirement |
|---|---|
| `G1` | `SBX-3` real deterministic Docker lifecycle sufficiently qualified |
| `G2` | `SBX-4` source/security/credential/network boundary qualified |
| `G3` | sufficient `SBX-5` cancellation/quiescence/recovery to contain failed optimizer runs |
| `G4` | sufficient `SBX-6` exact run/source/evidence harvesting to reconstruct the experiment |
| `G5` | `BOUND-1` applicable bounds active |
| `G6` | scheduled before `SBX-8` final commissioning |

Shape of the experiment, as authorized: an adversarial-but-productive sandbox workload in which a qualified coding optimizer is given broad reversible freedom over an isolated exact-SHA copy of SSSF against a fixed benchmark, while canonical host SSSF, credentials, control state, evaluator authority and other protected domains are proven unreachable. Arm A is an ordinary optimizer control; arm B is the same agent, model, effort, runtime, source, benchmark and budget with the Agent Lightning Skill loaded. The initial scope uses the **Skill only** — the full RL trainer/gateway/controller stack is not authorized here.

Held boundaries carried from the commission:

- a sandbox result never directly becomes canonical SSSF; a useful change is reintroduced through a fresh ordinary increment with current source identity and the normal maker/checker, validators, review, proof and landing path;
- the benchmark/scorer definition, held-out cases, acceptance/VerificationContract authority, proof records, security/privacy/capability policy, landing authorization, maker/checker rules, canonical BOUND-1 policy, the canonical host checkout and credentials are protected surfaces — an optimizer suggestion against them is retained as diagnostic evidence and can never self-approve;
- a higher visible benchmark score is not evidence that SSSF improved; credible improvement needs held-out/generalization evidence and no unacceptable regression under canonical qualification;
- unavailable measurement is `CNO`, never improvement;
- boundedness integrates with `BOUND-1` rather than creating parallel limits;
- no new paid service or expenditure, and no full-framework deployment or standing always-on optimizer under this authorization.

Follow-ons — a review of the full Agent Lightning framework, and a standing bounded optimization role for every material new SSSF/DSH addition — remain `PLANNING_ONLY_UNTIL_SEPARATE_RULING`. They are named here so they are not mistaken for part of this registration, and they are not registered as candidates by it.

Re-observe the exact upstream `microsoft/agent-lightning` identity and skill path immediately before execution. The `v1.0.1` / `8435586d147b4cf7bff33e687d7317149e79cbb8` reference in the commission is planning evidence, not a runtime pin.

---

## WAYFINDER — post-Docker / pre-DSH commissioning gate

**Planning state: `SEQUENCED` after the post-Docker/pre-DSH baseline; not `ACTIVE` yet.** Registered from control #6 (comments `5418574266`, `5418915210`), control #33 and its gate revision `5418916312`, and the success-semantics ruling `SOL-FM-SSSF-WAYFINDER-POC-1-SUCCESS-SEMANTICS-20260826`. The existing gate is expanded into three explicit steps; none of them is activated, executed or commissioned by this registration.

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

### Status model

Three distinct projections. `POKER_SCHOOL_PHASE_A` is the normative definition of the Poker School product PASS; it is not a third independent verdict axis over Wayfinder.

| Axis | Values | Observed at registration |
|---|---|---|
| `POKER_SCHOOL_PHASE_A` | `PASS` / `INCOMPLETE` / `BLOCKED` | `BLOCKED` — `POKER-SCHOOL-SOURCE-CUSTODY-v1` unsatisfied |
| `WAYFINDER_TECHNICAL_GATE` | `PASS` / `FAIL` / `CNO` | `CNO` — no axis of `WAYFINDER-TECHNICAL-GATE-v1` is observed-good |
| `WAYFINDER_PRODUCT_COMMISSIONING` | `PASS` / `INCOMPLETE` / `BLOCKED` / `FAIL` / `CNO` | `BLOCKED` |

Binding rules:

- DSH eligibility depends on `WAYFINDER_TECHNICAL_GATE = PASS`, not on Poker School availability;
- `POKER_SCHOOL_PHASE_A = BLOCKED` because source media is unavailable may coexist with `WAYFINDER_TECHNICAL_GATE = PASS`. DSH then continues under the dependency-cone continuation law while `WAYFINDER_PRODUCT_COMMISSIONING` stays `BLOCKED` or `INCOMPLETE`;
- `WAYFINDER_PRODUCT_COMMISSIONING = PASS` requires the real broad-intent/fog-of-war POC to execute far enough to establish the product, translation and supervision properties it exists to test. Technical transport smoke alone cannot manufacture a full product-commissioning PASS;
- a Poker School run that exposes a transport/identity/supervision defect material to downstream unattended operation re-opens the affected DSH dependency cone.

**Historical `wayfinder_verdict` — input lineage only.** Control #33's original combined `wayfinder_verdict` field (`vocabulary: [PASS, FAIL, CNO]`, with `PASS_requires` covering broad-intent receipt, plan derivation, autonomous resolution of routine uncertainty, no unauthorized money/security/privacy/product assumption, Browser Sol routing for material architecture ambiguity, decomposition/supervision success, reconstructable lineage, return through the intended control surface, and "Poker School reaches PASS, or any non-PASS is attributable to a genuine Captain/external blocker rather than transport/orchestration failure") is **superseded as a single all-purpose status** by the two-axis Wayfinder model above plus `POKER_SCHOOL_PHASE_A`. Its wording is preserved here as input lineage for the axis definitions. No competing current verdict owner is maintained and nothing is projected from it.

### WAYFINDER-0 — Configure the Captain's existing Wayfinder transport

**Planning state: `SEQUENCED`, not `ACTIVE`. Hard pre-DSH technical prerequisite.**

Finish and configure the Captain's existing, partially configured Wayfinder transport so it is commissionable. This completes the existing local setup; it does not install another Wayfinder implementation.

### WAYFINDER-1 — Deterministic transport + identity smoke

**Planning state: `SEQUENCED`, not `ACTIVE`. Hard pre-DSH technical prerequisite.**

A deterministic transport/identity smoke proving Captain → Wayfinder → FirstMate attribution and the return path. Its PASS is the `WAYFINDER_TECHNICAL_GATE` and is what DSH eligibility consumes.

The exact deterministic smoke fixture is not specified by any observed governing document. That is a `CNO` to resolve inside WAYFINDER-1, not an assumption to carry forward.

### WAYFINDER-POC-1 — Poker School Phase A product-commissioning POC

**Planning state: `SEQUENCED`, not `ACTIVE`, not executed. Mandatory for full Wayfinder product/fog-of-war commissioning; conditionally nonserializing for DSH.** Detailed commissioning contract: control #33. Candidate register entry: `FUT-014`.

The first substantial real project driven through Wayfinder, run deliberately with broad-project fog of war preserved: the Captain supplies product intent, hard constraints, reserved-authority boundaries and the definition of success, and the engineering system investigates current upstream contracts, selects reversible engineering details, decomposes the work, supervises execution and validates results.

Normative Phase A product PASS, from control #33: one actual video passes end to end from source media through media inspection, local timestamped transcription, bounded strategically relevant frame extraction, a structured provenance-bearing poker corpus, current `teach` lesson generation, an interactive reasoning-based assessment, and resulting learning evidence.

**Assessment interpretation against the current `teach` contract.** The current upstream `teach` skill implements a stateful file-backed teaching workspace with lessons, quizzes/drills, references and learning records, and explicitly ships **no** initial knowledge-assessment step — learner level is inferred from mission and learning records.

- do not build a replacement assessment framework to satisfy older wording; adapt Phase A around what current `teach` truthfully provides;
- Phase-A product PASS still requires at least one materially source-dependent lesson plus a meaningful source-dependent reasoning interaction, using current `teach`-supported quiz/drill/learning-record behavior or an equivalent behavior that exact upstream generation already provides;
- "prefer answer commitment before explanation where current `teach` supports it" is a preference on interaction shape, not a mandate to add an assessment subsystem. If the real interaction can require and record an answer before feedback, use it; otherwise record the limitation rather than silently rewriting `teach`;
- the absence of a shipped initial learner-level assessment step is an observed upstream limitation and a possible later improvement candidate, not by itself a Phase-A failure;
- if at execution time the exact qualified `teach` generation cannot produce any meaningful reasoning interaction or learning evidence without replacing its framework, `POKER_SCHOOL_PHASE_A` cannot be `PASS`: record `INCOMPLETE` or `CNO` at the exact affected property and return the evidence rather than inventing equivalence;
- re-observe the exact upstream `teach` generation immediately before execution. Any generation named in planning evidence is a snapshot, never a perpetual runtime pin.

**Current Captain-owned blocker — `POKER-SCHOOL-SOURCE-CUSTODY-v1`.** Class `CAPTAIN_REQUIRED`. Two axes, both observed unsatisfied at registration:

| Axis | Statement | Observed |
|---|---|---|
| `A1` | at least one representative poker training video is present at the commissioning-owner-decided source location; the seed names `E:\Poker-School\source-videos\` | `ABSENT` — `E:\Poker-School` does not exist; `E:\Poker` holds notes, documents and PNGs and zero video files at depth ≤ 3 |
| `A2` | is `E:\Poker-School` binding as a location or illustrative, and if binding does it bind only the human-facing artifacts or the working/cache artifacts too? | `UNANSWERED` — workspace *layout* is `SELF_HANDLE`; only the binding-location question is Captain/commissioning-owner authority |

Dependency cone: exactly `{WAYFINDER-POC-1, WAYFINDER_PRODUCT_COMMISSIONING}`. It does not gate `WAYFINDER-0`, `WAYFINDER-1`, `AL-1`, any `SBX` item, or `DSH-0A → DSH-0B → DSH-1…`. No source video may be invented and no cloud or paid substitute is authorized. Re-observe both axes immediately before any Phase A execution attempt.

Scope exclusions carried from control #33: full-library batch ingestion, solver/GTO engine integration, a poker bot, automated wagering or casino/account integration, a hand-history platform, a custom spaced-repetition platform, a custom replacement for `teach`, an elaborate database, cloud hosting, and paid API integration.

---

## FUT-003 — FirstMate planning-transition awareness

**Planning state: `ACTIVE`, not `PROVEN`.**

Governing architecture: `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`.

Implementation remains split into SSSF `FP-001` producer and FirstMate `FM-FP-001` consumer. Only `ACTIVE` transitions may enter normal intake, and even then exact referenced source must pass ordinary admission. Live enablement requires accepted exact producer/consumer identities, compatibility and rollback proof.

---

## SDLC-L1..L4 — AI-native SDLC transfer laws

**Planning state: `SEQUENCED`, not `ACTIVE`, not implemented.** Registered from control #36 `SOL-FM-SSSF-AI-NATIVE-SDLC-TRANSFER-LAWS-001` (Captain-authorized), sequenced against the existing owner/dependency map produced by the #36 owner-reconciliation pass.

These four laws **strengthen existing owners**. No `intent.md` / `spec.md` / `plan.md` / `REVIEW.md` artifact family, no second SDLC state machine, no new daemon, scheduler, registry or state database is authorized by this registration. Where a law is already satisfied by a landed owner, it is recorded as satisfied and not duplicated.

Disposition vocabulary used below, from the owner-reconciliation matrix: `ALREADY_SATISFIED` (a landed owner proves the property), `EXTEND_OWNER` (an existing owner must be extended; ordinary increment work), `DEFER_UNTIL_PREREQUISITE` (a named control-plane or roadmap prerequisite must exist first).

Cross-cutting rule for all four: knowledge or judgment may live in instructions and skills, but a property that must always hold migrates to code/hook/type/validator enforcement at its canonical seam wherever practical. Harness-specific hooks improve early feedback and never replace harness-neutral effect/acceptance owners.

### SDLC-L1 — Authorization-gate hooks

> A hook may enforce an authorization but never becomes the source of authorization. No material side effect occurs unless the exact required authority is present, applicable, current, and mechanically proven at the final pre-effect seam.

| Disposition | Scope |
|---|---|
| `ALREADY_SATISFIED` | typed one-use head-bound authority, exact-head re-observation at use, restart-surviving consumption, distinguishable refusal-vs-CNO, chokepoint placement, `not-applicable` as a reported verdict — all landed in the FirstMate landing-authorization owner; and the SSSF `DestroyAuthorization` family for the destroy action class, with its watched-red fixture proving missing/wrong/fabricated authority blocks before effect |
| `EXTEND_OWNER` | the live SSSF sandbox lifecycle recipes consume obligation *ordering* rather than a typed one-use authority: teardown/destroy, runtime-key minting with a spend limit, public-exposure of a sandbox, and the fleet-wide reap backstop. Extend them onto the existing `DestroyAuthorization*` owner; SSSF also ships no harness pre-tool projection |
| `DEFER_UNTIL_PREREQUISITE` | an SSSF-side `landing-authorization/v1` / `verification-contract/v1` owner waits on the B4 seam-contract family already listed under B4 above |

Constraint carried from control #30: configuration activation must use a configuration-effect-specific one-use authority. Repository landing authorization must not be reused as configuration-mutation authority.

Watched reds this law must eventually prove red: an environment variable or prose marker treated as approval for a head-bound effect; a stale or wrong-repository/head/target authority admitted; a Claude-specific hook credited with protecting non-Claude execution paths; a hook deciding product/security/spend authority instead of consuming typed authority; one-use authority reused after consumption; post-effect success inferred without authoritative observation.

### SDLC-L2 — Evaluator immutability

> Once an acceptance/evaluation surface is established for a task generation, the maker or optimizer cannot silently weaken or rewrite that surface while trying to satisfy it. A legitimate evaluator change requires an explicit revision transition that invalidates or re-baselines dependent evidence and independently qualifies the new evaluator generation.

| Disposition | Scope |
|---|---|
| `ALREADY_SATISFIED` | the ADW roster already refuses the builder write access to the ADW machinery that grades it, and read-only agents are genuinely read-only against the repository. The revision/generation semantics this law needs — declared freshness dependencies, evaluator bytes and contract version as first-class dependencies, property-scoped rather than global freeze, and refusal of self-review — exist and are tested in the FirstMate qualification owner and are the model to copy |
| `EXTEND_OWNER` | the regression/failing test established before a fix is not frozen for that task generation; the deterministic validators are writable by the builder and by the documenter; the check manifest and its pinning validator are writable by the same agent, so a coordinated two-file edit is uncaught; every agent can write every agent's prompt surface; and the current permission control is post-effect detect-and-rollback rather than pre-effect refusal. All of this extends the existing roster/permissions owner — the one new artifact is a list of protected evaluator paths inside a file that already exists |
| `DEFER_UNTIL_PREREQUISITE` | held-out/hidden-benchmark access control belongs to `AL-1` and waits on its `SBX-4..6` + `BOUND-1` predicate |

Freeze the property-scoped evaluator surface relevant to the active task/qualification generation, never every test file forever. Refactors and legitimate test improvements outside the protected property remain ordinary work where no acceptance-laundering risk exists.

Required fixtures: a bug-fix agent attempting to delete or relax the failing test is refused; an optimizer editing a benchmark scorer is refused or the experiment fails; a genuinely defective test produces an explicit evaluator revision that creates a new generation and invalidates the old evidence; an unrelated test file outside the frozen property scope still changes freely.

### SDLC-L3 — Configuration regression evals

> Agent-facing configuration that materially changes execution behavior deserves regression qualification like code.

| Disposition | Scope |
|---|---|
| `ALREADY_SATISFIED` | one landed deterministic instance already is a configuration regression eval — the production-extension-path validator, which refuses to pass on an empty roster surface rather than passing vacuously — plus the three-valued gate law under which unavailable evidence is `CNO`, never a pass, and the standing rule against adding an LLM judge where code can settle the claim exactly |
| `EXTEND_OWNER` | the rest of the roster surface (model, thinking, tools, writes, protected files, prompt-engineering paths), the prompt/skill/instruction bytes, and the tool-schema/extension behavior have no deterministic coverage. Extend by adding validators in the shape of the landed one. The semantic-eval half extends existing register entries `FUT-010` and `FUT-011` rather than opening a parallel register |
| `DEFER_UNTIL_PREREQUISITE` | predicate `SDLC-L3-RUNTIME-GATE-v1`: runtime configuration gating waits on control #30 CRP for immutable candidate/effective release identity and transactional activation, control #31 HQC for applicability/completeness verification, and control #32 EIL for the recurrence/incident corpus |

Controls #31 and #32 are planning commissions whose Browser Sol review is not complete. They are referenced here as pending dependencies only; **no HQC or EIL architecture is pre-decided, activated or registered by this roadmap entry.** Fixture, schema and integration-requirement work proceeds dependency-independently.

Gate semantics: no configuration change fails merely because an eval metric is unavailable — unavailable required evidence is `CNO`/non-PASS for any acceptance that depends on it; model/provider variance is controlled or reported rather than misattributed to repository architecture; pass-rate gains never override security, cost, privacy or capability law; exact model/harness/provider/config release identities are preserved.

### SDLC-L4 — Task-contract deviation control

> Material implementation drift from the accepted task/phase contract is recorded as a typed deviation/revision, not erased by rewriting the plan after the fact.

| Disposition | Scope |
|---|---|
| `ALREADY_SATISFIED` | the **phase** contract is already immutable to the agent working inside it, because the ADW phase declarations sit inside protected paths; artifact evidence is already bound to the exact generation it reviewed by the evidence-manifest owner; and append-only lineage keeps a superseded worker's evidence attributed to the worker that produced it |
| `EXTEND_OWNER` | the **task** contract is fully maker-writable, and the durable intent records — increment documents, the increment ledger, the proof matrix — are writable by the same agents required to update them. The both-directions comparison primitive this law needs already exists as an open, green, unlanded candidate; extend that owner rather than building a second one, then add one typed deviation record above it. The true touched-path set is already computed and discarded; a closed deviation-classification vocabulary does not yet exist in SSSF |
| `DEFER_UNTIL_PREREQUISITE` | a typed task/phase-contract *workspace* owner waits on control #27, whose report is returned and planning-only. A deviation record is lineage: it belongs in the durable control state and is projected, not stored in a workspace that owns nothing authoritative |

Classifications to reuse or define: `implementation_detail_nonmaterial`, `required_root_cause_expansion`, `recurrence/invariant_prevention`, `material_architecture_change`, `product_scope_change`, `security/privacy/cost/capability_change`, `unknown/CNO`.

Agents may not retroactively edit the task contract to make the diff appear compliant. Normal reversible root-cause or recurrence-prevention work stays within delegated authority where already lawful. A genuine Captain-only scope, security, spend or product change still routes to the Captain. Exact-head and artifact evidence stays bound to the candidate generation it actually reviewed.

### CB-1 — Deterministic control-band maintenance loop

**Planning state: `CANDIDATE`. Disposition: `ROADMAP_CANDIDATE_ONLY`, not sequenced for implementation.** Candidate register entry: `FUT-016`.

```text
deterministic observation
  -> typed threshold / control-band breach
  -> bounded FirstMate task
  -> agent diagnosis only when reasoning is needed
  -> normal SSSF implementation / verification / review / authorization
  -> incident/failure enters the recurrence owner
  -> structural fix + regression fixture where warranted
```

Rules that bind any future implementation: the detector stays deterministic code and never becomes a continuously reasoning monitor agent; action tiers are pre-authorized and bounded, with production, destructive, security and spend boundaries still governed by existing authority; it reuses the existing unattended supervision and control-plane mechanisms and adds no second daemon or orchestrator; and it is implemented only after the current execution, lineage and CRP owners are mature enough to support it truthfully.

### Sequence

Implement in small reviewable increments following actual owner dependencies, never one combined PR. `SDLC-L1` enforcement and `SDLC-L2` may proceed once their exact existing seams are identified and normal SSSF gates permit. `SDLC-L3`'s deterministic validators and fixtures proceed now; its runtime gate waits behind `SDLC-L3-RUNTIME-GATE-v1`. `SDLC-L4` extends the existing task/increment/workspace lineage owners. `CB-1` stays planning-only until separately activated.

Acceptance for the set: no new AI-native-SDLC outer framework or state machine exists; authorization hooks consume canonical typed authority and cannot grant it; at least one real or fixture pre-effect gate proves stale/wrong/missing authority blocks before effect; property-scoped evaluator mutation by the maker is mechanically refused in at least one representative case; legitimate evaluator revision has explicit generation and applicability semantics; the configuration regression-eval architecture binds to the CRP/HQC/EIL owners without duplicate release truth; material task-contract deviation cannot be hidden by a post-hoc plan rewrite; and positive plus watched-red tests prove each activated law.

---

## FUT-001 — Bounded autonomous DSH execution cells

**Planning state: `SEQUENCED`, not `ACTIVE`.**

Real DSH activation follows the post-Docker baseline **and WAYFINDER-1 commissioning**. What DSH eligibility consumes is `WAYFINDER_TECHNICAL_GATE = PASS`. `WAYFINDER-POC-1` is a `NONSERIALIZING_COMMISSIONING` predecessor of `WAYFINDER_PRODUCT_COMMISSIONING`, not of DSH: a Poker School blocked only by a Captain/source/non-technical condition leaves DSH eligible, while a defect it exposes that is material to unattended operation re-opens the affected DSH cone.

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