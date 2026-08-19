# SWE-Search Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **SWE-Search: Enhancing Software Agents with Monte Carlo Tree Search and Iterative Refinement**
- arXiv: `2410.20285`

The paper is a search/refinement research source, not an authorization to adopt MCTS or Moatless Tree Search.

## Governing interpretation

When serial bounded reasoning no longer suffices, CODE may search over AGENT-generated semantic possibilities. Search itself must prove value relative to simpler alternatives.

> **Search strategy is CODE; semantic branch generation/evaluation may be AGENT work.**

## EXPLORE-1 — CODE-owned inner search policy

Agents may propose candidate semantic actions/branches and probabilistic evaluators may score them, but CODE owns branch selection, retry/backtrack semantics, pruning, continuation, and termination according to a qualified search policy.

Search remains inside one bounded DSH execution cell and never becomes SSSF outer workflow authority.

Routing: `FUT-005`, `FUT-006`, DSH-2/DSH-7.

## EXPLORE-2 — Search is applicability-driven

Do not instantiate tree/branch search merely because the capability exists.

CODE should admit search only when evidence supports meaningful branching headroom, for example:

- multi-hypothesis uncertainty remains;
- ordinary bounded refinement has stalled;
- alternative strategies are materially distinct;
- task class historically benefits from search;
- remaining cell budget can support it.

Otherwise use the lowest sufficient execution class.

## EXPLORE-3 — Search branches retain exact lineage

Each branch/node is a typed descendant of one `execution_cell_id` and one SSSF `outer_attempt_id`, with explicit parent identity and working-state lineage.

Potential bindings include:

- `inner_unit_id` / parent node;
- exact source/working generation;
- candidate mutation/workspace identity;
- action identity;
- observations/evidence refs;
- evaluator observations;
- branch terminal reason.

Multiple branches are not multiple SSSF outer attempts.

## EXPLORE-4 — Compute-matched baseline requirement

Any search mechanism must be compared against simpler alternatives under matched or explicitly accounted compute, including at least:

- one trajectory;
- ordinary bounded serial refinement;
- independent-N candidate generation;
- search-guided N.

Measure whether search adds value beyond merely spending more inference.

Required metrics should include `search_gain_over_independent_N`, selection regret, oracle headroom, total compute/cost/latency, reviewer burden, and accepted-value-per-compute.

## EXPLORE-5 — Phase-aware semantic evaluation

Probabilistic evaluators should receive the typed semantic phase/goal of the branch rather than applying one generic quality question to all states.

Illustrative phase criteria:

- localization: did this reduce uncertainty over relevant source scope?
- reproduction: did this establish/narrow the target failure?
- implementation: does the mutation address the supported hypothesis?

The semantic phase is supplied from typed runtime/work state; the evaluator does not own phase identity.

Routing: `FUT-007`, phase taxonomy research.

## EXPLORE-6 — Search policy is part of exact execution identity

Material search behavior depends on algorithm/policy parameters such as selection/pruning strategy, depth/branch limits, exploration coefficients, candidate terminal policy, evaluator feedback policy, and selection/discriminator budget.

Bind a qualified search-policy generation/digest to any search-enabled DSH execution. The same model under materially different search policy is not automatically the same qualified execution generation.

## EXPLORE-7 — Search/evaluator telemetry

Future search-enabled evidence should allow analysis of:

- candidate/branch diversity;
- stochastic vs strategy vs model/profile diversity;
- evaluator score and qualitative-feedback provenance;
- pruned/dead branches;
- search depth/width;
- model/verifier calls and cost;
- search gain relative to independent-N;
- selection regret/oracle headroom;
- deterministic final acceptance.

Routing: `FUT-008` and harness scorecard.

## Supporting findings

- Qualitative evaluator feedback can be useful branch-diversification evidence, but remains advisory data rather than instruction authority.
- Combine cheap CODE-observed loop/repetition controls with semantic dead-end evaluation where deterministic evidence is insufficient.
- Search budgets should be multidimensional (`max_nodes`, `max_depth`, `max_children`, model/verifier calls, tokens, cost, wall time, live candidates).
- Candidate-selection methods such as debate/tournaments/value agents remain replaceable implementation options and must earn complexity.
- Agent-selected tests during search are diagnostic evidence; acceptance tests remain determined by VerificationContract applicability.
- Search-tree visualizations may be derived from typed inner-unit evidence but do not become trace/state authority.

## Non-decisions

This research does **not** authorize:

- MCTS adoption;
- Moatless Tree Search installation;
- state promotion of FUT-005/FUT-006/FUT-008;
- unconditional search in DSH;
- evaluator authority over acceptance or budgets;
- a new search-state database outside the existing trace/evidence owners.
