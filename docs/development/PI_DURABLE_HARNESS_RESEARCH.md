# Pi Durable AgentHarness Research — SSSF/DSH Inputs

## Status

- **Planning disposition:** `PRESERVE` supporting research only.
- **Primary target:** existing Sandbox → DSH implementation plan, especially DSH-0A, DSH-0B, DSH-1, DSH-2, DSH-3 and DSH-5.
- **Secondary target:** context-projection research, BOUND-1, FUT-011/FUT-013 instruction/tool-schema qualification, and future long-running execution recovery.
- **No new FUT ID. No roadmap promotion. No Pi dependency. No production install.**

Reviewed source identities on 2026-08-22:

- repository: `earendil-works/pi`
- exact reviewed `main`: `c49906ec77788625aacbdc53ebca6fbe65bd20f5`
- durable harness design at that identity: `packages/agent/docs/harness.md`
- current code/reducer and related harness implementation at that identity are supporting implementation evidence; the durable redesign remains active/transitional work rather than a completed SSSF dependency candidate.

Separately reviewed experimental source:

- PR: `earendil-works/pi#8172` — `example: tool-result pruner + spill extension`
- exact PR head: `5936a6a193ab5735069a5587002b80a7e206ed03`
- state: closed, unmerged
- evidence class: contributor experiment / research evidence, **not** accepted Pi runtime behavior or an official Pi architectural ruling against DSH.

Re-inspect then-current Pi and DSH source and pin exact identities before implementation or qualification. This document preserves design/proof inputs; it does not freeze either upstream.

---

# 1. Governing extraction rule

> **Borrow durable execution and recoverability laws; do not import another harness as SSSF authority.**

SSSF code remains the deterministic outer workflow owner. Docker remains the required production sandbox boundary. DSH may use equivalent private inner mechanisms inside an ExecutionCell, but Pi's session, lane, extension, hook, storage or runtime abstractions must not become new SSSF-visible control-plane nouns merely because they are useful internally.

The strongest extracted principle is:

> **Long-running agent execution should be designed like recoverable stateful systems, not like a conversational while-loop whose only recovery mechanism is model memory.**

---

# 2. Correction to the DSH pruning criticism

The social-media framing that DSH is simply a "permanently-lossy pruner" is too broad for then-current DSH.

Current DSH already distinguishes at least:

- an append-only session/event history that retains original execution evidence;
- a model-facing active projection that may prune or compact history;
- a spill policy for sufficiently large tool output;
- optional exact session-query/retrieval facilities.

The material remaining weakness is narrower:

> **A model-facing pruned projection can become effectively unrecoverable to the model even when the canonical original still exists durably.**

A representative risk window is a tool result large enough to be pruned under context pressure but not large enough to have been proactively spilled. The original may still exist in the append-only session log, yet the active projection may expose only head/tail text without a narrow admitted recovery handle.

Therefore SSSF should not describe current DSH historical storage itself as destructively lossy without fresh source proof. The design target is to eliminate **irretrievable lossy projections**, not to create another raw-history owner.

---

# 3. Reversible Projection Law

Adopt as a DSH design/proof input:

> **Raw execution evidence may leave active model context; it may not become irretrievable merely because its model-facing projection was reduced.**

More formally:

> **Any lossy model-facing projection must retain a durable, authorized and bounded recovery reference to the canonical observation.**

Target shape:

```text
CANONICAL RAW OBSERVATION
        │
        ├── exact identity / digest / owner
        │
        ▼
CODE-owned projection strategy
        │
        ├── deterministic reducer/query
        ├── exact indexed retrieval
        ├── bounded head/tail fallback
        └── semantic compression where genuinely needed
        │
        ▼
MODEL PROJECTION
        │
        └── durable recovery reference
                ↓
        CANONICAL RAW OBSERVATION
```

The recovery reference may resolve to an existing authoritative source such as:

- an exact DSH session/event record;
- an SSSF/DSH spill artifact;
- a source file or generated artifact with exact identity;
- an indexed exact observation store;
- another immutable evidence artifact admitted by policy.

