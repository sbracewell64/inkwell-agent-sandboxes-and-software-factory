# End-to-End Agent System Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **Benchmarking and Studying the LLM-based Agent System in End-to-End Software Development**
- arXiv: `2511.04064`

The paper is an end-to-end workflow research source, not an authorization to adopt its role taxonomy or benchmark.

## Governing interpretation

The strongest SSSF lesson is that requirement loss and authority drift across intermediate artifacts are major system-level failure modes.

> **Derived plans are hypotheses about how to satisfy requirements; they never supersede the authoritative requirement contract.**

## EXPLORE-1 — Authoritative requirement coverage ledger

Material requirements should remain individually identifiable from Engineer intent through planning, execution, verification, and terminal disposition.

Every authoritative requirement should receive a typed disposition such as implemented, deferred-with-authority, out-of-scope-with-authority, blocked/CNO, or exact successor semantics. Decomposition must not allow an omitted requirement to disappear silently.

Routing: FirstMate semantic compiler, WorkPackage design, harness scorecard.

## EXPLORE-2 — Derived plans do not supersede source requirements

Plans, designs, localization bundles, and implementation handoffs are derived artifacts. They should bind provenance to the authoritative WorkPackage/requirement IDs and remain advisory execution hypotheses.

Downstream workers retain access to the authoritative requirement contract. A derived plan may be wrong without changing what the system is required to accomplish.

## EXPLORE-3 — CODE-owned completion

Agent self-submission is a candidate terminal recommendation only.

SSSF CODE owns terminal-state folding across requirement coverage, applicable deterministic verification, semantic review, authority/CNO handling, evidence completeness, and cleanup/quiescence.

A model saying it is done cannot satisfy missing requirements or waive unmet obligations.

## EXPLORE-4 — Independent checker derivation

Builder-generated tests and self-checks are valuable diagnostic evidence but do not by themselves establish independent maker/checker verification.

Where independent checking is required, tester/reviewer obligations should derive from authoritative requirements and applicable verification/review policy under a distinct, narrower capability profile that does not inherit maker mutation authority.

Routing: DSH-6, VerificationContract/review policy, private capability registries.

## EXPLORE-5 — Global requirements remain outside local debugging cognition

Early deterministic feedback is useful. The problem is not early testing; it is allowing repeated local debugging to become the only surviving representation of the task.

Authoritative requirement state should remain durable outside model context while bounded implementation/refinement units focus locally. Context compaction or local repair must not erase the full obligation set.

## EXPLORE-6 — Controlled harness experiments

When comparing workflow/agent architecture changes, hold the rest of the execution binding constant where possible.

Examples:

- single agent vs maker/checker: hold model, ACI generation, environment, WorkPackage, budget, and scorecard constant;
- ACI-v1 vs ACI-v2: hold workflow/model constant;
- search vs no-search: hold agent/interface constant and match or explicitly account compute.

This supports causal attribution of harness improvements rather than conflating model, interface, workflow, and environment changes.

## Additional supporting observations

- Material requirement/work dependencies should survive semantic planning into deterministic WorkNode/DAG sequencing where useful.
- More agents and more planning artifacts are not inherently better; every extra role/artifact should justify itself by reducing uncertainty, enabling deterministic control, or strengthening independent evidence.
- Requirement-level completion vectors are more informative than one aggregate project score.
- Stochastic reruns may provide complementary requirement coverage, but Best-of-N remains an economics/value question and must be evaluated under bounded compute.

## Non-decisions

This research does **not** authorize:

- a Designer/Developer/Tester role taxonomy as SSSF architecture;
- a new planning-document hierarchy;
- automatic promotion of derived plans to specification authority;
- replacing deterministic acceptance with LLM requirement judges;
- changing the Docker-first / Wayfinder / DSH roadmap order.
