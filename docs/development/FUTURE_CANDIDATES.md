# Future SSSF Candidate Register

This is the durable register for future architecture and research items that have moved beyond pure conversation but are not necessarily active engineering work.

State meanings are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md).

## Register

| ID | Item | State | Decision / sequence | Notes |
|---|---|---|---|---|
| FUT-001 | Bounded autonomous DSH execution cells | SEQUENCED | `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`; long-range roadmap | SSSF owns outer authority; DSH may exercise substantial inner autonomy inside externally bounded execution cells. Cordis remains encapsulated inside DSH. |
| FUT-002 | Awesome DSH Plugin catalog as future research/reuse source | PRESERVE | none | Consult `awesome-dsh-plugin/awesome-dsh-plugin` before implementing new post-DSH harness capabilities. Catalog inclusion never implies trust or production eligibility. |
| FUT-003 | FirstMate planning-transition awareness | ACTIVE | `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`; `FP-001` producer + `FM-FP-001` consumer | Implementation is authorized on isolated branches. SSSF will emit a typed append-only planning feed; FirstMate will consume it through its existing authenticated custom-check/watch path. Only `ACTIVE` may enter engineering intake. Production landing/enablement remains held by current acceptance boundaries. |

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

## Not registered by default

Ideas discussed only hypothetically remain `EXPLORE` and do not appear here. In particular, discussion in architecture chats does not become a durable candidate merely because it was detailed or favorable.
