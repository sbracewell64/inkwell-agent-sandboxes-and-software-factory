# DSH Plugin Research Reference

## Status

**Future architecture/research reference only. Not a current implementation item.**

Do not interrupt serialized SSSF work to act on this catalog. Do not install plugins from it during the current baseline, Docker Sandbox, backend/model qualification, or core DSH migration work.

## Catalog

Repository:

- `awesome-dsh-plugin/awesome-dsh-plugin`
- https://github.com/awesome-dsh-plugin/awesome-dsh-plugin

Observed when this reference was recorded on 2026-08-16:

- catalog branch: `main`
- observed catalog commit: `1f00f0333366e851b0b11c92976eeda2b8b3cb99`

The observed SHA records only the catalog state seen when this reference was created. When a future capability enters the roadmap, inspect the **then-current catalog**. Any candidate plugin must be pinned and qualified at its own exact source/build/dependency identity.

## Governing instruction

> **Before implementing a new post-DSH harness capability, consult the Awesome DSH Plugin catalog for existing implementations and reusable ideas, but never infer trust or production eligibility from catalog inclusion.**

## Trust boundary

The catalog is an **idea and candidate-source index**, not an SSSF allowlist, trust registry, dependency source, or production marketplace.

The catalog warns that DSH plugins execute third-party code with the harness process's permissions. Such code may access files, credentials, and network resources; tool approvals do not sandbox plugin code. Catalog inclusion is explicitly **not** a security review.

Therefore:

- do not make a plugin marketplace part of the trusted SSSF/DSH production profile;
- do not install catalog plugins merely because they are listed;
- do not automatically update a previously qualified plugin;
- do not treat popularity, catalog inclusion, or prior qualification of another version as evidence that a candidate is safe or compatible.

## When this reference becomes actionable

Consult this catalog when a specific post-DSH capability reaches the roadmap, after the applicable prerequisites are already proven, including:

- deterministic SSSF execution and real PR landing/merge baseline;
- Docker Sandbox execution/isolation layer;
- Claude, Codex, DeepSeek, or other required backend/model qualification;
- stable SSSF-to-DSH execution-cell contract;
- DSH lifecycle, cancellation, evidence, budget, and quiescence contracts.

The catalog must not become a reason to reorder those prerequisites.

## Candidate discovery and qualification procedure

For a future SSSF requirement:

1. Discover relevant existing DSH plugins in the catalog before designing a new capability from scratch.
2. Inspect the exact current source, architecture, manifest, lifecycle hooks, dependencies, permissions, network behavior, persistence, and DSH integration seams of promising candidates.
3. Compare multiple implementations when the catalog contains meaningful alternatives.
4. Extract useful patterns, or reuse a plugin only when it fits SSSF's outer-authority / bounded-inner-autonomy law.
5. Pin every candidate to an exact Git commit plus build artifact, dependency lock, effective DSH compatibility identity, and any external executable/server identities it relies on.
6. Require deterministic contract tests and negative controls.
7. Perform security, dependency, provenance, and supply-chain review.
8. Qualify in an isolated Docker execution environment before any trusted profile admission.
9. Exercise lifecycle, cancellation, hard-timeout, process-tree/worker/transport quiescence, evidence attribution, resource ceilings, and external-effect controls.
10. Require Browser Sol semantic review before admission when the candidate materially changes DSH autonomy, authority surfaces, evidence semantics, security posture, or factory behavior.
11. Treat every plugin upgrade as a **new qualification candidate**. No automatic production upgrade follows from a prior version passing.

Admission is determined by evidence against SSSF contracts, never by catalog membership.

## Architectural boundary

The intended post-DSH model remains:

```text
SSSF deterministic outer work graph
        ↓
bounded autonomous DSH execution cell
        ↓
deterministic SSSF verification / acceptance / promotion
```

A third-party DSH plugin, if admitted, exists **inside the bounded DSH execution domain**. It gains no authority to:

- alter the SSSF outer work graph;
- create or advance outer retry/attempt state;
- weaken source/workspace custody;
- bypass SSSF budgets or hard deadlines;
- commit, promote, land, or deploy outside the SSSF-owned promotion path;
- redefine deterministic acceptance;
- set terminal SSSF workflow state.

A plugin may contain substantial inner autonomy if that autonomy is bounded, attributable, externally terminable, and still returns through SSSF-owned verification and acceptance.

## High-value areas to revisit

The following catalog areas/projects are research leads only. Their future existence, exact implementation, compatibility, security, and value must be re-observed when evaluated.

- `dsh-windtunnel` — deterministic DSH/plugin contract regression testing.
- `dsh-eval-harness` — real-agent regression evaluation.
- `qiushi-dsh-evidence-audit` — append-only/hash-linked evidence observation.
- `dsh-egress-guard` — runtime egress and redaction controls.
- `dsh-plugin-vetting` — plugin static vetting and supply-chain analysis.
- `dsh-depguard` — DSH dependency-topology protection.
- `dsh-repro` — reproducible failure bundles.
- agent-tree token/resource budgets.
- trajectory and loop anomaly detection.
- stale-safe editing.
- progressive tool discovery.
- LSP and code-intelligence capabilities.
- bounded phase-local subagent tooling.
- governed self-evolution systems such as `dsh-continual-evolve`, `dsh-rule-evolve`, and related projects.

These names are not endorsements and do not imply future admission.

## Governed self-evolution law

A running production agent must not silently rewrite its own authority or production generation.

Models may propose new versions of prompts, memory, skills, subagents, workflows, tools, or configuration. A proposal remains an immutable candidate until SSSF-controlled qualification decides whether it becomes a new production generation.

Required promotion flow:

```text
running immutable generation
        ↓
proposed candidate generation
        ↓
isolated deterministic evaluation
+ negative controls
+ security/dependency review
+ independent semantic review
+ provenance/versioning
+ rollback qualification
        ↓
SSSF-owned promotion decision
        ↓
new immutable production generation OR rejection
```

Self-evolution must never bypass SSSF outer authority, source custody, budgets, acceptance, independent review where required, versioning, rollback, or promotion.

## Evaluation standard

A plugin experiment must use the normal future-capability evaluation discipline, including at minimum:

- Problem
- Evidence
- Primitive
- Owner
- Existing owner
- Replacement
- Inputs
- Outputs
- State
- Trigger
- Verifier
- Negative control
- Failure behavior
- Rollback
- Documentation
- Documentation verifier
- Telemetry
- Promotion criteria
- Retirement
- Net complexity

Additionally record:

- exact source/build/dependency identity;
- requested DSH capability and authority scope;
- execution-cell resource/time/cost ceilings;
- child/session/process/effect attribution;
- quiescence proof;
- external-effect policy;
- upgrade qualification policy.

## Disposition

This document exists so the catalog and consultation rule survive independently of chat or human memory.

It is deliberately **not** an instruction to install, evaluate, schedule, or integrate any plugin now. It becomes relevant only when a corresponding post-DSH capability is actually admitted to the roadmap.