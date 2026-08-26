# Future SSSF Candidate Register

This is the durable register for future architecture and research items that have moved beyond pure conversation but are not necessarily active engineering work.

State meanings are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md).

## Register

| ID | Item | State | Decision / sequence | Notes |
|---|---|---|---|---|
| FUT-001 | Bounded autonomous DSH execution cells | SEQUENCED | `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`; long-range roadmap | SSSF owns outer authority; DSH may exercise substantial inner autonomy inside externally bounded execution cells. Cordis remains encapsulated inside DSH. |
| FUT-002 | Awesome DSH Plugin catalog as future research/reuse source | PRESERVE | none | Consult `awesome-dsh-plugin/awesome-dsh-plugin` before implementing new post-DSH harness capabilities. Catalog inclusion never implies trust or production eligibility. |
| FUT-003 | FirstMate planning-transition awareness | ACTIVE | `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`; `FP-001` producer + `FM-FP-001` consumer | Implementation is authorized on isolated branches. SSSF will emit a typed append-only planning feed; FirstMate will consume it through its existing authenticated custom-check/watch path. Only `ACTIVE` may enter engineering intake. Production landing/enablement remains held by current acceptance boundaries. |
| FUT-004 | LLM-as-a-Verifier as post-DSH research source | PRESERVE | `FUT-004_LLM_AS_VERIFIER_REFERENCE.md` | Preserve exact reviewed upstream identity and ideas; no dependency/install/trust implied. |
| FUT-005 | Verifier-guided DSH progress and refinement | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | Probabilistic progress is advisory inner-cell evidence consumed by code-owned policy. Production evaluation no earlier than DSH-2. |
| FUT-006 | Best-of-N DSH candidate selection | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | Multiple inner candidates remain one outer attempt; serial work waits for stable DSH cells, parallel work for DSH-3. |
| FUT-007 | Typed criteria decomposition for inner semantic evaluation | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | Criteria derive from typed work/acceptance contracts, not verifier invention; requires DSH WorkPackage/ExecutionCell semantics. |
| FUT-008 | Hierarchical probabilistic-verifier evidence and cost telemetry | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | Required governed evidence substrate before production use of the other verifier candidates; verifier authority remains advisory. |
| FUT-009 | SSSF architecture-unit contract and generated governance views | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | Collapse future ADR/ownership/artifact/validator/lineage catalogs into one small machine-readable architecture contract plus deterministic generated projections. |
| FUT-010 | Compact SSSF architectural laws | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | Extract a small SSSF-native law set into the existing Boundary Law surface; do not create an AE-style Constitution or governance runtime. |
| FUT-011 | Instruction-artifact governance | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; `AGENT_ENGINEERING_SKILLS_RESEARCH.md`; unsequenced | One semantic owner per durable instruction, real consumers, truthful bounds, generated inventory where useful, and behavioral/pressure qualification where the instruction claims to change agent behavior. |
| FUT-012 | Deterministic derived documentation | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | Generate mechanically derivable indexes/ownership/status views from canonical machine state; authored rationale remains authored and authoritative only in its proper domain. |
| FUT-013 | Agent engineering skill repositories as research sources | PRESERVE | `AGENT_ENGINEERING_SKILLS_RESEARCH.md` | Preserve exact-reviewed agent-skills, Superpowers, Matt Pocock skills, and agent-rules-books as idea/source material; do not install a competing router or import skills wholesale. |
| FUT-014 | Poker School Phase A Wayfinder product-commissioning POC | SEQUENCED | control #33 + gate revision `5418916312` + success-semantics ruling `SOL-FM-SSSF-WAYFINDER-POC-1-SUCCESS-SEMANTICS-20260826`; `ROADMAP.md` `WAYFINDER-POC-1` | Mandatory for full Wayfinder product/fog-of-war commissioning; conditionally nonserializing for DSH when blocked only by a Captain/source/non-technical condition. Currently `BLOCKED` on `POKER-SCHOOL-SOURCE-CUSTODY-v1`. Registration is not execution. |
| FUT-015 | Agent Lightning gated sandbox optimization POC | SEQUENCED | control #34 `SOL-FM-SSSF-AGENT-LIGHTNING-SBX-POC-001`; `ROADMAP.md` `AL-1` | Post-`SBX-4` / pre-`SBX-8` window behind `AGENT-LIGHTNING-POC-ELIGIBILITY-v1` (`SBX-3..6` + `BOUND-1`). Skill only, not the full RL stack. Registration is not execution, admission, or spend authorization. |
| FUT-016 | Deterministic control-band maintenance loop | CANDIDATE | control #36 `future_candidate_DETERMINISTIC_CONTROL_BAND_LOOP`; `ROADMAP.md` `CB-1` | `ROADMAP_CANDIDATE_ONLY`. Deterministic detector triggers a bounded task; no continuously reasoning monitor agent, no second daemon or orchestrator. Not sequenced for implementation. |

