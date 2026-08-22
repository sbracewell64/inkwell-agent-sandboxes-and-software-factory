# Agent Orchestrator Research — FirstMate / SSSF Inputs

## Status

- **Planning disposition:** `PRESERVE` supporting research only.
- **Primary target:** FirstMate supervision, control-plane reactions, Wayfinder/operational projection.
- **Secondary target:** SSSF durable-fact/reducer, bounded delivery, generation fencing, FUT-011, FUT-012, BOUND-1.
- **No new FUT ID. No roadmap promotion. No Agent Orchestrator dependency. No production install.**

Reviewed source identity on 2026-08-22:

- repository: `Untrivial-ai/agent-orchestrator`
- exact reviewed `main`: `11c1b5caee309e13fa18019fd3145962aa5c420f`
- license: Apache-2.0
- principal reviewed surfaces: `docs/architecture.md`, `docs/backend-code-structure.md`, `docs/STATUS.md`, `docs/telemetry.md`, session/lifecycle/domain/CDC code, delegation code, status derivation, worktree adapter structure, and `.agents/skills/bug-triage/SKILL.md`.

Re-inspect then-current upstream and pin exact source identity before copying/adapting implementation details.

---

# 1. Architectural ruling

Agent Orchestrator (AO) is a mature research source for **supervisory control-plane mechanics**. It should not become another orchestrator inside FirstMate or SSSF.

The strongest reusable pattern is:

```text
AUTHORITATIVE FACTS
GitHub / SSSF / workers / control plane
        ↓
observers
        ↓
normalized durable facts
        ↓
deterministic reducers
        ├─ ownership
        ├─ applicability
        ├─ reaction set
        └─ attention projection
        ↓
bounded effect delivery
        ├─ worker feedback
        ├─ Browser Sol escalation
        └─ Captain escalation
        ↓
Wayfinder / operational view
```

Governing extraction rule:

> **Persist authoritative facts and reaction state; derive attention and display status. Do not turn the dashboard, Kanban column, notification, or agent narration into a second state authority.**

This fits the current FirstMate↔Browser-Sol control-plane model better than adopting AO itself.

---

# 2. Durable facts; derived status

AO intentionally persists a small set of lifecycle/SCM facts and derives user-facing states such as working, CI failed, changes requested, mergeable, needs input, and no-signal at read time.

SSSF/FirstMate should preserve this rule:

> **Attention is a projection, not durable truth.**

The authoritative inputs remain concrete facts such as:

- exact repository / PR / commit / expected head;
- current checks and check identities;
- review decisions / unresolved review facts;
- worker activity / liveness observations;
- current control-plane classification/ruling/disposition;
- accepted execution state and evidence state;
- authority owner and pending decision class.

A Wayfinder/FirstMate board can then derive compact states without persisting them as independent truth.

Candidate attention vocabulary:

```text
WORKING
WAITING_EXTERNAL
CI_FAILED
REVIEW_ACTIONABLE
ENGINEERING_DECISION
CAPTAIN_REQUIRED
READY_FOR_NEXT_GATE
NO_SIGNAL / CNO
```

These are operational projections only. The reducer must be able to explain each projection from exact underlying facts.

## No-signal / CNO discipline

AO's status reducer does not confidently call a signal-capable session idle after a grace window when no activity signal has ever arrived; it derives `no_signal` instead.

SSSF/FirstMate extraction:

> **Missing expected telemetry/observation is not positive idle state.**

When an owner is expected to report but observation is absent beyond the accepted proof window, derive `NO_SIGNAL` / `CNO`, not `IDLE`, `DONE`, or `READY`.

---

# 3. Reaction records should be first-class bounded state

AO's lifecycle layer contains useful dedup/signature/attempt machinery for returning CI/review/conflict feedback to the worker that owns a PR. SSSF/FirstMate should generalize that into an explicit reaction record rather than treating a chat message as the reaction itself.

Target conceptual shape:

```yaml
reaction:
  id: ...
  subject:
    kind: pr
    identity: ...
    expected_head: ...

  cause:
    kind: ci_failure

  signature: ...

  owner:
    worker_id: ...

  applicability:
    ...

  attempts:
    used: ...
    max: ...

  resolution:
    ...
```

