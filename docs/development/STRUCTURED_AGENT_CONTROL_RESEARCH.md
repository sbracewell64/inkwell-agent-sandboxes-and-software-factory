# Structured Agent Control Research

## Status

`EXPLORE` / supporting research only.

This document preserves research observations from:

- **Behavior Trees Enable Structured Programming of Language Model Agents**
- arXiv: `2404.07439v1`
- submitted: 2024-04-11

The paper is supporting evidence, not an SSSF dependency, runtime choice, or behavior-tree adoption decision.

## Governing interpretation

The useful architectural lesson is not "SSSF should use behavior trees." It is:

> **Keep control flow explicit, keep child interfaces small, express preconditions/postconditions mechanically where possible, and confine model judgment to bounded semantic roles.**

This reinforces the existing SSSF value-creator law:

- ENGINEER owns VALUE and reserved AUTHORITY.
- AGENT owns UNCERTAINTY REDUCTION.
- CODE owns STATE TRANSITION wherever stable/checkable rules can honestly own it.

## EXPLORE-1 — Predicate-driven reconciliation

Strongest near-term idea.

Before executing an expensive/reversible transition, deterministic code should establish whether the action's postcondition already holds and whether its current preconditions still hold.

Preferred direction:

```text
canonical state/evidence
        ↓
mechanical predicates
        ↓
next eligible transition
```

rather than remembered workflow position or agent inference over prose.

Potential benefits:

- restartability;
- idempotence;
- stale-state resistance;
- unnecessary-work avoidance;
- lower agent/Captain involvement;
- clearer formal/mechanical verification of transition legality.

Routing: supporting evidence for `FUT-010` and future deterministic SSSF state-transition work.

## EXPLORE-2 — Small inner workflow algebra

The paper's action/condition/sequence/fallback structure is useful as evidence that DSH inner workflows should begin from a constrained control vocabulary rather than arbitrary recursive graphs.

Possible early DSH-4 primitives:

- action;
- condition;
- sequence;
- fallback;
- later, only if proven useful: bounded repeat/retry and parallel.

This does **not** select a behavior-tree library or expose behavior-tree terminology as SSSF architecture.

Routing: `FUT-001`, especially DSH-4.

## EXPLORE-3 — Finite semantic predicates

Where deterministic observation cannot settle a semantic question, prefer a typed finite classification surface over an open-ended model decision.

Example:

```yaml
question: root_cause_status
choices:
  - understood
  - partially_understood
  - contradicted
  - insufficient_evidence
```

The agent performs semantic classification; deterministic code owns what each class permits.

Probabilities/repeated classifications may be retained as advisory evidence but do not become acceptance authority.

Routing: supporting evidence for `FUT-007` and later DSH routing/semantic-evaluation work.

## EXPLORE-4 — Classification before risky effects

Useful pattern:

```text
requested action
      ↓
bounded semantic risk characterization
      ↓
deterministic authority/policy gate
      ↓
effect executor
```

The semantic classifier is not itself the security boundary. Separation or model diversity is not proof of correctness; exact qualification and deterministic authority remain required.

Routing: later DSH capability/effect-policy research.

## EXPLORE-5 — Formal/mechanical control-graph verification

Potential future use: verify deterministic control properties surrounding agents rather than attempting to formally verify arbitrary model reasoning.

Candidate properties include:

- every admitted work state can reach a terminal disposition;
- no DSH child can reach SSSF landing/promotion authority;
- every irreversible transition has an authorization predecessor;
- FAIL cannot reach ACCEPTED;
- required CNO cannot become PASS;
- exact candidate identity precedes review/landing authorization;
- head movement invalidates landing authorization;
- cleanup/reconciliation is reachable from every execution state.

Routing: `FUT-009` / `FUT-010` EXPLORE evidence only.

## Explicit non-adoptions

### No global blackboard

A generic shared blackboard would risk becoming an undocumented parallel state authority. Cross-cell/outer-boundary state should remain typed, attributed, and owned through existing SSSF contracts/evidence/Git identities.

Temporary DSH-internal shared state may exist as an implementation detail if it cannot acquire outer authority.

### Control status is not evidence

A small child control result such as SUCCESS/FAILURE/RUNNING may be useful for inner control, but it is insufficient as SSSF evidence.

Preferred separation:

```yaml
control:
  status: FAILURE
evidence:
  failure_class: tests_failed
  source_sha: ...
  inner_attempt: ...
  usage: ...
  cleanup: ...
```

### No behavior-tree runtime decision

Do not add a behavior-tree subsystem, dependency, blackboard, or new SSSF-visible control vocabulary from this paper without a later explicit candidate evaluation showing net simplification and a real ownership gap.

## Promotion posture

All mechanisms remain `EXPLORE`.

Strongest promotion opportunity: **predicate-driven reconciliation / explicit precondition-postcondition law**, when future SSSF work next changes deterministic state-transition machinery.

Do not create a separate behavior-tree candidate unless future evidence reveals a real primitive not already owned by `FUT-001`, `FUT-007`, `FUT-009`, or `FUT-010`.
