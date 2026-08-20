# Context Mode Research

## Status

`EXPLORE` / supporting context-projection research only.

This document preserves SSSF-relevant findings from:

- **Context Mode** — `mksglu/context-mode`

The project is a context-window optimization/runtime research source, not an authorization to install Context Mode into FirstMate or SSSF.

## Governing interpretation

Context Mode's strongest contribution is observation virtualization rather than generic lossy compression: keep bulky observations outside the model context, compute over them deterministically or retrieve exact indexed chunks on demand, and expose only the minimum sufficient projection to the agent.

> **Large observation does not imply large prompt. Prefer deterministic reduction for computable data, exact indexed retrieval where detail matters, and semantic compression only where needed.**

## EXPLORE-1 — Externalize oversized observations

Large tool outputs should remain outside active model context and be referenced through durable observation identity/pointers when possible.

The canonical raw observation remains SSSF/FirstMate-owned, provenance-bound state. Any Context-Mode-style index or summary is a derived projection rather than the source of truth.

## EXPLORE-2 — Deterministic computation before semantic consumption

For structured/computable observations such as CI logs, GitHub run lists, build output, analytics, or large JSON collections, prefer deterministic reducer/query code over spending model context on the raw dataset.

Preferred pattern:

```text
raw observation
      ↓
AGENT formulates bounded query/reducer when semantics are needed
      ↓
CODE executes inside an admitted sandbox/runtime
      ↓
small exact result
      ↓
AGENT interprets
```

Where the required computation is already known mechanically, CODE should formulate and execute it directly without another agent turn.

## EXPLORE-3 — Exact indexed retrieval for precision-sensitive material

For documentation, APIs, tool signatures, source excerpts, code examples, and other material where summarization could destroy required detail, prefer exact chunk indexing + bounded retrieval rather than lossy compression.

FTS5/BM25 is a plausible simple implementation reference for future observation/history indexing, but no dependency decision is made here.

## EXPLORE-4 — Projection policy depends on observation class

A future DSH/FirstMate observation projection policy should choose mechanisms according to the material being projected, for example:

- structured computable data → deterministic reducer/query;
- exact retrievable knowledge → bounded indexed retrieval;
- semantic prose → qualified compression when needed;
- authoritative requirements/source/evidence → exact retention with scope/reference narrowing rather than destructive summarization.

One generic compressor is not assumed optimal for every observation type.

## EXPLORE-5 — Oversized output becomes a query surface, not truncation

When a raw observation exceeds the current active-context budget, preserve the full content durably and expose an exact query/retrieval interface rather than silently truncating the observation.

The pointer/index generation should bind the raw observation digest/source generation so stale or mismatched retrieval can be detected.

## EXPLORE-6 — Session continuity is only a projection over canonical state

Context Mode's SQLite/session reconstruction addresses a real agent-compaction problem, but SSSF already has stronger owners for requirements, work state, source identity, evidence, reviews, and rulings.

Any future session-resume summary must therefore be a derived convenience projection over canonical Git/GitHub/SSSF/control-plane state. It must never become workflow truth or a competing decision/state database.

## EXPLORE-7 — Agent-generated reducer code executes inside the real SSSF sandbox

Context Mode's `ctx_execute*` implementation executes generated programs using host runtimes and can run with the project root as working directory. This is not an SSSF-grade isolation boundary.

If SSSF adopts the "think in code" pattern, generated reducer/query code must execute inside the Docker/SandboxProvider boundary with normal capability, effect, network, budget, process-custody, and cleanup rules.

Do not add a host-level polyglot executor as a competing sandbox.

## EXPLORE-8 — Reject automatic hook/routing ownership

Context Mode's full plugin relies on SessionStart/PreToolUse/PostToolUse/PreCompact-style hooks and injected routing instructions to steer agents toward its tools.

SSSF/FirstMate should not make hidden hooks another workflow or routing authority. Capability admission and projection policy remain explicit CODE-owned state.

## EXPLORE-9 — Dependency value is lower than design value

The Context Mode package includes MCP tooling, polyglot execution, routing hooks, persistent session state, many platform adapters, plugin installation, and an Elastic License 2.0 dependency surface.

The architectural patterns are currently more valuable to SSSF than the full dependency. Prefer a small SSSF-owned observation projection/index implementation when the real seam is built unless controlled qualification later establishes material value from the package itself.

## EXPLORE-10 — Compare projection strategies empirically

When the DSH observation/context-projection seam is implemented, compare at least:

- raw baseline;
- Headroom-style compression;
- deterministic reduction/query;
- exact indexed retrieval.

Hold model/profile, source, WorkPackage, tool/ACI generation, and budget constant where possible.

Measure input tokens, latency, cost, retrieval rate, missed-fact/compression-regret rate, engineering acceptance, and Captain-intervention effects rather than token savings alone.

## Headroom relationship

The already-preserved Headroom research and this research are complementary rather than mutually exclusive:

```text
Headroom
→ strong content-aware compression implementation

Context Mode
→ strong observation virtualization / compute-and-retrieve model
```

A future SSSF observation projection boundary may select different strategies by observation class while retaining the same canonical raw evidence underneath.

## Licensing observation

Context Mode uses Elastic License 2.0 rather than a permissive Apache/MIT license. This is not a legal ruling, but it makes the package a less attractive long-term architectural dependency than an equivalent permissively licensed implementation, especially if SSSF/FirstMate distribution or hosted use changes later.

## Routing

- `FUT-001` / DSH observation-context projection design.
- DSH-5 bounded retrieval and richer tool capabilities.
- FirstMate future large-observation handling.
- Existing Headroom comparison/qualification work.
- Existing durable-history vs active-projection research.

## Non-decisions

This research does **not** authorize:

- installing Context Mode into FirstMate;
- installing Context Mode into SSSF;
- a Context Mode pilot before the already-authorized narrower Headroom pilot;
- host-level `ctx_execute*` as an SSSF execution boundary;
- Context Mode session SQLite as workflow truth;
- hook-based tool routing as FirstMate/SSSF authority;
- Context Mode's sandbox replacing Docker/SandboxProvider;
- roadmap or FUT state promotion.

The Docker-first → baseline → Wayfinder → DSH sequence remains unchanged.