Do **not** duplicate the original merely because the projection is lossy when a canonical exact owner already exists and can be safely retrieved.

## Spill only when needed

Preferred decision:

```text
exact canonical observation already retrievable?
        ├── yes → reference existing owner
        └── no  → create bounded spill/artifact before information is lost
                         ↓
                  lossy projection
                         ↓
                  recovery reference
```

This preserves Pi's useful recoverability idea without turning every projection into another disk copy or truth store.

## Typed projection provenance

A future internal projection record should be able to bind, where applicable:

```yaml
source:
  kind: session_event | spill | source_file | artifact | other
  ref: ...
  digest: ...
projection:
  kind: ...
  digest: ...
  original_bytes: ...
  projected_bytes: ...
omitted_ranges:
  - start: ...
    end: ...
recovery:
  kind: ...
  ref: ...
```

Human-readable markers are useful but not sufficient as the sole provenance owner. Typed source relationships should survive later compaction/projection changes.

## Bounded recovery tools

Prefer narrow CODE-owned recovery surfaces such as:

```text
observation_read(ref, offset, limit)
observation_grep(ref, pattern, limits...)
```

rather than reinjecting an entire large observation or exposing a broad unrelated session-management interface solely to recover one pruned tool result.

Recovery output itself must not enter a recursive prune/recovery loop. The implementation must either exempt admitted recovery reads where safe or preserve the original recovery chain so repeated projection remains recoverable.

---

# 4. One Effects boundary for consequential work

Pi's strongest execution-design idea is that **every consequential effect routes through one injected effects boundary**.

SSSF/DSH should preserve this principle for inner DSH execution:

> **A bounded DSH execution procedure receives one effect-capability boundary rather than direct access to storage, providers, tools, hook runners, timers or other effectful owners.**

At minimum the boundary must cover effect classes such as:

```text
Durable writes
Provider/model requests
Tool execution
Hook/interception execution
Timers / sleeps / backoff
Deferred-provider redemption/cancellation where present
Other externally observable side effects admitted later
```

Conceptual internal interface:

```text
CellEffects
  ├── durable_write(...)
  ├── provider_request(...)
  ├── execute_tool(...)
  ├── run_hook(...)
  ├── sleep(...)
  └── admitted future effects
```

The exact interface belongs to the DSH adapter/private runtime and must not expose Cordis or Pi implementation nouns to the SSSF public contract.

## Why the boundary matters

It gives CODE one complete crash/effect catalog and enables:

- authority recheck immediately before dispatch;
- intent-before-effect persistence;
- deterministic tracing/evidence;
- bounded retry/replay policy;
- cancellation propagation;
- fault injection;
- exact crash-boundary qualification;
- a manual/test drive that parks before each effect while using the same production procedure.

No side path should bypass the admitted effects boundary for an effect that can change durable or external state. A direct provider/tool/storage call outside the boundary is an architecture violation unless specifically classified as passive/read-only and proven outside the effect catalog.

---

# 5. Durable intent before effect; result after effect

Adopt as a DSH recovery law:

> **Before an effect that matters to recovery, persist an intent that binds what is about to happen and the identity of its expected result. After the effect, persist the result under that identity.**

Conceptually:

```text
intent exists + result exists
        → completed durable effect

intent exists + result absent
        → outcome unknown / recovery decision required
```

For a tool call, the intent should be able to bind at least:

- execution-cell / inner-unit / operation identity;
- tool identity/generation;
- effective arguments after authorized interception;
- provisioned result identity;
- effect/replay classification;
- applicable policy/budget identity.

A crash between effect start and durable result must never be guessed into success merely because the model previously intended the call.

## Replay/effect classification

Pi's binary replay declaration is useful, but SSSF should evaluate a richer typed class such as:

```text
READ_ONLY
IDEMPOTENT
IDEMPOTENCY_KEYED
RECONCILABLE
NON_REPLAYABLE
UNKNOWN
```