Additional fields may be required in the accepted implementation, including:

- source fact/provenance refs;
- exact generation/reducer-policy identity;
- delivery target/class (`worker`, `browser-sol`, `captain`, external dependency);
- last delivery observation;
- next eligible retry time where applicable;
- superseded/stale reason;
- terminal disposition.

A reaction is not an agent prompt. The prompt/message is one delivery projection of an authoritative reaction.

## Signature purpose

A reaction signature should bind the material condition that makes a reaction distinct, such as:

```text
subject identity
+ exact relevant head/generation
+ cause class
+ material evidence identity
+ recipient/owner where policy requires it
```

If the same condition is observed repeatedly, the reaction should converge on the same identity/signature rather than manufacturing repeated work.

If the material condition changes, a new generation/signature becomes eligible.

---

# 4. Derive all applicable reactions before delivering any

AO contains a concrete bug-history lesson: one actionable PR condition (for example CI failure) must not hide an independent condition (for example review feedback or merge conflict). Current lifecycle code builds all applicable nudges and then sends each independently.

Adopt this as a control-plane law:

```text
observe current PR
        ↓
persist exact facts
        ↓
derive ALL applicable reactions
        ↓
for each independent reaction:
   identity
   applicability
   recipient/owner
   signature
   delivery state
   retry ceiling
        ↓
deliver to owning worker / ruling authority
```

Do **not** implement reaction logic as a mutually exclusive `if/else` chain unless policy proves the causes are genuinely exclusive.

A failure while computing or delivering reaction A must not silently suppress independent reaction B. Each reaction has its own state and retry/disposition path.

This is particularly relevant to FirstMate's existing CI watch and Browser-Sol control routing.

---

# 5. Owner-directed feedback

AO keeps PR/CI/review feedback attached to the worker session that owns the work. That is preferable to broadcasting failures into an ambient coordinator conversation and hoping the right agent notices.

FirstMate target:

```text
fact / reaction
      ↓
deterministic ownership resolution
      ↓
current responsible worker / PR owner
      ↓
bounded feedback delivery
```

If ownership is ambiguous, resolve from authoritative task/PR/branch/execution state before delivery. Do not infer owner merely from who most recently spoke.

If the condition requires architectural judgment instead of implementation work:

```text
BROWSER_SOL
```

If it genuinely requires Captain authority:

```text
CAPTAIN_REQUIRED
```

The reaction owner/recipient is therefore an authority classification, not merely an inbox address.

---

# 6. Bounded live projection over durable truth

AO's CDC/SSE design contains a strong pattern: durable changes live in a change log; live delivery is a projection. The poller drains bounded batches, the SSE transport has a bounded live buffer, and when the live consumer cannot keep up the stream is closed instead of silently dropping events; the consumer catches up from durable truth on reconnect.

Adopt the generalized law:

```text
durable truth
    ↓
bounded live projection
    ↓
consumer

consumer too slow
    ↓
DO NOT grow forever
DO NOT silently drop
    ↓
disconnect / restart projection
    ↓
catch up from durable truth
```

This is a direct BOUND-1 application.

For FirstMate/Wayfinder/control-plane consumers:

- live notification/event buffers have explicit bounds;
- overflow behavior is deterministic;
- live delivery loss never becomes authoritative data loss;
- durable cursor/catch-up source is explicit where replay is required;
- a stale cursor cannot fabricate successful continuity;
- each consumer's catch-up semantics are independently testable.

Do not add CDC merely because AO uses SQLite CDC. Reuse the authoritative stores already present; the important pattern is **durable source + bounded live projection + replay/catch-up**, not the technology.

---

# 7. Observer → durable fact → reducer → effect

AO separates external observation from durable lifecycle updates and from user-facing status. Preserve that separation.

Target FirstMate/SSSF shape:

```text
observer
  reads GitHub / worker / CI / review / runtime fact
        ↓
normalizer
  produces typed observation
        ↓
state owner
  persists/folds authoritative durable fact
        ↓
reducer
  computes applicability / ownership / reactions / attention
        ↓
effect delivery
```

An observer should not directly decide product/engineering state merely because it discovered a fact.

This is compatible with the Pi-derived boundary:

