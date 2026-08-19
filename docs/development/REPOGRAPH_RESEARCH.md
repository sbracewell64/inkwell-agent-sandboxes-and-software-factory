# RepoGraph Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **RepoGraph: Enhancing AI Software Engineering with Repository-level Code Graph**
- arXiv: `2410.14684`

The paper is a repository-structure/code-intelligence research source, not an adoption decision for RepoGraph itself.

## Governing interpretation

Repository relationship intelligence is useful as deterministic narrowing, but the source remains authoritative.

> **The source owns truth; the graph only accelerates questions about it.**

Do not create a persistent graph/knowledge store that becomes a second source of project truth.

## EXPLORE-1 — Exact-source-bound derived projection

Any repository graph/index used by SSSF or DSH should be a read-only derived projection bound to exact source identity and its builder generation.

Potential identity includes:

- repository;
- exact source commit/tree or working-generation identity;
- builder/parser/index generation;
- projection digest;
- coverage manifest.

If the working source changes, a prior projection is stale unless a qualified incremental-update mechanism proves equivalence. Stale projections must be refreshed or refused rather than silently queried against new source.

Routing: `FUT-001`, especially DSH-5 code-intelligence capability design.

## EXPLORE-2 — Explicit coverage and CNO semantics

Graph/index coverage must declare what it can and cannot observe, including as applicable:

- languages/files included;
- relation types represented;
- excluded manifests/configuration/generated files;
- static-vs-dynamic limitations;
- unsupported language/runtime relationships.

An absent edge is not automatically proof of no relation. Query results should support `PRESENT`, `ABSENT`, `COULD_NOT_OBSERVE`, and `STALE` (or exact successor semantics) according to the projection's claimed coverage.

## EXPLORE-3 — Deterministic observation backpressure for graph queries

Graph queries consume cognition and budget even when read-only.

Bound graph retrieval by deterministic policy such as:

- max hops;
- max nodes/edges;
- relation types;
- max returned tokens;
- max queries/total graph-observation budget per cell.

Over-broad queries should return typed refinement/backpressure rather than flooding model context.

## EXPLORE-4 — Minimal sufficient neighborhoods and conditional compression

Prefer the smallest structural neighborhood that resolves the current uncertainty. More graph context is not assumed to be better.

Compression/summarization is conditional:

- compact neighborhoods may be supplied directly;
- larger neighborhoods may use a separately qualified projection/compression step;
- raw graph evidence remains distinct from the active model-facing projection;
- compressed projections bind their own generation/provenance.

This strengthens the existing history-vs-active-projection and hierarchical-context-narrowing laws.

## EXPLORE-5 — Repository relations join the localization bundle

Repository graph evidence is one separately attributable localization channel alongside:

- issue/WorkPackage clues;
- entity/symbol structure;
- failing-test/runtime evidence;
- text/semantic retrieval;
- LSP/static-analysis/dynamic signals.

A localization handoff should preserve graph-query identity, source projection, anchor, relation/hop scope, and evidence refs rather than collapsing graph proximity into an opaque score.

Graph evidence is diagnostic structural evidence; it does not establish that a candidate location is the defect or that a proposed repair is correct.

## Additional supporting observations

- Prefer CODE-selected graph retrieval when applicability is mechanically known; permit bounded agent-initiated graph queries for emergent uncertainty.
- Repeated equivalent graph queries are eligible for the existing deterministic redundant-read/loop controls.
- Relationship intelligence and entity intelligence should live under one qualified code-intelligence capability family rather than create multiple new SSSF subsystems.
- Any graph/index implementation must earn admission through the replay/regression and fresh-frontier harness scorecard, measuring localization benefit, query/context cost, stale/CNO behavior, and downstream accepted outcomes.

## Non-decisions

This research does **not** authorize:

- RepoGraph installation;
- a persistent authoritative repository knowledge graph;
- immediate DSH-5 activation;
- graph-derived acceptance or workflow authority;
- treating absent static relationships as proven absence outside declared coverage;
- a roadmap/FUT-state promotion.