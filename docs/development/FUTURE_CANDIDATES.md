# Future SSSF Candidate Register

This is the durable register for future architecture and research items that have moved beyond pure conversation but are not necessarily active engineering work.

State meanings are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md).

## Register

| ID | Item | State | Decision / sequence | Notes |
|---|---|---|---|---|
| FUT-001 | Bounded autonomous DSH execution cells | SEQUENCED | `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`; long-range roadmap | SSSF owns outer authority; DSH may exercise substantial inner autonomy inside externally bounded execution cells. Cordis remains encapsulated inside DSH. |
| FUT-002 | Awesome DSH Plugin catalog as future research/reuse source | PRESERVE | none | Consult `awesome-dsh-plugin/awesome-dsh-plugin` before implementing new post-DSH harness capabilities. Catalog inclusion never implies trust or production eligibility. |
| FUT-003 | FirstMate planning-transition awareness | DECIDED | `ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`; unsequenced | FirstMate will consume typed planning transitions through its existing authenticated custom-check/watch path; it must never derive execution authority from planning prose, and only `ACTIVE` may enter engineering intake. |

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

`DECIDED`

Governing decision:

[`ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`](../decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md)

Decision basis evaluated against FirstMate `main` at observed commit:

`f4e69d6ce411750b55fc9f186f60ce0e8b0cd786`

Implementation remains **unsequenced and inactive**. No FirstMate watcher change, task, or engineering intake is authorized by this decision alone.

### Problem

Browser Sol now maintains a deliberate SSSF planning lifecycle (`EXPLORE -> PRESERVE -> CANDIDATE -> DECIDED -> SEQUENCED -> ACTIVE -> PROVEN`). FirstMate should learn about durable planning promotions without requiring the Captain to relay them, but it must not infer work from prose or treat every planning-document edit as authorization.

Without a typed signal, the alternatives are both undesirable:

- manual Captain transport of planning changes; or
- FirstMate periodically rereading planning prose and deciding semantically whether a change is actionable.

The second would collapse the planning/engineering authority boundary we created.

### Evidence and existing primitives

FirstMate already has the required transport foundations:

1. `bin/fm-watch.sh` owns one continuous supervision cycle and runs authenticated `state/*.check.sh` checks on its existing slow cadence. A validated custom check that returns empty output stays silent; nonempty output is durably queued as a `check:` wake and closes that watcher cycle.
2. `bin/fm-check-lib.sh` validates custom checks against a private hash-bound trust record and executes a private snapshot rather than mutable live bytes.
3. `bin/fm-check-register.sh` intentionally binds a custom check identity to its current bytes.
4. `bin/fm-remote-delta-read.sh` already implements the continuity algorithm needed for an append-only feed: byte offset plus prefix SHA-256, bounded complete-line reads, and explicit `continuity-broken` results on truncation, replacement, or prefix mutation rather than silent rebasing.
5. `bin/fm-procevent-remote-reply.sh` demonstrates durable cursor and idempotent-ingestion patterns over that delta contract, but process-event itself is designed for blocking external-process sources. A GitHub planning branch is periodic repository state, so adding a blocking process source would duplicate the watcher's polling role.

### Decided primitive

Use **one registered FirstMate custom check** as the outer detector, running under the existing `fm-watch` cadence. Do not create another polling daemon.

When implemented, the SSSF planning side will expose a small append-only transition feed, intended as:

`docs/development/PLANNING_EVENTS.jsonl`

The feed is a notification index, not a new source of truth. Each event points to the authoritative planning documents and exact Git identity.

Example shape:

```json
{"schema":"sssf-planning-event/v1","event_id":"plan-20260818-0007","item_id":"FUT-003","from":"CANDIDATE","to":"DECIDED","source_commit":"<sha>","authoritative_refs":["docs/development/FUTURE_CANDIDATES.md","docs/decisions/<adr>.md"],"actionability":"awareness"}
```

An activation event would instead carry `to: "ACTIVE"`, a named increment identity, and `actionability: "engineering"`.

FirstMate will keep a private cursor for the feed using the same semantic fields as the existing remote-delta contract:

- byte offset;
- prefix SHA-256;
- last handled event identity;
- exact observed SSSF planning ref/commit.

The custom check will surface the oldest unseen valid event and leave later events for later checks, preserving order and bounding each wake.

### Authority split

**Browser Sol owns:**