## FUT-001 — Bounded autonomous DSH execution cells

### Status

`SEQUENCED`

### Confirmed architectural direction

Target shape:

```text
SSSF deterministic work graph
        -> bounded autonomous DSH execution cell
        -> deterministic SSSF verification / acceptance
```

SSSF retains outer authority over:

- existence and identity of the execution domain;
- objective and role;
- source/workspace custody;
- eligible models/backends;
- resource, time, token, and cost ceilings;
- external-effect policy;
- maker/checker independence requirements;
- outer retry decisions;
- deterministic verification;
- acceptance;
- commit/promotion;
- terminal workflow state.

DSH may progressively qualify substantial inner autonomy, including:

- multi-turn reasoning;
- autonomous and parallel subagents;
- bounded refinement/Ralph loops;
- DSH workflows and `tool-workflow`;
- goal-driven inner execution;
- compaction;
- MCP/LSP/code mode;
- product subagents;
- long-running workers where justified;
- adaptive inner orchestration;
- eventually governed self-evolving agents.

An inner feature is not rejected merely because it contains its own loop, goal, workflow, or subagent mechanism. It is admitted only when its authority remains inside one SSSF execution domain and its budgets, evidence, termination, and effects are externally governable.

### Cordis boundary

SSSF does not import or expose Cordis as an architectural substrate. Cordis is an internal DSH implementation dependency. SSSF must interact through a stable DSH harness/executor boundary such that a future DSH implementation change away from Cordis does not alter SSSF's public control model.

### Prerequisite sequence

Before production DSH adoption, preserve and prove the existing execution/isolation foundations:

1. deterministic SSSF baseline capable of landing and merging a real PR;
2. parallel disposable Docker Sandbox execution substrate;
3. qualified Claude, Codex, and DeepSeek backend contracts;
4. source custody, lifecycle, evidence, hard termination, and quiescence contracts;
5. stable DSH execution-cell request/result/evidence boundary;
6. progressively larger inner-autonomy features, each admitted by evidence.

See [`ROADMAP.md`](ROADMAP.md) and the governing ADR.

## FUT-002 — Awesome DSH Plugin catalog

### Status

`PRESERVE`

Repository:

`awesome-dsh-plugin/awesome-dsh-plugin`

Governing instruction:

> Before implementing a new post-DSH harness capability, consult the Awesome DSH Plugin catalog for existing implementations and reusable ideas, but never infer trust or production eligibility from catalog inclusion.

This is an idea and candidate-source catalog, not an allowlist or marketplace for the trusted production profile.

When a corresponding capability reaches `CANDIDATE`, inspect the then-current catalog and candidate plugin source directly. Pin any candidate to exact source/build/dependency identity and require deterministic contract tests, negative controls, security/dependency review, isolated Docker qualification, lifecycle/quiescence evidence, and semantic review before admission. Every upgrade is a new qualification candidate.

High-value areas already identified for later research include contract/regression testing, evidence auditing, egress/redaction, static plugin vetting, dependency topology protection, reproducible failure bundles, hierarchical resource budgets, loop anomaly detection, stale-safe editing, progressive tool discovery, LSP/code intelligence, bounded subagent tooling, and governed self-evolution.

## FUT-003 — FirstMate planning-transition awareness

### Status

`ACTIVE`

Architecture is governed by `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`.

Implementation authorization is split into two independently bounded increments:

- `FP-001` — SSSF planning-event producer contract, append-only feed, validator, bootstrap snapshot, and evidence;
- `FM-FP-001` — FirstMate consumer using the existing authenticated custom-check/watch surface, private cursor/receipts, state-only classification, and `ACTIVE`-only intake eligibility.