```text
Events observe execution
Hooks intercept execution
Telemetry observes diagnostics
```

and extends it at the supervisory level:

> **Observation supplies facts; reducers decide deterministic applicability; effect owners deliver bounded consequences.**

---

# 8. Generation fencing and stale-controller protection

AO uses multiple generation/fence concepts so an old controller/runtime cannot continue mutating a session after replacement. Its durable session metadata distinguishes controller generation from runtime launch generation, and interface transitions are committed/fenced rather than inferred from process liveness.

This strongly reinforces existing SSSF/FirstMate expected-head and stale-state discipline.

General law:

> **Any actor that can outlive replacement must carry a generation/authority token that the current state owner can reject.**

Applicable future surfaces include:

- FirstMate worker generations;
- PR/review reaction deliveries;
- DSH inner controllers;
- browser/preview controllers;
- remote sandbox/executor owners;
- provider conversations when a controller handoff occurs.

A stale actor may remain alive physically; it must be unable to mutate authoritative state.

---

# 9. Durable controller handoff is useful research, not an SSSF feature today

AO's Chat↔TUI interface transition is unusually rigorous:

- one committed controller at a time;
- target preflight before commit;
- drain versus interrupt policy;
- durable transition checkpoints;
- source intake fence;
- generation fencing;
- durable outbox across the no-controller gap;
- rollback to the last committed mode if target startup fails;
- restart reconciliation after daemon death.

This is useful research for any future FirstMate/DSH runtime-controller replacement, but no current requirement justifies adding a generic controller-handoff subsystem to SSSF.

Preserve the narrower law:

> **Replacing a controller is a state transition with a commit point, fencing, rollback and message custody—not a process restart heuristic.**

---

# 10. Worktree isolation is useful operationally but not a security boundary

AO gives workers separate branches/worktrees and preserves work when cleanup cannot safely prove it disposable. Those are good workspace-isolation and source-ownership ideas.

SSSF remains stronger:

- Docker is the production sandbox/security boundary;
- credential-bearing canonical source stays outside worker access;
- exact commit/tree identity is authoritative;
- Git worktrees alone do not constitute hostile-code isolation.

Do not regress SSSF to AO's trusted-host model simply because AO supports many harnesses conveniently.

---

# 11. Browser capability pattern

AO stores a one-way verifier for a per-session random browser capability while keeping the bearer token itself out of durable storage. That is a useful capability design pattern:

> **Persist enough to verify an ephemeral capability after restart; do not persist the bearer secret merely for convenience.**

Potential future relevance:

- worker-scoped browser bridges;
- DSH capability tokens;
- temporary effect grants;
- local control bridges.

Any adoption still requires SSSF capability/effect policy and Docker boundary review.

---

# 12. FirstMate operational projection / Wayfinder

AO's Kanban is useful primarily as an information-design reference.

The future FirstMate/Wayfinder operational surface should present the smallest actionable projection over authoritative facts, for example:

```text
WORKING
WAITING_EXTERNAL
CI_FAILED
REVIEW_ACTIONABLE
ENGINEERING_DECISION
CAPTAIN_REQUIRED
READY_FOR_NEXT_GATE
NO_SIGNAL / CNO
```

A card/item should expose enough provenance to answer:

- what exact artifact/work is this;
- who owns the next action;
- why is attention required;
- what exact evidence caused that status;
- what reaction is pending/already delivered;
- whether the observation is current for the expected head/generation;
- what gate follows after resolution.

The board must not create or mutate engineering truth by moving cards between columns. Columns are reducer output.

This supports the existing principle that Wayfinder is an operator/intent surface, not an engineering-state authority.

---

# 13. Operational instruction drift: important FUT-011 evidence

AO's public `.agents/skills/bug-triage/SKILL.md` was stale at the reviewed commit relative to current architecture/status documentation. It instructs triagers that sessions use a Zellij runtime and tells them to inspect `zellij list-sessions`, while current architecture/status identifies tmux on Unix and ConPTY on Windows for TUI runtime behavior.

This is strong real-world evidence for FUT-011:

> **An operational skill can become actively wrong while continuing to parse and look authoritative.**

Therefore any SSSF/FirstMate skill that names implementation facts such as:

