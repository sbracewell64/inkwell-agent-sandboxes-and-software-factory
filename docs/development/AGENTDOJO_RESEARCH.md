# AgentDojo Research

## Status

`EXPLORE` / supporting security research only.

This document preserves SSSF-relevant findings from:

- **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents**
- arXiv: `2406.13352`
- NeurIPS 2024 Datasets and Benchmarks Track

The benchmark is a security-evaluation research source, not an authorization to adopt AgentDojo or treat static benchmark success as a production security guarantee.

## Governing interpretation

Tool-returned/external content is data with explicit provenance, not authority. Security-critical effects require CODE-owned mediation independent of whether the model correctly distinguishes instructions from data.

> **Untrusted content may influence semantic judgment; it cannot grant itself effect authority.**

## EXPLORE-1 — Separate utility and security qualification

A capable agent and a secure agent are different properties. Qualification should track at least benign task utility, utility under adversarial/untrusted input, and prohibited-effect/security outcomes separately.

Do not collapse security into one aggregate task-success score.

## EXPLORE-2 — External/tool-returned content has explicit trust provenance

Every model-facing observation derived from external tools, web pages, messages, retrieved documents, or other attacker-influenceable state should retain provenance/trust classification.

Content itself cannot redefine the authoritative WorkPackage, capability envelope, effect policy, or user/Captain authority.

## EXPLORE-3 — Pre-effect mediation is CODE-owned

Before an effectful tool call executes, CODE should validate capability admission, authority, effect class, target/resource scope, relevant source/current-state identity, and budget.

Prompt instructions or model intent are not sufficient authorization.

## EXPLORE-4 — Least privilege/tool narrowing is useful but must not rely on the model as the security boundary

Restrict available tools/effects to the smallest set required by the admitted task where this can be established safely. Prefer deterministic derivation from typed task/cell contracts.

Model-proposed tool narrowing may be advisory evidence but is not a security guarantee, especially when required later actions depend on untrusted observations.

## EXPLORE-5 — Data dependency matters for security policy

Distinguish tasks whose permitted action/effect set can be determined before reading untrusted data from tasks where later legitimate actions depend on tool-returned content.

The latter require stronger information/effect-flow controls than one-time preselection of tools.

## EXPLORE-6 — Security effects and semantic output need separate controls

Isolation that prevents unauthorized tool calls may still fail when malicious data biases a purely semantic output (for example, choosing an attacker-preferred recommendation). Security review therefore includes both effect authorization and integrity of semantic decision inputs where material.

## EXPLORE-7 — Adversarial evaluation is a living frontier

Security qualification should include explicit attack/negative-control episodes and should not treat a fixed static attack set as proof of robustness. Defense changes require refreshed adversarial evaluation, including adaptive/defense-aware attacks when practical.

## EXPLORE-8 — Underspecified/action-open authority is a first-class risk

Tasks that delegate consequential action selection to attacker-controlled or untrusted content are structurally higher risk than precisely bounded tasks. FirstMate/WorkPackage compilation should narrow consequential objectives and allowed effects before DSH consumes untrusted data wherever possible.

## EXPLORE-9 — Security benchmark state is observed, not LLM-judged where deterministic checks exist

Prefer programmatic resulting-state checks for prohibited effects and task utility. LLM semantic judges remain residual diagnostic/review mechanisms rather than primary security enforcement.

## EXPLORE-10 — Prompt defenses remain defense-in-depth only

Delimiting, prompt repetition, detector models, and similar in-context defenses may improve robustness but cannot replace least privilege, reference-monitor-style mediation, source/effect isolation, or explicit authority checks.

## Routing

- `FUT-001`, especially DSH external-tool capability/effect policy and DSH-5 richer capabilities.
- Security/negative-control qualification for external web/tool integration.
- WorkPackage/FirstMate requirement and effect narrowing.
- Future AgentDojo/AutoDojo-style security frontier when real external-tool/browser capabilities near implementation.

## Non-decisions

This research does **not** authorize:

- AgentDojo as a production dependency;
- model-selected tools as the security boundary;
- prompt-injection detectors as acceptance/security authority;
- unrestricted browser/web/tool access;
- a new security daemon/layer;
- roadmap or FUT state promotion.