The producer and consumer may be implemented and proven on isolated branches now. They must not be merged, enabled against the production planning source, or promoted to `PROVEN` merely because branch-local tests pass. Current SSSF PRE_CERTIFICATION constraints and the moving FirstMate watcher surface remain acceptance boundaries.

### Problem

Browser Sol maintains a deliberate SSSF planning lifecycle (`EXPLORE -> PRESERVE -> CANDIDATE -> DECIDED -> SEQUENCED -> ACTIVE -> PROVEN`). FirstMate should learn about durable planning promotions without requiring the Captain to relay them, but it must not infer work from prose or treat every planning-document edit as authorization.

Without a typed signal, the alternatives are both undesirable:

- manual Captain transport of planning changes; or
- FirstMate periodically rereading planning prose and deciding semantically whether a change is actionable.

The second would collapse the planning/engineering authority boundary.

### Evidence and selected primitive

The candidate evaluation was completed against FirstMate `main` at observed commit `f4e69d6ce411750b55fc9f186f60ce0e8b0cd786`.

FirstMate already provides the required transport foundations:

1. `bin/fm-watch.sh` owns one continuous supervision cycle and runs authenticated `state/*.check.sh` checks on its existing slow cadence. A validated custom check that returns empty output stays silent; nonempty output is durably queued as a `check:` wake and closes that watcher cycle.
2. `bin/fm-check-lib.sh` validates custom checks against a private hash-bound trust record and executes a private snapshot rather than mutable live bytes.
3. `bin/fm-check-register.sh` intentionally binds a custom check identity to its current bytes.
4. `bin/fm-remote-delta-read.sh` already implements the continuity algorithm needed for an append-only feed: byte offset plus prefix SHA-256, bounded complete-line reads, and explicit `continuity-broken` results on truncation, replacement, or prefix mutation rather than silent rebasing.
5. `bin/fm-procevent-remote-reply.sh` demonstrates durable cursor and idempotent-ingestion patterns over that delta contract, but process-event itself is designed for blocking external-process sources. A GitHub planning branch is periodic repository state, so adding a blocking process source would duplicate the watcher's polling role.

Selected design: **one registered FirstMate custom check** as the outer detector, running under the existing `fm-watch` cadence. No second polling daemon.

The SSSF planning side exposes an append-only notification index at:

`docs/development/PLANNING_EVENTS.jsonl`

The feed is not a source of truth. Each event points at authoritative planning documents and exact Git identity.

### Bootstrap rule

The bridge must not activate itself by replaying historical transitions. The first feed record is therefore a non-actionable bootstrap snapshot that establishes the current planning states and cursor baseline. FirstMate must consume that snapshot only as synchronization state.

Subsequent records are ordered transitions. A transition record's `source_commit` names the already-existing authoritative planning commit that established the state change; the later commit that appends the event is transport provenance, not the authority being announced.

### Authority split

**Browser Sol owns:**

- planning-state promotion;
- updates to `FUTURE_CANDIDATES.md`, ADRs, and `ROADMAP.md`;
- append of the corresponding transition event after the authoritative planning commit exists;
- the authoritative meaning of `EXPLORE` through `SEQUENCED`.

**FirstMate code owns:**

- polling the exact configured SSSF planning source;
- validating feed syntax/schema and continuity;
- deduplication and cursor advancement;
- classifying `to` state mechanically;
- refusing silent rebase after continuity failure.

**FirstMate agent behavior:**

- `PRESERVE`, `CANDIDATE`, `DECIDED`, `SEQUENCED`, `SUPERSEDED`, and `PROVEN` may refresh project knowledge or constraints but must not create engineering work merely from the event;
- only `to: ACTIVE` may enter normal FirstMate work intake;
- even `ACTIVE` is not executable authority by itself: FirstMate must fetch the named authoritative increment/docs at the referenced source identity and pass them through ordinary admission/classification before acting.

FirstMate does not promote SSSF planning states and does not edit Browser-Sol-owned planning documents through this mechanism.

### Required producer controls

`FP-001` must prove at least:

