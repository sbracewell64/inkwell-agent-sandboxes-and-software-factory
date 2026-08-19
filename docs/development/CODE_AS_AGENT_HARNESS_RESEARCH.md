# Code as Agent Harness — SSSF Research Requirements

## Status

Authorized supporting research for existing SSSF planning. No new FUT item, runtime, or implementation stage is created by this document.

Source:

- **Code as Agent Harness**
- arXiv: `2605.18747v1`
- reviewed in August 2026

The paper is used as research evidence for the existing Sandbox→DSH plan, FUT-008, FUT-009, FUT-010, FirstMate semantic compilation, and future DSH-8 self-evolution work. It is not an SSSF dependency or source of engineering state.

## Governing interpretation

The useful thesis for SSSF is:

> Reliable agentic engineering comes from executable, inspectable, stateful, governed machinery around uncertain model cognition; agents reduce uncertainty while deterministic code owns stable/checkable state transitions.

This reinforces the SSSF value-creator law:

- ENGINEER owns VALUE and reserved AUTHORITY.
- AGENT owns UNCERTAINTY REDUCTION.
- CODE owns STATE TRANSITION wherever stable/checkable rules can honestly own it.

## Requirement 1 — Harness-level evaluation scorecard

The post-Docker / pre-DSH baseline must establish a reusable scorecard so later DSH/autonomy features are compared against the harness, not only final task success.

Candidate dimensions include, where observable and relevant:

- accepted-task rate;
- false-acceptance / escaped-defect rate;
- outer attempt count;
- inner attempt/refinement count;
- wall time;
- model calls;
- token and monetary cost;
- tool-call count;
- unnecessary/repeated actions;
- deterministic gate failures;
- recovery rate after failure/interruption;
- reviewer burden;
- COULD_NOT_OBSERVE rate;
- policy violations;
- process/environment cleanup failures;
- replay completeness;
- evidence completeness;
- Captain intervention count.

The scorecard is an evaluation surface, not a new state authority. Existing trace/evidence owners should emit/derive these measurements where possible.

Promotion rule: a later DSH feature should justify its added complexity with measured value against the accepted baseline.

## Requirement 2 — Explicit verifier scope

Acceptance-critical verifiers should state not only their result but their evidentiary scope.

A verifier contract should be able to express, as appropriate:

```yaml
verifier: example
proves:
  - property-A
does_not_prove:
  - property-B
applies_to:
  - exact candidate/source/environment identity
assumptions:
  - ...
result: PASS | FAIL | COULD_NOT_OBSERVE
evidence:
  - ...
```

Rules:

- green output does not imply properties outside declared scope;
- assumptions and unobserved regions remain visible;
- CNO is never silently narrowed to PASS;
- aggregate acceptance is derived by code from applicable contracts;
- semantic review interprets evidence where judgment genuinely remains but does not replace deterministic sensors.

This is supporting evidence for FUT-009/FUT-010 and existing VerificationContract work, not a separate verification layer.

## Requirement 3 — Transactional work envelopes

As SSSF reaches Docker parallelism and DSH child execution, independently bounded work should explicitly bind the state it reads, what it may write, assumptions it relies on, verification obligations, and conflict behavior.

Conceptual shape:

```yaml
reads:
  source_sha: ...
  files:
    - ...
  assumptions:
    - ...
writes:
  expected:
    - ...
requires:
  - verification-contract-A
conflict_policy:
  source_changed: STALE
  overlapping_write: BLOCK
  assumption_invalidated: REPLAN
```

The exact schema remains an implementation decision for the existing WorkNode/ExecutionCell surfaces.

Rules:

- canonical state wins over an agent's remembered belief;
- consequential actions revalidate the exact state/assumptions they were authorized against;
- stale or conflicting work does not proceed on conversational confidence;
- parallel workers synchronize assumptions as well as files;
- expected-head/source protection generalizes to all material work-envelope inputs.

Primary future checkpoints: SBX-7 and DSH-3.

## Requirement 4 — Planning as transition contract

FirstMate semantic reduction should increasingly compile actionable Engineer intent into typed state-transition contracts rather than relying on large prose plans as the execution authority.

The machine-owned portion should be able to bind, as relevant:

- goal/value reference;
- success criteria/invariants;
- exact source identity;
- relevant context references;
- permitted writes/effects;
- implementation constraints;
- verifier obligations;
- rollback/recovery points;
- authority class;
- unresolved semantic decisions.

Prose remains useful for rationale and irreducible semantic context. It should not own deterministic workflow state when a typed contract can.

## Requirement 5 — Durable state vs active model projection

The active model context is a working projection, not historical truth.

Compaction, summarization, rotation, checkpointing, or retrieval may alter the active projection but must not rewrite durable execution evidence to imply the projection is complete history.

This reinforces the Cordis-Python-derived DSH requirement already present in the Sandbox→DSH plan.

## Requirement 6 — Durable authority decisions

Captain/Browser-Sol/FirstMate decisions that materially affect engineering authority should have durable, exact-state-bound representations rather than depend on chat memory alone.

Use existing control issues, planning transitions, typed authority records, one-use landing authorization, and repository evidence. Do not create a second decision ledger merely to satisfy this requirement.

## Requirement 7 — Governed Harness Mutation Contract

Before DSH-8 self-evolution is activated, every proposed harness/runtime/instruction/workflow/plugin generation change must be represented as a bounded candidate mutation, not a live self-rewrite.

Minimum conceptual contract:

```yaml
mutation:
  target: ...
  observed_problem: ...
  proposed_change: ...
  predicted_improvement: ...
invariants_preserved:
  - ...
falsifier:
  - ...
baseline:
  - ...
held_out_evaluation:
  - ...
rollback:
  - ...
```

Rules:

- an agent may propose a candidate generation;
- deterministic qualification and applicable independent review evaluate it;
- held-out/regression evidence is required where the claimed improvement is behavioral;
- production promotion remains SSSF-owned;
- rollback is defined before promotion;
- the running generation never silently rewrites production authority.

## Negative controls / rejected interpretations

Do not:

- add a generic shared blackboard as a second SSSF truth system;
- move SSSF outer orchestration into natural-language runtime scripts;
- equate more agents with better engineering;
- treat model confidence as a termination/acceptance oracle;
- treat one successful task as evidence that a more complex harness is better;
- create new telemetry stores when the accepted trace/evidence owners can emit or derive the needed facts.

## Promotion/implementation checkpoints

These requirements become implementation-relevant only at existing checkpoints:

- post-Docker / pre-DSH baseline: harness scorecard;
- current/future VerificationContract work: explicit verifier scope;
- SBX-7 / DSH-3: transactional work envelopes;
- FirstMate semantic compiler maturation: planning-as-contract;
- DSH-1+: durable history versus active projection;
- all durable authority transitions: exact-state-bound decision representation;
- DSH-8: Harness Mutation Contract.

No roadmap order changes are authorized by this research record.