CODE owns the mapping from effect class + observed durable state to legal recovery action. A later implementation/tool generation must not silently widen replay permission; recovery should require compatibility between the recorded effect classification and the currently admitted implementation.

---

# 6. Events, Hooks and Telemetry are different authorities

Preserve this separation explicitly:

```text
Events
  observe execution

Hooks
  intercept execution

Telemetry
  observes diagnostics
```

These must remain distinct in DSH/SSSF.

## Events — observe execution

Events are passive operational observation:

- they report committed/current execution facts;
- event listeners cannot change sequencing, authority, acceptance or durable state merely by observing;
- listener failure must not silently change execution outcome;
- UI/event delivery is not the durable source of truth;
- reconnect may reconstruct from authoritative snapshot/state rather than requiring event replay when that is the chosen contract.

## Hooks — intercept execution

Hooks are explicit interception authority:

- hook registration/admission is policy-controlled;
- the hook's allowed mutation surface is typed and narrow;
- transformed values that affect later execution become durable **before** the affected execution proceeds where recovery requires them;
- failure mode is explicit; security/policy interception should fail closed where omission could widen authority;
- hook side effects outside the harness/effects boundary do not gain exactly-once semantics by magic and must use idempotency/reconciliation where needed;
- a hook cannot enlarge the ExecutionCell's outer SSSF authority.

Hooks may be internal DSH mechanisms. SSSF should consume resulting effective facts/evidence, not a public generic hook framework unless a separately proven need exists.

## Telemetry — observes diagnostics

Telemetry is passive process/runtime diagnostics:

- it cannot affect execution, acceptance or promotion;
- it is not a durable workflow owner;
- telemetry adapter/export failure must not become an execution-control mechanism unless a specific accepted safety policy says otherwise;
- default telemetry must avoid prompts, tool arguments/results, credentials and other sensitive content unless explicitly admitted;
- trace/span identity is useful correlation evidence but not a substitute for SSSF/DSH durable operation identity.

Governing boundary:

> **Observation cannot silently acquire interception authority. Interception cannot silently acquire durable-state or outer-workflow authority. Telemetry cannot become workflow control.**

This separation is especially important if DSH/Cordis plugins are later admitted, because plugin composition must not blur passive observation, interception and state ownership.

---

# 7. Deterministic effect stepping and crash qualification

Pi's manual-drive concept is a strong DSH qualification input:

> **Production and crash tests should run the same execution procedure; the test mode changes only the effect boundary, allowing CODE to park before each effect.**

For a scripted/fake provider and deterministic tools, qualification should be able to:

```text
start real execution procedure
    ↓
park before effect N
    ↓
optionally inject steer/abort/fault
    ↓
execute exactly one effect
    ↓
close/crash
    ↓
reopen durable state
    ↓
resume/reconcile
    ↓
assert terminal state/evidence
```

Where practical, crash sites should be **derived mechanically from the effect trace**, not hand-picked. Adding a new effect to the production procedure should therefore create a new crash boundary that the conformance suite must disposition.

This should complement, not replace:

- DSH Testkit lifecycle qualification;
- deterministic/mock AgentBackend/SandboxProvider tests;
- Windtunnel-style contract regression;
- real Docker process/quiescence tests;
- watched-red property controls.

## Required failure controls

Eventually cover at least:

- crash before intent write;
- crash after intent / before external effect;
- crash while effect outcome is unknown;
- crash after effect / before result write;
- crash during recovery itself;
- retry cap survives restart;
- authority/cancellation changes while parked;
- hook/interceptor crash at every admitted hook boundary;
- telemetry/event listener failure cannot alter execution;
- second recovery pass is idempotent/convergent where required.

---

# 8. Pure recovery reduction and fixed-point proof

Preserve the following principle:

> **Live inner orchestration state should be reproducible from durable owner-emitted facts, or explicitly classified as ephemeral.**

Target:

```text
durable records + canonical entries + bounded point lookups
        ↓
pure reducer
        ↓
expected ExecutionCell/inner-unit runtime state

expected state == live state
```