- the bootstrap snapshot is non-actionable and unique;
- event IDs are unique and ordered;
- state values are closed-set;
- transition edges are legal under `PLANNING_LIFECYCLE.md`;
- `ACTIVE` names a concrete increment identity and authoritative references;
- authoritative references are relative, bounded repository paths;
- every transition binds a full source commit identity;
- malformed JSON, duplicate IDs, illegal edges, absent required fields, and feed replacement/truncation are non-pass conditions;
- the honest feed passes non-vacuously.

### Required consumer controls

`FM-FP-001` must prove at least:

- no appended event produces no wake;
- a tampered registered check is rejected by the existing trust mechanism;
- changed/truncated prefix produces continuity failure and no cursor advance;
- duplicate event produces no duplicate transition effect;
- malformed or stale event produces no activation;
- every non-`ACTIVE` transition is awareness-only;
- `ACTIVE` is only intake eligibility and still requires exact referenced source validation;
- first synchronization consumes the bootstrap snapshot without creating work;
- rollback retires the check/cursor without changing SSSF planning truth.

### Rollback

Producer rollback removes the feed/validator before canonical adoption; the planning lifecycle and authoritative documents remain usable without it.

Consumer rollback retires the registered planning check and its private cursor/receipts; FirstMate returns to manual/ad-hoc awareness without changing SSSF planning state.

### Current acceptance boundary

`ACTIVE` means engineering is authorized. It does **not** mean either implementation is trusted or production-enabled.

Promotion to `PROVEN` requires implementation, proof, evidence, documentation, and accepted immutable Git identity on both sides. The SSSF side must respect current PRE_CERTIFICATION constraints; the FirstMate side must rebase and requalify against the settled watcher/test surface before live enablement.

## FUT-004 through FUT-008 — Post-DSH probabilistic verifier family

### Status

- `FUT-004` — `PRESERVE`: LLM-as-a-Verifier upstream research source.
- `FUT-005` — `CANDIDATE`: verifier-guided DSH progress and refinement.
- `FUT-006` — `CANDIDATE`: best-of-N DSH candidate selection.
- `FUT-007` — `CANDIDATE`: typed criteria decomposition for inner semantic evaluation.
- `FUT-008` — `CANDIDATE`: hierarchical probabilistic-verifier evidence and cost telemetry.

Detailed hypotheses, DSH gates, required evaluations, negative controls, and preserved upstream identity live in:

- [`FUT-004_LLM_AS_VERIFIER_REFERENCE.md`](FUT-004_LLM_AS_VERIFIER_REFERENCE.md)
- [`VERIFIER_DSH_RESEARCH.md`](VERIFIER_DSH_RESEARCH.md)

All four candidates are **unsequenced and gated behind DSH**. They do not authorize a pre-DSH verifier layer.

Shared law:

- probabilistic verifier output is advisory inner-cell evidence, never an SSSF acceptance oracle;
- deterministic `FAIL` cannot be overwritten by a probabilistic score;
- `COULD_NOT_OBSERVE` cannot be narrowed by probabilistic confidence;
- self-verification is optimization, not independent maker/checker review;
- code owns operational interpretation of scores, thresholds, and budgets;
- authoritative criteria derive from Engineer intent / typed work contracts, not verifier invention;
- generation, verification, selection, and refinement remain attributable execution units rather than being hidden behind a transparent TurboAgent-style inference proxy.

Before any of FUT-005 through FUT-008 advances to `DECIDED` or `SEQUENCED`, re-evaluate it against the then-qualified DSH execution-cell boundary, the current SSSF evidence/authority model, and the then-current upstream verifier implementation at an exact source identity.

## FUT-009 through FUT-012 — AE governance simplification family

### Status

- `FUT-009` — `CANDIDATE`: SSSF architecture-unit contract and generated governance views.
- `FUT-010` — `CANDIDATE`: compact SSSF architectural laws.
- `FUT-011` — `CANDIDATE`: instruction-artifact governance.
- `FUT-012` — `CANDIDATE`: deterministic derived documentation.

Detailed candidate evaluations, required controls, complexity constraints, and relationships to Sandbox -> DSH live in:

- [`AE_GOVERNANCE_RESEARCH.md`](AE_GOVERNANCE_RESEARCH.md)
- [`AGENT_ENGINEERING_SKILLS_RESEARCH.md`](AGENT_ENGINEERING_SKILLS_RESEARCH.md) for additional instruction-governance and simplicity evidence relevant primarily to FUT-010/FUT-011.