- runtime technology;
- port;
- file path;
- provider capability;
- command syntax;
- schema field;
- current workflow owner;

must either:

1. derive those facts mechanically at invocation time;
2. consume a generated/current reference;
3. or be guarded by a drift validator tied to the authoritative code/config.

A skill-generation digest alone proves which stale instructions were used; it does not prove they were true.

This also supports FUT-012: mechanically derivable operational documentation should be generated or checked where practical.

---

# 14. Boundedness findings

AO includes several good bounded surfaces:

- bounded CDC poll batches;
- bounded SSE live buffer;
- bounded history pages;
- bounded browser network capture;
- telemetry event rate limiting and local retention pruning;
- bounded task-title refinement timeout;
- bounded review feedback retries in at least some reaction classes.

SSSF should preserve the pattern, not the exact numbers.

Every adopted equivalent remains subject to `BOUNDEDNESS_LAW.md`, including:

- reaction count and attempts;
- change/event log retention;
- live delivery buffers;
- observer polling work;
- owner-resolution scans;
- notifications;
- worker feedback queues;
- pending Browser-Sol/Captain escalations;
- Wayfinder projections;
- browser/session capability state.

An AO mechanism that uses an unlimited or sentinel retry value cannot be copied until SSSF explicitly classifies and proves its bound/safety under BOUND-1.

---

# 15. Architecture-boundary lessons

AO's backend docs explicitly assign package ownership and dependency direction. The useful SSSF extraction is not to copy its package tree but to mechanically preserve ownership boundaries where possible.

Useful laws:

- durable domain facts do not depend on transport/UI types;
- adapter implementations are leaf dependencies;
- observers do not become workflow decision owners;
- display/read-model assembly does not become durable state authority;
- command engines own multi-step mutations; protocol layers stay thin;
- ports exist only for real replaceable capability boundaries.

This reinforces FUT-009/FUT-010 and the earlier Factory research finding that architectural import/dependency laws should be mechanically checked where practical.

---

# 16. Telemetry disposition

AO remote product telemetry is not an SSSF adoption candidate. AO uses PostHog in production packages and documents opt-out controls plus 30-day local operational-event pruning.

SSSF/FirstMate should preserve only the useful principles:

- allowlisted structured telemetry fields;
- prompts/source/tool content excluded by default;
- bounded rates and retention;
- operational telemetry separate from engineering truth and workflow control;
- external telemetry/export is optional and must not be required for local correctness.

No new external telemetry service or paid dependency is authorized by this research.

---

# 17. Explicit non-adoptions

Do not adopt from AO:

- AO itself as a second FirstMate/SSSF orchestrator;
- AO's project orchestrator as competing planning authority;
- AO session DB as SSSF truth;
- Kanban/card position as stored workflow state;
- tmux/conpty/worktree host execution as SSSF security containment;
- automatic broad agent-adapter expansion merely to match AO's catalog;
- host-trusted reviewer execution as independent review proof;
- PostHog/product telemetry;
- stale operational skills or prose runtime facts without drift controls;
- a generic controller-handoff subsystem without a demonstrated requirement;
- unbounded reaction retry semantics.

---

# 18. Revisit / application points

Use this research when:

1. FirstMate's unattended CI/review/control-plane reaction system is next revised;
2. Wayfinder's operational/attention view is commissioned beyond the initial transport proof;
3. a durable worker/controller handoff becomes a real requirement;
4. FUT-011 instruction-artifact governance is evaluated for promotion;
5. FUT-012 derived documentation is evaluated;
6. BOUND-1 audits live projections, feedback queues, observers and reaction chains.

At those points, inspect then-current AO source and compare against the exact reviewed commit above. Prefer extracting a smaller deterministic pattern into existing FirstMate/SSSF owners rather than creating a new service or control plane.

---

# 19. Concise preserved laws

1. **Persist facts; derive attention.**
2. **Derive every independent applicable reaction before delivery.**
3. **A reaction has identity, subject/head, cause, signature, owner, applicability, attempt bound and resolution state.**
4. **Deliver reactions to the authoritative owner, not the loudest/current conversation.**
5. **Live projection is bounded; on overflow reconnect and catch up from durable truth rather than grow forever or silently drop.**
6. **Missing expected signal becomes NO_SIGNAL/CNO, not idle confidence.**
7. **Stale controllers/workers are fenced by generation even if still physically alive.**
8. **Operational views are projections and cannot become state authority.**
9. **Operational skills that encode current implementation facts require drift controls.**
10. **Every observer, reaction queue, delivery retry, event buffer and projection remains subject to the Boundedness Law.**

