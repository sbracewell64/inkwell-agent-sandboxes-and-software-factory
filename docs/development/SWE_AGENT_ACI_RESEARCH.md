# SWE-agent Agent-Computer Interface Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering**
- arXiv: `2405.15793`

The paper is an agent-interface research source, not an adoption decision for SWE-agent itself.

## Governing interpretation

The interface between a model and its execution environment is part of the behaviorally relevant execution binding. SSSF should qualify agent-facing tool, observation, context, and guardrail generations rather than treating the model alone as the agent identity.

## EXPLORE-1 — Agent-interface generation is part of exact execution identity

Bind the effective agent-facing interface used by an execution cell, including as applicable:

- tool-contract generation/digest;
- observation-contract generation/digest;
- context/projection policy identity;
- guardrail policy identity;
- model/profile-specific presentation identity.

A model qualified under one materially different agent-interface generation does not transfer qualification by assertion to another.

Routing: `FUT-001`, DSH-1/DSH-5, AgentBackend/ExecutionCell evidence.

## EXPLORE-2 — Observation backpressure

Observations consume cognition and budget and therefore require CODE-owned bounds.

Broad searches or oversized observations should return typed refinement results such as `TOO_BROAD`, counts, truncation/projection facts, and narrowing suggestions rather than flooding model context.

Source/file views should be bounded projections chosen by deterministic policy and relevance rather than whole-file/repository dumps by default.

Routing: DSH-5 and context policy.

## EXPLORE-3 — Transactional stale-safe mutation

The agent proposes a semantic mutation; CODE owns application mechanics.

Preferred direction:

```text
observed working generation G
        ↓
agent proposes mutation bound to G
        ↓
CODE validates expected source/state
        ↓
atomic tentative apply
        ↓
cheap deterministic guardrails
        ↓
reject/rollback OR publish new working generation G+1
```

Use exact-match/structural identity and expected-state protection rather than relying on fragile line numbers as long-term mutation authority.

Routing: DSH-5 and stale-safe editing research.

## EXPLORE-4 — Effectful tools return resulting-state evidence

A successful effectful call should report what state transition actually occurred, not merely `ok`.

Potential fields include:

- old/new working generation;
- changed paths/ranges;
- mutation digest;
- guardrail outcomes;
- bounded diagnostics;
- stale/ambiguous/no-op status.

This reduces follow-up tool calls needed merely to discover whether an action happened.

Routing: general DSH tool/result contract.

## EXPLORE-5 — Agent-interface changes require measured qualification

Tool/interface additions are hypotheses, not automatically beneficial capabilities.

Qualify material ACI changes against the SSSF replay corpus/harness scorecard while holding model/task conditions stable where possible. Measure accepted outcome, cost, latency, tool-call count, loop/recovery behavior, evidence quality, and failure-class movement.

This applies to future LSP, MCP, semantic search, debugger/static-analysis, browser, and plugin capabilities.

Routing: DSH-5, FUT-002, harness scorecard.

## Supporting observations retained for later implementation

- Prefer compact semantic operations over raw mechanical sequences, but do not make tools so high-level that they become hidden workflow authorities.
- Specialized/private tool registries remain preferred to broad general shell exposure for routine work.
- Deterministic context projection should preserve full durable evidence elsewhere.
- Repeated edit/search failures and no-progress mutation patterns are candidates for CODE-owned loop/recovery guards at DSH-2.
- Budget exhaustion yields a typed terminal result and possible candidate evidence; it never implies acceptance or promotion.
- Test passing is narrower than engineering acceptance and must retain explicit verifier scope.

## Non-decisions

This research does **not** authorize:

- adopting SWE-agent as the DSH runtime;
- a universal fixed file-window size;
- line-number editing as authoritative mutation identity;
- unrestricted shell as the normal DSH interface;
- auto-submission/acceptance of partial work on budget exhaustion;
- state promotion of any existing FUT item;
- pre-Docker DSH activation.