All four are **unsequenced**. The 67-document AE corpus was reviewed as architectural evidence, but AE itself is not a source of present SSSF authority and its Runtime/Repository/Registry/EIA topology is explicitly not adopted.

Shared extraction law:

> **Use AE to identify what SSSF must know and prove, not to decide how many components SSSF must have.**

Shared constraints:

- existing SSSF owners must be preferred over new subsystems;
- generated/read-only projections must not become second sources of truth;
- architectural-law work should strengthen the existing Boundary Law rather than create a Constitution hierarchy;
- instruction governance must not create a pre-DSH instruction runtime;
- deterministic derived documentation is adopted selectively only where canonical machine state already exists;
- architecture/governance machinery is admitted only when it reduces net complexity or closes a demonstrated recurrence class.

Potential dependency shape for later evaluation is `FUT-010 -> FUT-009/FUT-011 -> selective FUT-012`, but this is not roadmap sequencing. No implementation authority follows from this registration.

The semantic half of `SDLC-L3` (configuration regression evals, `ROADMAP.md`) extends `FUT-010` and `FUT-011` rather than opening a parallel register: `FUT-011` already owns *one semantic owner per durable instruction, real consumers, truthful bounds, and behavioral qualification where the instruction claims to change agent behavior*, and `FUT-010` owns the law-set extraction. Fixture and schema requirements arriving from `SDLC-L3` are recorded against those two entries. This cross-reference adds no state to either candidate.

## FUT-013 — Agent engineering skill research family

### Status

`PRESERVE`

Preserved exact-reviewed sources:

- `addyosmani/agent-skills` — instruction/skill structural, routing, behavioral and pressure evaluation;
- `obra/superpowers` — pressure-tested process documentation, fresh-context task/review patterns, durable recovery and instruction de-duplication;
- `mattpocock/skills` — focused planning/design primitives including deep-module/seam discipline and facts-versus-decisions/frontier reasoning;
- `mattpocock/agent-rules-books` — compact on-demand engineering doctrine/reference packs.

Detailed exact source identities, extracted mechanisms, non-adoption constraints, and possible FirstMate/DSH use live in:

- [`AGENT_ENGINEERING_SKILLS_RESEARCH.md`](AGENT_ENGINEERING_SKILLS_RESEARCH.md)

The primary architectural effect is new evidence for existing candidates rather than new workflow machinery:

- `FUT-011` should evaluate structural + applicability/routing + behavioral falsifiability for operational instruction artifacts where appropriate;
- `FUT-010` should consider real-seam/deep-owner and smallest-effective-mechanism laws;
- DSH-3/DSH-6 may later evaluate fresh-context briefs/reviews and bounded reviewer loops;
- Wayfinder-style issue maps remain `EXPLORE/REFERENCE` because SSSF already has an authoritative planning lifecycle and adding another planning truth would increase complexity.

Direct use of an external `SKILL.md` by FirstMate is permitted only as a future qualification question. FirstMate already has code-owned supervision and an owned `.agents/skills` surface, so any import/adaptation must first demonstrate a real semantic gap, reduce to the smallest needed judgment instruction, prove trigger/consumer behavior, avoid collision with existing skills, and preserve FirstMate's SELF_HANDLE/BROWSER_SOL/CAPTAIN/EXTERNAL_DEPENDENCY authority model.

No repository in this family is an allowlist, package dependency, active router, or implementation instruction by virtue of `PRESERVE` status.

## FUT-014 — Poker School Phase A Wayfinder product-commissioning POC

### Status

`SEQUENCED`

Roadmap owner: `WAYFINDER-POC-1` in [`ROADMAP.md`](ROADMAP.md). Commissioning contract: control #33, its Captain-authorized gate revision `5418916312`, and the success-semantics ruling `SOL-FM-SSSF-WAYFINDER-POC-1-SUCCESS-SEMANTICS-20260826`.

The first substantial real project driven through the Captain's existing Wayfinder transport, with broad-project fog of war deliberately preserved. It is a **workload**, not a control-plane increment: it creates no durable supervision, dispatch, status, routing, benchmark, evaluator or reconciliation mechanism, and it mutates nothing in SSSF. The only SSSF-side artifact the Wayfinder programme owes is this planning registration.

