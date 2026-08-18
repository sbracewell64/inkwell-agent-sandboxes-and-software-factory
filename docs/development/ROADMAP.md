# Post-Baseline Roadmap

The order below deliberately separates concerns.

Planning-state semantics are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). A roadmap item may be `SEQUENCED` without being `ACTIVE`; activation begins only when a named increment enters the existing increment protocol.

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

## B4 — Durable local/free agent roster

Goal:

Add an explicit locally maintained roster without changing upstream/default staffing.

Acceptance:

- planner qualification,
- builder qualification,
- typed-output retry,
- permission enforcement,
- deterministic test+commit fixture,
- documented last-verified date/model IDs.

## B5 — Sandbox provider contract

Goal:

Extract the semantic contract currently supplied by exe.dev before replacing it.

Define provider-neutral operations:

- create
- fill/source
- execute
- readiness
- port exposure
- artifact/Git extraction
- state inspection
- destroy

Acceptance:

contract tests run against the exe.dev reference adapter.

## B6 — Free/local sandbox implementation

Implement the selected local/free provider only after B5.

Acceptance must preserve:

- host isolation,
- disposable/reproducible state,
- guest toolchain,
- no host provisioning credential in guest,
- application + observability access,
- Git harvest,
- explicit destruction,
- crash recovery.

## B7 — Observability and unattended execution

Goal:

make trace/status inspection reliable from the Windows host and suitable for supervisory automation.

## B8 — Broader ADW/agent qualification

Qualify scout/reviewer/documenter and additional ADWs with explicit fixtures.

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

## Long-range sequenced direction — FUT-001

**Planning state: `SEQUENCED`, not `ACTIVE`.**

The long-range DSH direction is governed by `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`.

Target shape:

```text
SSSF deterministic work graph
        -> bounded autonomous DSH execution cell
        -> deterministic SSSF verification / acceptance
```

### Preconditions before production DSH adoption

Do not treat DSH as the production harness until the relevant existing SSSF contracts are proven independently of DSH:

1. the current SSSF baseline can deterministically land and merge a real PR;
2. the parallel disposable Docker Sandbox execution substrate is proven;
3. Claude, Codex, and DeepSeek backend/model contracts are qualified;
4. source/workspace custody is explicit and exact;
5. lifecycle, evidence, hard-deadline, cancellation, and quiescence contracts are proven.

These prerequisites give DSH a known execution and isolation envelope against which it can be evaluated.

### DSH-0 — Stable execution-cell boundary

Start with the smallest qualification fixture:

- one exact SSSF-owned execution-cell request;
- mock adapter first;
- typed result;
- attributable evidence;
- hard timeout and termination;
- no outer-graph authority;
- no Cordis concepts exposed to SSSF.

The purpose is to prove the boundary, not to define the permanent autonomy level.

### DSH-1 — Real multi-turn single-agent cell

Admit a qualified real backend with normal multi-turn reasoning and bounded tools.

Prove model/backend identity, usage attribution, workspace integrity, evidence completeness, and forced termination.

### DSH-2 — Bounded autonomous refinement

Qualify internal refinement/repair/Ralph-style loops inside one SSSF outer attempt.

Measure first-attempt acceptance, repair burden, wall time, token/cost use, and defect rate against the simpler DSH-1 baseline.

### DSH-3 — Autonomous and parallel subagents

Qualify child-agent delegation and then parallel children.

Require hierarchical lineage, aggregate budget enforcement, authority inheritance/restriction, child evidence, and zero surviving children at cell closure.

### DSH-4 — Inner workflows and goals

Qualify DSH workflows, `tool-workflow`, and goal-driven inner execution where they improve outcomes.

An inner DSH graph may be complex, but it cannot create or advance SSSF outer graph nodes, commit/promote work, or manufacture another outer attempt.

### DSH-5 — Richer engineering capabilities

Evaluate one capability at a time against the last qualified cell baseline, including as appropriate:

- compaction;
- MCP;
- LSP/code intelligence;
- code mode;
- long-running workers/background work;
- persistent terminal capability.

Admission is evidence-driven. The existence of an internal loop or long-lived mechanism is not itself a rejection criterion; containment, attribution, budget enforcement, and quiescence are mandatory.

### DSH-6 — Product subagents

After Claude/Codex/DeepSeek execution contracts are independently known, qualify DSH use of those products as bounded inner workers.

Maker/checker independence remains an SSSF policy and may require separate execution cells even when DSH can invoke multiple products internally.

### DSH-7 — Adaptive inner orchestration

Permit DSH to choose dynamically, within its fixed cell budget and authority, whether to delegate, invoke a critic, prototype, use an admitted tool, compact, or refine again.

SSSF should control the execution cell rather than micromanage model turns.

### DSH-8 — Governed self-evolution

Research controlled self-evolution only after the preceding authority/evidence mechanisms are proven.

A running production agent may propose new prompt, memory, skill, subagent, workflow, or configuration generations. Deterministic evaluation, independent review, versioning, rollback, and SSSF-owned promotion decide whether a new immutable generation becomes production.

A production agent does not silently rewrite its own persistent authority.

## Long-range admission rule

Every DSH stage must preserve:

- SSSF ownership of outer work graph and terminal state;
- source/workspace custody;
- external resource/time/cost ceilings;
- external-effect policy;
- deterministic verification and acceptance;
- commit/promotion authority;
- forceable termination and provable quiescence;
- attributable evidence for relevant children and actions.

Later stages are not automatically implemented because earlier stages pass. Each capability must show measured value relative to the last qualified baseline and pass the candidate-evaluation standard before canonical adoption.

## Rule

Do not begin the local-sandbox replacement by editing exe.dev commands everywhere. First make source ownership explicit, then define the provider contract, then swap the implementation.

Do not begin production DSH adoption by replacing the SSSF outer graph. First prove the existing factory, Docker execution substrate, backend contracts, and DSH cell boundary; then progressively increase inner autonomy as evidence permits.
