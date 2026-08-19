# Agentic Software Engineering Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **Agentic Software Engineering: Foundational Pillars and a Research Roadmap**
- arXiv: `2509.06216`
- reviewed as supporting architecture research, not as an SSSF runtime or artifact-taxonomy adoption decision.

## Governing interpretation

The paper's strongest contribution for SSSF is the separation between human-facing and agent-facing engineering environments. SSSF keeps that idea but strengthens it with the three-value-creator model:

- ENGINEER owns VALUE and reserved AUTHORITY;
- AGENT owns UNCERTAINTY REDUCTION;
- CODE owns STATE TRANSITION wherever stable/checkable rules can honestly own it.

Do not import the paper's artifact vocabulary wholesale. Concepts map into existing SSSF owners.

## EXPLORE-1 — Dual-surface value-creator interfaces

Human-facing surfaces should optimize for intent, trade-offs, decisions, completion evidence and progressive disclosure.

Agent-facing surfaces should optimize for exact state, structured machine-readable diagnostics, bounded capabilities, semantic/structural code access and efficient uncertainty reduction.

Code-facing contracts own deterministic transition legality, budgets, admission, verification, acceptance and promotion.

Likely mapping:

```text
Captain -> existing Wayfinder -> FirstMate
                     |
                     v
              typed SSSF work/evidence
                     |
                     v
              SSSF + Docker + DSH
```

Routing: supporting evidence for FUT-010 and future WAYFINDER-1 commissioning.

## EXPLORE-2 — FirstMate briefing compilation

The paper's structured briefing concept is useful, but the Engineer should not have to author a large detailed specification for routine work.

Preferred SSSF direction:

```text
Engineer intent/value
        -> FirstMate repository investigation + ambiguity reduction
        -> typed WorkPackage / transition contract
        -> SSSF admission
```

The compiled work contract may bind goal, value reference, success criteria, invariants, context/source refs, constraints, authority and verification obligations.

Routing: future FirstMate semantic-compiler work; no new BriefingScript artifact.

## EXPLORE-3 — Evidence-readiness projection with progressive disclosure

The paper's merge-readiness concept maps best to a generated human/reviewer projection over canonical SSSF evidence rather than a new acceptance authority.

Potential generated view:

- completion status;
- applicable verifier obligations;
- PASS / FAIL / CNO summary;
- independent review status;
- source/exact-head identity;
- unresolved risk;
- evidence links;
- landing authorization status where applicable.

The projection must remain derived/read-only. Canonical tests, validators, reviews, proof records, traces and Git identity remain authoritative.

Routing: FUT-009/FUT-012 and future Wayfinder UX.

## EXPLORE-4 — Feedback to candidate-instruction pipeline

Repeated human/reviewer corrections may be generalized into candidate operational guidance, but specific feedback never self-promotes into permanent instruction authority.

Preferred flow:

```text
recurring correction
    -> candidate generalized rule
    -> FUT-011 qualification
    -> trigger/routing/collision + behavioral watched-red tests
    -> promotion only if proven
```

If the rule can be enforced deterministically, CODE should own it instead of an instruction artifact.

Routing: supporting evidence for FUT-011.

## EXPLORE-5 — Risk/uncertainty-dependent autonomy profiles

One fixed ceremony is inefficient. SSSF should eventually select among qualified execution/autonomy profiles as a deterministic function of typed risk, uncertainty, reversibility, evidence requirements and authority class.

Agents may help classify genuinely semantic uncertainty, but cannot enlarge their own authority or select a more permissive profile by assertion.

Routing: future DSH-7 / CODE-owned policy evaluation.

## Existing SSSF mappings

Do not add paper-specific permanent nouns where existing owners suffice:

| Paper concept | SSSF owner |
|---|---|
| human command environment | existing Wayfinder + FirstMate |
| agent execution environment | SSSF + Docker + DSH |
| detailed briefing | FirstMate -> WorkPackage / typed transition contract |
| workflow script | CODE-owned workflow/policy |
| mentorship script | FUT-011 qualified instructions |
| consultation request | `fm-sol-control/v1` escalation/ruling |
| merge-readiness pack | generated evidence/readiness projection |
| verification/certification record | existing evidence/review/ruling/proof owners |
| N-version execution | FUT-006 research |
| agent-native tools | DSH-5 research |

## Rejected / constrained ideas

- Do not create parallel BriefingScript / LoopScript / MentorScript / CRP / MRP / VCR artifact hierarchies.
- Do not make an agent-interpreted workflow script the outer SSSF state machine.
- Do not let agent memory become project truth.
- Do not weaken duplication/complexity discipline based on speculative claims that agents make duplicated code cheap.
- Multiple candidate implementations are not automatically worth their cost; FUT-006 requires measured qualification against the harness scorecard.

## Promotion posture

No existing FUT item changes state from this research record alone. Revisit these findings when the corresponding existing owner reaches a real promotion/implementation checkpoint.