Gate split, exactly as authorized:

- `WAYFINDER-0` and `WAYFINDER-1` are **hard** pre-DSH technical prerequisites;
- `WAYFINDER-POC-1` is **mandatory** for full Wayfinder product/fog-of-war commissioning;
- when it is blocked solely by Captain absence, missing source video, or another non-technical Captain/external condition that does not invalidate `WAYFINDER-0/1` transport correctness, it is **nonserializing**: record `WAYFINDER_PRODUCT_COMMISSIONING = BLOCKED` or `INCOMPLETE`, retain the exact blocker, and let DSH progress under the dependency-cone continuation law;
- a defect it exposes in transport, identity or supervision that is material to downstream unattended operation re-opens the affected DSH dependency cone.

Current status: `POKER_SCHOOL_PHASE_A = BLOCKED` and `WAYFINDER_PRODUCT_COMMISSIONING = BLOCKED` on `POKER-SCHOOL-SOURCE-CUSTODY-v1`, a Captain-owned blocker whose two axes — a representative source video at the commissioning-owner-decided location, and whether `E:\Poker-School` is binding or illustrative for the execution host — are both unsatisfied. `WAYFINDER_TECHNICAL_GATE = CNO`; none of its axes is observed-good.

This registration authorizes no execution. Poker School does not run before the Wayfinder technical gate clears.

## FUT-015 — Agent Lightning gated sandbox optimization POC

### Status

`SEQUENCED`

Roadmap owner: `AL-1` in [`ROADMAP.md`](ROADMAP.md). Commission: control #34 `SOL-FM-SSSF-AGENT-LIGHTNING-SBX-POC-001`.

A gated post-`SBX-4` / pre-`SBX-8` sandbox workload: a qualified coding optimizer is given broad reversible freedom over an isolated exact-SHA copy of SSSF against a fixed benchmark, in two arms — with and without the Agent Lightning Skill — while canonical SSSF, credentials, control state and evaluator authority are proven unreachable. The initial scope is the Skill only; the full RL trainer/gateway/controller stack is not authorized.

Eligibility is `AGENT-LIGHTNING-POC-ELIGIBILITY-v1`: `SBX-3` lifecycle, `SBX-4` source/security/credential/network boundary, sufficient `SBX-5` cancellation/quiescence/recovery, sufficient `SBX-6` run/source/evidence harvesting, `BOUND-1` bounds active, and scheduling before `SBX-8`. Any unobservable axis is `CNO`.

**Registration is not execution, not admission of Agent Lightning into SSSF, not a spend authorization, and not evidence of containment.** A sandbox result never directly becomes canonical SSSF; a useful change returns through a fresh ordinary increment. Follow-on evaluation of the full framework and of a standing optimizer role remains `PLANNING_ONLY_UNTIL_SEPARATE_RULING` and is not registered here.

## FUT-016 — Deterministic control-band maintenance loop

### Status

`CANDIDATE` — disposition `ROADMAP_CANDIDATE_ONLY`, not sequenced.

Roadmap owner: `CB-1` in [`ROADMAP.md`](ROADMAP.md). Source: control #36 `future_candidate_DETERMINISTIC_CONTROL_BAND_LOOP`.

Deterministic observation reaches a typed threshold or control-band breach, which opens a bounded FirstMate task; an agent diagnoses only where reasoning is genuinely needed; the fix then follows the normal SSSF implementation, verification, review and authorization path, and the incident feeds the recurrence owner so a structural fix and regression fixture follow where warranted.

Binding constraints on any future implementation: the detector stays deterministic code and never becomes a continuously reasoning monitor agent; action tiers are pre-authorized and bounded, with production, destructive, security and spend boundaries left to existing authority; it reuses the existing unattended supervision and control-plane mechanisms rather than adding a second daemon or orchestrator; and it is implemented only once the current execution, lineage and CRP owners can support it truthfully.

No monitoring subsystem is deployed, scheduled or authorized by this registration.

## Not registered by default

Ideas discussed only hypothetically remain `EXPLORE` and do not appear here. In particular, discussion in architecture chats does not become a durable candidate merely because it was detailed or favorable.