---

# 20. Additional authorized extracts

## 20.1 Capability coexistence does not prove continuity/equivalence

AO permits Chat↔TUI handoff only where the adapter proves the two identities refer to the same native provider conversation. Merely supporting both interfaces is not enough.

General FirstMate/SSSF law:

> **Two capabilities can coexist without being semantically interchangeable. If continuity depends on equivalence, prove the equivalence.**

Apply this to:

- host-native CLI versus structured provider protocol;
- TUI versus Chat controllers;
- two AgentBackend modes for one provider;
- host-native versus Docker-hosted agent bindings;
- alternate tool schemas for the same model;
- resumed/replaced controllers claiming continuity of one conversation or execution identity.

Do not carry history/evidence/authority across a boundary merely because product names match.

## 20.2 Keep non-authoritative semantic enrichment off critical state-transition paths

AO treats worker spawn as the commit point and performs task-title refinement asynchronously with a bounded timeout. Failure to improve a human-facing title does not invalidate the already-created worker.

General FirstMate law:

> **Do not put non-authoritative semantic cosmetics on the critical path of a deterministic state transition.**

Potential examples:

- display title;
- human-readable summary;
- board label;
- optional categorization;
- explanatory prose.

Commit authoritative work first when safe. Semantic enrichment may follow independently and must not silently change scope, authority, or acceptance.

## 20.3 Tracker/issue/PR text is untrusted task data

AO's current worker prompt explicitly marks fetched tracker/SCM issue context as user-authored external text that cannot override standing instructions or repository safety rules.

Preserve the stronger SSSF/FirstMate distinction:

```text
authenticated typed control envelope / role
        ≠
free-form issue / PR / review / comment text
```

A control issue may validly transport a typed `fm-sol-control/v1` escalation or ruling, but arbitrary text quoted inside it cannot grant itself authority. Repository/PR/comment content remains data interpreted under the existing authority model.

This reinforces the existing AgentDojo law that untrusted content cannot grant itself effect authority.

## 20.4 Reaction policy should suppress expected stack noise without hiding actionable defects

AO's stack-aware PR logic avoids sending merge-conflict nudges for a child PR whose target is another still-open parent PR when that conflict is expected from stack topology. At the same time, actionable child signals such as failing CI or requested changes remain visible.

FirstMate extraction:

> **Suppress mechanically expected noise only when topology/policy proves it non-actionable; do not suppress independent actionable evidence.**

For stacked/dependent work, reaction policy should understand dependency position rather than blindly treating every raw provider state as an operator/worker intervention.

## 20.5 Material evidence changes, not polling cycles, create new reactions

AO's persisted reaction signatures survive restart and suppress repeated identical nudges. The valuable general rule is:

> **A polling cycle is not an event. A material fact/signature change is an event.**

FirstMate should key reaction eligibility to exact current evidence/generation rather than elapsed polling cycles. Re-observation of unchanged evidence converges on the same reaction identity.

---

# 21. FirstMate priority shortlist from AO

When the relevant FirstMate owners are next revised, inspect existing implementation first and consider only demonstrated gaps in this order:

1. derived attention projection from authoritative facts;
2. `NO_SIGNAL` / CNO when an expected observation channel is silent;
3. first-class reaction records with exact subject/head/cause/signature/owner/attempt state;
4. derive all independent applicable reactions before any delivery;
5. deliver repair feedback to the current responsible worker by default;
6. generation-fence stale worker/controller callbacks;
7. bounded live notification with durable replay/catch-up;
8. durable message custody across any real owner/controller handoff;
9. qualify identity/capability equivalence before claiming continuity;
10. keep cosmetic semantic enrichment off critical state transitions;
11. treat free-form tracker/SCM content as untrusted data under typed authority;
12. freshness-qualify operational skills against the implementation contracts they describe.

None of these authorizes a second daemon, database, Kanban state machine, telemetry service, or AO installation.