After resume/recovery and at selected stable boundaries, recompute the durable reduction and compare it with live runtime state. A mismatch is a defect/corruption signal, not an invitation for the model to improvise a recovery narrative.

Recovery reads themselves remain subject to the Boundedness Law: indexed/bounded reads over the still-relevant operation are preferred to rescanning all historical traffic.

---

# 9. Conversation, runtime state, observations and accounting remain separate owners

Do not overload model conversation history with execution control state.

Keep distinct, conceptually:

```text
conversation / semantic history
runtime operation state
intent/effect/recovery records
queues / pending work
raw observations and projections
usage/cost accounting
telemetry/diagnostics
```

Selected facts may be projected into model context when useful, but conversation prose is not the source from which CODE reconstructs retry count, authority, effect completion, child lifecycle or terminal state.

This strengthens the existing DSH requirement that durable historical evidence remain distinct from active model/context projection.

---

# 10. Parallel inner work: extract invariants, not the Pi `Lane` noun

Pi's lane model is useful research for concurrent long-lived work, but SSSF already has explicit run/adw/outer-attempt/execution-cell/inner-unit identities.

Do not add `Lane` as an SSSF architectural noun unless a real later seam requires it.

Preserve only the useful invariants:

- one active operation at a time per independently serialized inner unit;
- parallel units do not share mutable operation state by default;
- shared semantic history is immutable/passive where practical;
- every queued/deferred item belongs to one explicit unit;
- each unit has one mutation serialization owner;
- external effect work does not occupy the state-mutation critical section;
- cross-unit concurrency has explicit lineage, budgets and quiescence.

DSH-3 remains the stage that qualifies child/parallel semantics under SSSF identities and bounds.

---

# 11. Model × harness × tool-schema qualification

Do not preserve as fact the hypothesis that newer Claude models hallucinate foreign tool fields primarily because post-training binds them to Claude Code. The reviewed evidence does not isolate that causal mechanism from harness/schema defects.

Preserve the stronger, testable rule:

> **Coding-model quality is partly a property of model × harness × exact tool schema, not the model name in isolation.**

Qualification should therefore bind and measure, where behavior is material:

- exact model/profile;
- exact AgentBackend/DSH generation;
- exact tool schema/capability generation;
- instruction/system-prompt generation;
- malformed-call rate;
- nonexistent/invalid argument rate;
- wrong-tool selection;
- repair/retry rate;
- accepted-value/cost/latency outcome.

A changed tool schema can require requalification even when the underlying model identity is unchanged.

---

# 12. Boundedness implications

Every Pi-inspired mechanism remains subject to `docs/development/BOUNDEDNESS_LAW.md` and BOUND-1.

Explicitly audit and bound or justify:

- queue lengths and pending/deferred writes;
- retry/attempt chains;
- effect records and operation logs;
- event/watcher buffers;
- telemetry buffering/export queues;
- raw-observation spill storage and retention;
- projection/recovery requests and returned bytes;
- child/parallel inner units;
- history/query scans;
- compaction/recovery loops;
- deferred provider polling;
- cleanup/reconciliation queues.

A watcher/event buffer that can grow without a consumer is non-compliant unless it has an explicit safe-unbounded justification accepted under BOUND-1. Reversible projection must not be achieved by creating an uncontrolled retained-artifact surface.

---

# 13. DSH stage mapping

## DSH-0A — protocol/mock

Add proof inputs for representing:

- observation source identity distinct from active projection;
- reversible projection/recovery references;
- effect class/replay class;
- intent/result correlation identity;
- Events/Hooks/Telemetry authority classes without exposing Pi/Cordis nouns publicly;
- expected durable reducer state versus ephemeral runtime state.

Negative controls:

- passive event/telemetry path cannot mutate execution authority;
- hook cannot widen cell authority;
- lossy projection without a valid recovery reference is non-PASS when the evidence contract requires recoverability;
- unknown effect replay class does not become replay permission.

## DSH-0B — real Docker custody seam

Use the effects-boundary model as a crash/fault qualification seam while external SSSF process/Docker custody remains terminal authority.

Prove:

