# AutoGen Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation**
- arXiv: `2308.08155`

The paper is a multi-agent conversation/programming research source, not an authorization to adopt AutoGen or conversation-driven workflow control.

## Governing interpretation

AutoGen's useful contribution is composable, capability-differentiated agents. Its conversation-as-workflow model should not become SSSF outer control.

> **Semantic computation and workflow control are separate concerns; move stable control into CODE.**

## EXPLORE-1 — Separate semantic computation from control flow

Agent reasoning/tool use may implement bounded semantic computation, while stable sequencing, retry, readiness, termination, and acceptance remain CODE-owned.

Conversation may be an inner semantic protocol but not durable outer workflow state.

## EXPLORE-2 — Roles resolve to capability/authority envelopes

Role identity should correspond to explicit capabilities, information, authority, independence, and resource bounds rather than role-play labels alone.

## EXPLORE-3 — Agent termination is advisory

Model-generated completion/termination signals are candidate terminal recommendations only. CODE owns requirement coverage, verification, review, authority, exact-state, evidence, and cleanup folding.

## EXPLORE-4 — Deterministic vs semantic grounding

Mechanically checkable legality/grounding belongs in CODE. Irreducible commonsense or semantic grounding may remain bounded AGENT work.

Examples of CODE-owned grounding include expected-head checks, path authorization, schema validity, dependency readiness, capability permission, and budget state.

## EXPLORE-5 — Independent semantic safeguards are residual

Independent semantic checker/safeguard roles may add value where judgment remains, but deterministic safeguards should be applied first and never replaced by a safeguard agent.

## EXPLORE-6 — Bounded agent-requested context expansion

Agents may identify unresolved semantic uncertainty and request additional context. CODE owns retrieval execution, scope, paging/backpressure, provenance, and budgets.

## EXPLORE-7 — Dependency-directed communication

Prefer typed producer-to-explicit-consumer transport over ambient group-chat broadcast/shared cognition. Cross-unit information should be attributable and bounded.

## EXPLORE-8 — Transport and semantic handling remain separable

If DSH later needs an internal event/message runtime, delivery/routing mechanics should remain distinct from semantic handlers and subordinate to the ExecutionCell/outer SSSF authority.

## EXPLORE-9 — Explicit authority routing instead of generic human-in-loop

Do not use a generic user-proxy escalation model. SSSF routes deterministic facts to CODE, ordinary semantic engineering judgment to delegated agents/Browser Sol, external outages to `EXTERNAL_DEPENDENCY`, and reserved money/security/personal/irreversible decisions to the Captain.

## Non-decisions

This research does **not** authorize:

- AutoGen adoption;
- GroupChat/broadcast memory as DSH architecture;
- ConversableAgent/user-proxy control of outer workflow;
- actor/event runtime as SSSF authority;
- state promotion or roadmap changes.