- planning-state promotion;
- updates to `FUTURE_CANDIDATES.md`, ADRs, and `ROADMAP.md`;
- future append of the corresponding transition event;
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

### Evaluation record

| Field | Evaluation |
|---|---|
| Problem | FirstMate lacks deterministic awareness of Browser-Sol-managed planning promotions without Captain relay. |
| Evidence | Existing planning lifecycle explicitly separates planning from activation; FirstMate already has authenticated watch/check and durable cursor primitives but no SSSF planning adapter was found. |
| Primitive | Append-only SSSF planning transition feed + one authenticated FirstMate custom-check adapter. |
| Owner | Browser Sol owns promotion/event creation; CODE owns detection/continuity/state classification; FirstMate handles the resulting typed awareness/intake event. |
| Existing owner | Manual relay or ad hoc repository inspection. |
| Replacement | Removes Captain relay for promoted SSSF planning state and prevents broad semantic polling of planning prose. |
| Inputs | Exact SSSF repository/ref, `PLANNING_EVENTS.jsonl`, cursor offset/hash, event schema, referenced source commit. |
| Outputs | One bounded typed planning-event wake, or silence when no unseen event exists. |
| State | Append-only feed in SSSF; private FirstMate cursor/receipts under FirstMate state. |
| Trigger | Existing `fm-watch` custom-check cadence; no second daemon. |
| Verifier | Hermetic custom-check tests with a fake planning source plus watcher integration tests. |
| Negative control | No appended event => no wake; tampered registered check => rejected; changed/truncated prefix => continuity break; duplicate event => no duplicate transition effect; non-`ACTIVE` event => no task; malformed or stale `ACTIVE` reference => no activation. |
| Failure behavior | Do not advance cursor on malformed/unavailable/continuity-broken input. Surface continuity/security failure on a bounded cadence; never silently rebase. |
| Rollback | Remove/retire the registered planning check and its private cursor. SSSF planning docs remain valid and manually inspectable. |
| Documentation | SSSF planning lifecycle/candidate docs; FirstMate watcher/process-event or new planning-awareness doc as appropriate. |
| Documentation verifier | Tests assert event-state semantics and that only `ACTIVE` can reach intake. |
| Telemetry | Detection latency, duplicate wakes, continuity failures, invalid events, awareness events, attempted/accepted activations. |
| Promotion criteria | Contract tests prove silence, ordering, dedupe, continuity-break refusal, trusted-check enforcement, `ACTIVE`-only intake, stale-source protection, and rollback. |
| Retirement | Manual Captain transport of promoted SSSF planning changes. |
| Net complexity | One small feed + one adapter/cursor contract, reusing existing watcher infrastructure; no new service or scheduler. |
| Authority class | Browser Sol planning authority -> CODE transport -> FirstMate engineering intake only at `ACTIVE`. |
| State transition | Adds a deterministic notification bridge between planning lifecycle transitions and the existing increment intake boundary; does not add a new SSSF execution state. |
| Determinism boundary | Code parses exact event state; FirstMate cannot reinterpret a non-`ACTIVE` promotion as work authorization. |
| Provenance | Event names exact source commit and authoritative refs; FirstMate cursor and acknowledgement bind handling to the observed feed prefix/event identity. |

### Alternatives considered

#### Process-event adapter

Not selected as the primary detector. Process-event is well suited to a blocking external source; a GitHub planning branch must still be polled somewhere. Wrapping that polling in a blocking child would duplicate the existing watch cadence and add lifecycle machinery without clear value.

The useful part to reuse is the process-event family's cursor, acknowledgement, and continuity discipline.

#### Semantic reread of planning docs

Rejected. A document edit is not a planning-state transition, and `SEQUENCED` is not `ACTIVE`. Letting a model infer actionability from arbitrary diffs would weaken the explicit promotion protocol.

#### Separate planning daemon

Rejected. FirstMate already has the continuous watcher and custom-check lifecycle. A second polling owner would increase concurrency, lifecycle, and quiescence complexity for no demonstrated benefit.

### Sequencing status

`UNSEQUENCED`

The architecture is decided, but implementation should not enter `ROADMAP.md` or FirstMate engineering transport until the planning branch itself is ready to become part of the accepted SSSF documentation surface and a bounded FirstMate increment is explicitly chosen.

## Not registered by default

Ideas discussed only hypothetically remain `EXPLORE` and do not appear here. In particular, discussion in architecture chats does not become a durable candidate merely because it was detailed or favorable.