- no consequential admitted inner effect bypasses the effect boundary;
- manual/fault drive can park before each declared inner effect without changing production semantics;
- crash/reopen at effect prefixes converges or yields explicit non-PASS/CNO;
- inner durable state never substitutes for external process/container quiescence proof.

## DSH-1 — real multi-turn single-agent

Require:

- recoverable context projection for any admitted lossy observation reduction;
- canonical raw evidence retained under its proper owner;
- narrow bounded observation recovery;
- conversation distinct from operation/effect state;
- exact model × harness × tool-schema identity in qualification evidence;
- durable intent/result handling for material tool effects where recovery can encounter outcome ambiguity.

## DSH-2 — bounded refinement

Require retry/iteration counts to survive restart and remain descendants of one outer attempt. Add effect/replay classification to recovery evidence and prove crash/recovery does not reset ceilings.

## DSH-3 — children/parallelism

Apply the serialization/ownership invariants without importing the `Lane` noun. Each child/inner unit keeps explicit lineage, private mutable state, bounded queues/effects and externally enforced aggregate budgets.

## DSH-5 — richer capabilities/context

This becomes the main qualification stage for:

- compaction variants;
- observation virtualization/recovery tools;
- Context-Mode-style exact retrieval;
- Headroom semantic compression where appropriate;
- optional session-query/index implementations;
- long/background/deferred provider mechanisms;
- plugin hook/event/telemetry surfaces.

Compare raw baseline, deterministic reduction, exact retrieval, semantic compression and bounded head/tail fallback under the same evidence/outcome scorecard.

---

# 14. Candidate internal laws for later promotion

These are research-derived requirements, not yet standalone FUT items:

1. **Raw execution evidence may leave active context; it may not become irretrievable solely because the projection was reduced.**
2. **One effect boundary:** consequential inner effects route through one admitted boundary so authority, durability, tracing, cancellation and crash testing share one owner.
3. **Intent before effect; result after effect.**
4. **Unknown effect outcome remains unknown until deterministic replay/reconciliation policy disposes it.**
5. **Events observe execution. Hooks intercept execution. Telemetry observes diagnostics.**
6. **Observation cannot silently acquire interception authority; interception cannot silently acquire outer workflow authority; telemetry cannot become workflow control.**
7. **Live orchestration state must reduce from durable facts or be explicitly ephemeral.**
8. **Crash qualification should step the same production procedure at every consequential effect boundary.**
9. **Model qualification binds exact harness/tool-schema generation.**
10. **Every added durable/event/queue/recovery surface is subject to the Boundedness Law.**

Promote only if direct implementation experience shows these need a stronger canonical owner than the existing DSH plan/research documents.

---

# 15. Explicit non-adoptions

Do not adopt from Pi merely because it is useful research:

- Pi itself as SSSF/FirstMate/DSH outer control plane;
- Pi session storage or lane model as SSSF engineering truth;
- another generic extension/plugin authority layer;
- Pi-specific public hook/event APIs;
- Pi's security/trust boundary in place of Docker;
- a duplicate spill copy when an existing canonical observation is safely retrievable;
- unbounded watcher/event buffers;
- automatic replay of unknown/non-idempotent effects;
- the causal claim that a model is "bound to its vendor harness" without controlled evidence;
- contributor PR #8172 benchmark claims as accepted Pi production proof.

---

# 16. Revisit rule

Reinspect Pi and then-current DSH source before DSH-0A/0B activation and again before DSH-5 context/capability work. Specifically check:

- whether Pi's durable harness redesign is fully landed and what changed;
- whether the prune+spill experiment or equivalent became accepted Pi behavior;
- whether DSH's pruner/spill/session-query architecture changed;
- whether DSH now supplies model-visible exact recovery references for all admitted lossy projections;
- whether new plugin/event/hook/telemetry boundaries alter the ownership analysis;
- whether current DSH already implements any proposed mechanism well enough that SSSF should qualify rather than rebuild it.

Prefer deleting now-redundant planned machinery over preserving a research-derived duplicate.
