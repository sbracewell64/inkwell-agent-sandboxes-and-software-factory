# MultiAgentBench Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **MultiAgentBench: Evaluating the Collaboration and Competition of LLM Agents**
- arXiv: `2503.01935`

The paper is a multi-agent coordination research source, not an authorization to adopt MARBLE or any permanent DSH topology.

## Governing interpretation

Multi-agent topology is a qualified inner execution policy, not an SSSF architectural primitive.

> **Use the sparsest sufficient communication/delegation graph, and admit new edges only when they reduce uncertainty or advance admissible engineering state more effectively than the simpler topology.**

## EXPLORE-1 — Topology is a qualified DSH policy

Do not hard-code star, tree, chain, graph-mesh, or another collaboration topology as DSH architecture. Topology is workload- and role-dependent and must be qualified against real SSSF outcomes.

Routing: `FUT-001`, especially DSH-3/DSH-7.

## EXPLORE-2 — Sparse communication by construction

Communication/delegation edges should exist because a typed information, capability, authority, or independence dependency requires them.

Prefer explicit asymmetric edges such as builder -> research / critic before peer-to-peer or generic recursive collaboration.

## EXPLORE-3 — Agent count and communication rounds are CODE-owned budgets

More agents and more coordination rounds are not monotonically better.

Future cells should bind limits such as:

- max children;
- max depth;
- max parallel children;
- max messages/rounds;
- max peer exchanges;
- tokens/cost/wall time.

Agents may communicate inside those bounds but may not enlarge them.

## EXPLORE-4 — Coordination quality is diagnostic, not acceptance authority

Coordination quality and task success are separate dimensions. Useful communication metrics may help explain performance but cannot substitute for deterministic verification, semantic review, or accepted engineering outcomes.

Any LLM-derived coordination analysis is `INFERRED` evidence with evaluator provenance.

## EXPLORE-5 — Typed peer payloads; no generic shared cognition

If peer-to-peer exchange is ever admitted, messages should carry explicit sender/receiver/type/provenance/trust/authority identity rather than merging conversational memory.

Shared memory must not undermine maker/checker independence. Reviewers receive the candidate, authoritative requirements, and admissible evidence rather than inheriting the maker's complete cognition.

## EXPLORE-6 — CODE-owned redundant/no-progress communication controls

Mechanically detectable patterns such as near-identical repeated messages, same evidence refs without new state, or coordination rounds with no new evidence/task/candidate/decision should become typed loop/no-progress observations before spending semantic-agent effort detecting them.

## EXPLORE-7 — Topology is part of effective runtime identity

Qualification evidence should bind materially relevant coordination configuration, including:

- topology/edge-policy generation;
- relationship contracts;
- child count/depth/parallelism;
- communication budget;
- routing/aggregation policy.

A materially different communication graph is a different effective DSH generation for qualification purposes.

## EXPLORE-8 — Controlled topology experiments

When comparing coordination topologies, hold model/profile, ACI, tools, WorkPackage, environment, budget, verification, and other execution identity constant where possible.

Measure accepted engineering value, cost/latency, coordination overhead, child contribution, duplicate work, and failure/cleanup effects rather than message volume.

## EXPLORE-9 — Roles require a real boundary

A durable child role should correspond to a genuine distinction in capability, information, authority, independence, objective, or model/profile. Do not add roles merely to simulate a human team structure.

## Additional supporting observations

- Underlying task/model capability can dominate coordination quality; good collaboration cannot rescue an incapable solver.
- Large group discussion can underperform simpler planning; unrestricted peer chatter is not assumed useful.
- Expected-vs-observed discrepancy may support bounded replanning, but persistent self-evolving planning memory is not authorized by this research.
- Multi-agent coordination is valuable only when it outperforms the simpler topology on accepted-value-per-coordination-cost.

## Non-decisions

This research does **not** authorize:

- MARBLE adoption;
- a graph-mesh DSH topology;
- global shared agent memory;
- unlimited child spawning or communication;
- LLM coordination scores as acceptance evidence;
- state promotion or roadmap changes.
