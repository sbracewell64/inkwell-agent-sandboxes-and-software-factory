# DSPy Instruction-Compilation Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines**
- arXiv: `2310.03714`

The paper is an instruction/program-optimization research source, not an authorization to adopt DSPy, fine-tune models, or allow active prompts to self-modify in production.

## Governing interpretation

Separate the stable semantic contract from its model-specific prompt realization. A realization may be optimized only as an immutable candidate generation under normal SSSF evaluation and promotion rules.

> **Stable semantic intent belongs in the contract; model-specific elicitation belongs in a replaceable qualified realization.**

## EXPLORE-1 — Instruction contract vs compiled realization

A durable semantic instruction contract should bind the enduring behavior expected of a worker/node, including as applicable:

- semantic purpose;
- typed inputs/outputs;
- authority and capability constraints;
- applicability;
- evidence expectations;
- failure/CNO semantics.

Prompt text, demonstrations, formatting, model-specific hints, and context arrangement are compiled realizations of that contract rather than the specification itself.

Routing: `FUT-011`, DSH worker/reviewer profile design.

## EXPLORE-2 — Immutable compiled instruction generations

An optimized prompt/demo realization is a new immutable candidate generation, not an in-place mutation of the active production instruction.

Preferred lifecycle:

```text
qualified realization I7
        ↓
optimizer proposes I8
        ↓
replay / held-out / fresh-frontier evaluation
        ↓
independent qualification where required
        ↓
SSSF promotion or rejection
```

The running generation may propose a successor but cannot install it.

## EXPLORE-3 — Optimization metric is governed evidence, not acceptance authority

Any optimizer metric defines what the search rewards and therefore requires identity, ownership, proof scope, cohort provenance, and limitations.

An optimization metric may rank/select candidate realizations but does not become an SSSF acceptance contract by itself.

## EXPLORE-4 — Mechanize before prompt optimization

Do not use semantic prompt optimization to improve compliance with stable/checkable rules that CODE can enforce directly.

Examples that should move CODEward where possible:

- expected-write boundaries;
- schema constraints;
- source/head identity;
- deterministic tool/effect policy;
- required verifier applicability.

Prompt compilation is for residual semantic uncertainty.

## EXPLORE-5 — Demonstration provenance and leakage control

Demonstration/few-shot sets materially affect behavior and are part of the effective runtime identity.

Bind, where applicable:

- demonstration-set digest;
- source episode/cohort identities;
- optimization/validation split;
- forbidden-for-current-evaluation episodes.

Historical reference answers or hidden evaluation artifacts must not leak into the solver-visible realization for the same evaluation episode.

## EXPLORE-6 — Model/profile-specific qualification

The semantic contract may be reusable across models, but compiled prompt/demo realizations may be model/profile/ACI-specific.

A realization qualified for one materially different AgentBackend/ACI/context generation does not transfer by assertion to another.

## EXPLORE-7 — CODE-budgeted optimization search

Instruction optimization is a search problem. CODE owns:

- candidate bookkeeping;
- optimization budget;
- model/verifier call ceilings;
- cost/time ceilings;
- candidate selection for qualification;
- terminal/promotion state.

AGENT/LM mechanisms may propose candidate instructions/demonstrations but do not own promotion.

## EXPLORE-8 — Replay for development, fresh frontier for promotion

Historical replay episodes may be used for optimization/development and regression checking.

Promotion of a compiled realization requires held-out/fresh-frontier evidence so repeated optimization against replay cannot masquerade as generalization.

Routing: SWE-Gym/SWE-bench-Live evaluation research and DSH-8.

## EXPLORE-9 — Compiled candidate provenance bundle

A candidate realization should carry enough provenance to reproduce and evaluate it, including as applicable:

- instruction-contract identity;
- base/candidate generation;
- optimizer implementation/model/policy identity;
- optimization cohort;
- metric generation;
- prompt digest;
- demonstration-set digest;
- optimization/replay/frontier scores;
- token/cost/latency evidence.

Do not preserve only the final prompt text.

## EXPLORE-10 — FUT-011 lifecycle extension

Instruction-artifact governance should support:

```text
semantic contract
    ↓
realization
    ↓
behavioral qualification
    ↓
compiled candidate optimization
    ↓
held-out qualification / promotion
    ↓
periodic CODEward extraction
    ↓
simplification / retirement / recompilation
```

The instruction surface should shrink as stable behavior becomes deterministic.

## Additional supporting observations

- DSPy-like semantic programs, if ever useful, belong inside a bounded DSH execution cell and cannot own SSSF outer sequencing, acceptance, source custody, budget enlargement, or promotion.
- Optimizer algorithms should remain replaceable; do not build a generalized optimizer abstraction before a real second implementation seam exists.
- Automatic model fine-tuning is a separate security/cost/provenance capability and remains unauthorized by this research.

## Non-decisions

This research does **not** authorize:

- DSPy adoption;
- automatic prompt self-modification in production;
- automatic fine-tuning or training expenditure;
- optimizer metrics as acceptance authority;
- state promotion or roadmap changes.
