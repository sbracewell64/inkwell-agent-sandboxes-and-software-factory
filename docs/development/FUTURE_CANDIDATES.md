# Future SSSF Candidate Register

This is the durable register for future architecture and research items that have moved beyond pure conversation but are not necessarily active engineering work.

State meanings are defined in [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md).

## Register

| ID | Item | State | Decision / sequence | Notes |
|---|---|---|---|---|
| FUT-001 | Bounded autonomous DSH execution cells | SEQUENCED | `ADR-0004-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`; long-range roadmap | SSSF owns outer authority; DSH may exercise substantial inner autonomy inside externally bounded execution cells. Cordis remains encapsulated inside DSH. |
| FUT-002 | Awesome DSH Plugin catalog as future research/reuse source | PRESERVE | none | Consult `awesome-dsh-plugin/awesome-dsh-plugin` before implementing new post-DSH harness capabilities. Catalog inclusion never implies trust or production eligibility. |

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

## Not registered by default

Ideas discussed only hypothetically remain `EXPLORE` and do not appear here. In particular, discussion in architecture chats does not become a durable candidate merely because it was detailed or favorable.
