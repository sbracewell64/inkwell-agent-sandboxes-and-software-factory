# AgentScope Research

## Status

`EXPLORE` / supporting agent-runtime research only.

This document preserves SSSF-relevant findings from:

- **AgentScope: A Flexible yet Robust Multi-Agent Platform** — arXiv `2402.14034`
- **AgentScope 1.0: A Developer-Centric Framework for Building Agentic Applications** — arXiv `2508.16279`

The project/framework is a runtime/platform research source, not an authorization to adopt AgentScope, its ReAct workflow, message hub, sandbox, or current ecosystem as SSSF architecture.

## Governing interpretation

AgentScope provides useful evidence for typed provider-neutral runtime interfaces, narrow tool surfaces, asynchronous execution, and traceable messages. These mechanisms belong underneath bounded DSH cells; SSSF remains owner of source, authority, workflow, acceptance, and Docker custody.

> **Normalize runtime interfaces for the agent, but preserve the distinctions CODE needs for trust, authority, effects, provenance, lifecycle, and qualification.**

## EXPLORE-1 — Typed runtime messages with trace identity

Runtime messages/results should carry unique identity, producer/sender identity, timestamps, structured content type, and metadata/provenance rather than existing only as free-form conversation.

SSSF should add stronger evidence/trust/authority classification where material and should not require durable private chain-of-thought storage.

## EXPLORE-2 — Provider-neutral model interface; provider-specific formatting remains qualification-relevant

A unified AgentBackend/model response contract is useful across heterogeneous providers. Provider-specific formatters/adapters should remain explicit implementation generations because message formatting, tool schemas, reasoning configuration, and response conversion can materially alter behavior.

The stable semantic contract may be provider-neutral; the effective runtime generation is not.

## EXPLORE-3 — Unified usage/resource accounting

Per-call token, latency, error, and related usage data should be emitted in a provider-neutral typed form to support CODE-owned budgets, scorecards, rate limits, and cost analysis.

Observability is evidence/projection, not workflow authority.

## EXPLORE-4 — Developer/CODE-owned memory and AGENT-curated memory are different authorities

AgentScope's developer-controlled vs agent-controlled long-term-memory modes reinforce the need to separate systematic retention from opportunistic semantic memory.

SSSF CODE owns authoritative/durable retention and projection rules. AGENT may request retrieval or propose derived memory within bounded scopes but may not rewrite authoritative history/evidence.

## EXPLORE-5 — Tool surface narrowing reduces cognition and risk

Large undifferentiated tool catalogs increase context cost and selection complexity. Prefer task/cell-specific capability groups and expose the minimum sufficient tool surface.

For SSSF, activation/admission is CODE-owned from the ExecutionCell capability/effect contract; an agent may request an additional admitted group but cannot grant itself capabilities.

## EXPLORE-6 — Local and remote tools may share a semantic interface but not security identity

Wrapping MCP/remote endpoints as local-looking callable tools is ergonomically useful. CODE must still retain and enforce remote/local provenance, provider/server identity, trust class, credential boundary, network/effect policy, session lifecycle, and exact tool generation.

Uniform model presentation must not erase security distinctions.

## EXPLORE-7 — Stateful vs stateless external-tool sessions are explicit lifecycle semantics

Persistent remote/browser/MCP sessions and one-call ephemeral sessions have different state, cleanup, replay, privacy, and security behavior. Session mode/identity belongs in the effective execution binding when material.

CODE owns connect/close/reconcile/cleanup semantics rather than leaving session lifecycle to conversational agent behavior.

## EXPLORE-8 — Interrupted/streaming tools emit explicit partial results

Long-running or streaming tool execution may be interrupted while having produced useful partial observations. Runtime results should distinguish partial/interrupted/complete terminality and preserve yielded evidence where safe.

Partial observation does not imply the effect completed, and resumption/retry policy remains CODE-owned.

## EXPLORE-9 — Async and parallel runtime execution is subordinate to CODE scheduling

Asynchronous model/tool calls and parallel tool invocation can improve runtime efficiency. They remain resource/execution mechanics underneath the WorkNode/ExecutionCell graph and must respect dependency, effect conflict, capability, budget, and cancellation policy.

## EXPLORE-10 — Runtime hooks/tracing are projections over owner-emitted facts

OpenTelemetry-style tracing, hooks, Studio/visual inspection, and evaluation UIs are useful for diagnosis and development but should consume typed runtime facts rather than becoming a second source of truth or reconstructing hidden workflow authority.

## EXPLORE-11 — Runtime sandbox is not SSSF sandbox authority

A general framework may bundle its own sandbox for safe agent execution. SSSF already has a stronger Docker-first SandboxProvider/source-custody/cleanup design; an AgentScope-style sandbox should not become a competing owner.

## EXPLORE-12 — ReAct remains bounded inner behavior only

AgentScope 1.0 recommends ReAct as its primary agent architecture. For SSSF, ReAct-like reasoning/action loops may occur inside a bounded ExecutionCell/inner unit but cannot own outer sequencing, retries, acceptance, promotion, authority, or source custody.

## Routing

- `FUT-001` / DSH runtime contracts, AgentBackend, tools, memory, async resource execution.
- DSH-5 richer capabilities/MCP or remote-tool integration.
- SBX/DSH cleanup/session lifecycle and observability evidence.
- Existing effective-runtime identity and tool-capability research.

## Non-decisions

This research does **not** authorize:

- AgentScope adoption;
- AgentScope ReAct/message-hub orchestration as SSSF workflow;
- AgentScope sandbox replacing Docker/SandboxProvider;
- remote MCP tools losing trust/effect provenance;
- agent-controlled capability activation or durable evidence deletion;
- a new tracing/observability source of truth;
- roadmap or FUT state promotion.
