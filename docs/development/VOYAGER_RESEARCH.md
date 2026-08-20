# Voyager Research

## Status

`EXPLORE` / supporting lifelong-skill research only.

This document preserves SSSF-relevant findings from:

- **Voyager: An Open-Ended Embodied Agent with Large Language Models**
- arXiv: `2305.16291`

The paper is an embodied lifelong-learning research source, not an authorization to give SSSF agents self-directed product/roadmap goals or to adopt Voyager.

## Governing interpretation

Voyager's strongest transferable idea is an accumulating library of reusable executable skills refined through environment feedback. For SSSF, reusable skills must be qualified software artifacts, and self-selected curricula must remain inside explicitly authorized experimentation envelopes.

> **An agent may propose and refine reusable skills; CODE and normal engineering gates decide whether a skill becomes reusable authority-bearing capability.**

## EXPLORE-1 — Reusable executable skills are qualified artifacts

Repeated semantic procedures may eventually become reusable executable skills/tools rather than being rediscovered in every model context.

A skill candidate should bind exact source, implementation digest, interface/inputs/outputs, capability/effect class, dependencies, tests/validators, security constraints, and qualification provenance.

## EXPLORE-2 — Verify before skill admission

Do not add a generated program to a reusable skill catalog merely because its generating model or semantic critic says the task succeeded.

For SSSF, skill admission requires applicable deterministic execution/verification and independent semantic/security review where needed. Model self-verification is advisory evidence only.

## EXPLORE-3 — Skill versions are immutable generations

A refined skill becomes a new candidate generation rather than silently mutating an already-qualified skill. Consumers bind the exact admitted generation/digest they executed.

Promotion/rollback follows normal SSSF evidence discipline.

## EXPLORE-4 — Environment/error feedback supports bounded refinement

Execution feedback, deterministic errors, and observed environment state are high-value inputs to semantic refinement loops.

CODE owns loop count, budget, failure classification, continuation, and terminal state; AGENT proposes revised implementation inside those bounds.

## EXPLORE-5 — Skill retrieval is advisory selection, not authority

Embedding/semantic retrieval can identify potentially relevant reusable skills. Retrieval results must return exact skill identities/generations and remain subject to capability/authority/applicability checks before use.

Similarity does not authorize execution.

## EXPLORE-6 — Composition requires dependency closure

A composite skill that invokes other skills should bind its exact dependency graph/generations. Qualification must establish that dependencies are admitted and compatible; a composite skill cannot smuggle in unqualified capabilities through transitive calls.

## EXPLORE-7 — Reuse/generalization requires fresh-frontier qualification

A skill that works on the episode/world where it was created has not yet proven portability. Reusable skill generations should be tested on held-out/fresh contexts appropriate to their claimed applicability.

This routes naturally to the existing replay vs fresh-frontier evaluation discipline.

## EXPLORE-8 — Failed attempts are useful learning evidence, not executable memory

Failed tasks, error traces, and unsuccessful skill candidates can inform later semantic reasoning and skill generation, but remain diagnostic/history evidence rather than admitted capabilities.

## EXPLORE-9 — Self-directed curricula are restricted to isolated experimentation

Voyager's automatic curriculum is useful evidence that a model can propose progressively useful learning objectives from state and prior successes/failures.

In SSSF this pattern is appropriate, if at all, only inside DSH-8/evolution research with a CODE-owned objective envelope, budget, allowed capability set, immutable evidence, and separate promotion gates.

It may not create production intent, roadmap priority, acceptance criteria, or Captain authority.

## EXPLORE-10 — Stable successful skills should face a CODEward test

When a reusable semantic skill becomes stable/checkable, determine whether its behavior should remain an agent skill or be simplified into deterministic code/tooling. The skill catalog should not become an ever-growing substitute for mechanization.

## Routing

- `FUT-001`, especially DSH-5 richer capabilities and DSH-8 governed evolution.
- `FUT-011` skill/instruction qualification and retirement/mechanization.
- Replay/fresh-frontier harness scorecards for reusable skill promotion.

## Non-decisions

This research does **not** authorize:

- Voyager adoption;
- an autonomous production curriculum;
- model self-verification as skill admission authority;
- mutable shared skill memory without generations/provenance;
- unreviewed generated code as reusable capability;
- roadmap or FUT state promotion.
