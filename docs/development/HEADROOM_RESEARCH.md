# Headroom Research

## Status

`PRESERVE` / supporting research and controlled-pilot candidate only.

This document preserves SSSF/FirstMate-relevant findings from:

- `headroomlabs-ai/headroom`
- Apache-2.0
- current repository state reviewed 2026-08-19

This research does **not** authorize wholesale Headroom deployment, proxy/wrapper insertion, shared memory, automatic instruction learning, output shaping, adaptive compression state, or roadmap/FUT promotion.

## Governing interpretation

Headroom is potentially useful as a replaceable implementation behind an existing observation/context-projection seam, especially for bulky structured tool outputs consumed by FirstMate and later DSH.

> **Raw evidence remains owned by FirstMate/SSSF. Headroom may produce a cheaper model-facing projection; compression never changes authority or truth.**

## PRESERVE-1 — Narrow FirstMate controlled pilot is authorized

A future controlled pilot may test a pinned exact Headroom library generation on read-only, bulky observations such as:

- GitHub list/search/API JSON;
- GitHub Actions/CI logs;
- large command/test logs;
- bulk issue/PR metadata;
- repetitive search-result collections.

Initial pilot should exclude source code, review-critical diffs/patches, requirements, WorkPackages, Browser Sol rulings, review/security findings, acceptance evidence, and small observations where exact content is preferable to compression.

## PRESERVE-2 — Library seam only for initial qualification

Initial pilot should use the smallest library/SDK compression surface behind a FirstMate-owned adapter.

Do **not** initially use:

- `headroom wrap`;
- transparent provider proxying;
- turnkey deployment;
- Serena user-scope installation/configuration;
- shared/cross-agent memory;
- `headroom learn --apply`;
- output shaping;
- model-effort routing;
- code compression;
- adaptive TOIN learning;
- automatic context-management ownership.

These features introduce additional behavioral variables, configuration mutation, memory ownership, or runtime interception that conflict with stronger SSSF owners or would undermine causal qualification.

## PRESERVE-3 — Compression is a projection, never canonical observation state

The raw tool/result observation remains canonical under its existing FirstMate/SSSF owner.

A compressed representation is a derived model-facing projection and should bind provenance such as:

- raw observation identity/reference/digest;
- exact compressor implementation/generation;
- projection digest;
- token count before/after;
- compression/passthrough/failure disposition;
- retrieval/refinement provenance when additional raw content is requested.

Headroom CCR or another implementation cache must not become the sole authoritative retention mechanism for evidence required by replay, review, or qualification.

## PRESERVE-4 — Reversible retrieval fits observation backpressure

The useful Headroom pattern is:

```text
exact raw observation
        ↓
compressed active projection
        ↓
agent reasoning
        ↓
semantic uncertainty remains
        ↓
bounded retrieval/refinement
```

This is consistent with existing SSSF hierarchical-context-narrowing, observation-backpressure, MemGPT, RepoGraph, AutoCodeRover, and SWE-agent findings.

Retrieval remains CODE-bounded and provenance-bearing rather than unrestricted context expansion.

## PRESERVE-5 — Compression must be source/state aware

Wall-clock freshness is insufficient for engineering evidence.

Any future projection/retrieval integration should bind relevant source/execution identity such as:

- repository/source generation when applicable;
- execution cell/inner unit;
- observation generation;
- task/phase;
- raw-result digest.

A stale cached projection must not silently masquerade as current evidence.

## PRESERVE-6 — Compression quality requires SSSF workload qualification

Headroom project benchmarks are useful supporting evidence but are not SSSF admission proof.

Qualify the exact pinned generation against representative FirstMate work using controlled experiments where possible.

At minimum measure:

- input tokens;
- model calls;
- wall time;
- monetary cost;
- raw-retrieval rate;
- missed-fact rate;
- incorrect localization/diagnosis attributable to compression;
- accepted engineering outcome;
- Captain interventions.

Add a `compression_regret` diagnostic: how often a compressed projection omitted information whose absence or later retrieval materially harmed the task.

## PRESERVE-7 — Fail-open does not mean proof-preserving

A compressor may fail open operationally by returning unchanged content, which is useful for availability.

However, successful compression itself does not prove semantic equivalence. A projection that reduces tokens may still omit task-relevant information.

Therefore:

- compression success is not verification;
- project claims such as "same answers" remain empirical objectives, not SSSF invariants;
- high-risk/exact evidence classes may remain passthrough until specifically qualified.

## PRESERVE-8 — Adaptive compression state is behaviorally material

Features such as TOIN that learn which fields/items matter can cause the same raw input to produce different projections depending on accumulated local state.

Initial pilot should disable adaptive learning.

If adaptive compression is ever admitted later, its learned-state generation/digest, policy, and cohort become part of effective runtime identity and replay qualification.

## PRESERVE-9 — `headroom learn` is candidate mining only

Failed-session analysis may be useful for discovering possible instruction improvements.

Any learned recommendation should enter the existing FUT-011 instruction-governance lifecycle as an `INSTRUCTION_CANDIDATE` with provenance and behavioral qualification.

Headroom must not write or promote active FirstMate/SSSF instruction authority automatically.

## PRESERVE-10 — Do not adopt Headroom memory as a parallel truth system

Headroom persistent/cross-agent memory overlaps with SSSF's stronger separation of:

- authoritative state/evidence;
- exact durable history;
- derived semantic memory;
- active model projection.

Do not introduce Headroom memory as a second owner of durable state, cross-agent cognition, replay-visible history, maker/checker context, or project truth.

## PRESERVE-11 — Output shaping and reasoning-effort routing are separate experiments

Compression and model-effort/verbosity policies are different behavioral variables.

Initial Headroom qualification should keep output shaping and effort routing disabled. Any future effort-routing experiment should be qualified independently and remain CODE/model-profile policy rather than implicit compressor authority.

## PRESERVE-12 — SSSF placement

Headroom should not sit as another control-plane layer or orchestrator.

Preferred placement:

```text
raw typed observation
        │
        ├── canonical raw state retained by owner
        │
        └── projection seam
                ↓
        Headroom or alternative compressor
                ↓
        bounded model-facing observation
```

The implementation behind this seam remains replaceable.

## FirstMate controlled-pilot acceptance concept

A pilot is useful only if the pinned Headroom generation materially reduces context/token/cost pressure **without degrading accepted engineering outcomes or increasing Captain intervention**.

A favorable token-saving number alone is insufficient for admission.

If results are positive, Headroom remains an implementation candidate behind FirstMate/DSH observation projection, not a new architectural layer.

## Routing

- FirstMate: future controlled observation-compression pilot.
- `FUT-001` / DSH: later observation/context-projection implementation candidate.
- Existing context/history/provenance research: supporting reference.
- `FUT-011`: `headroom learn` only as instruction-candidate mining, never direct promotion.

## Non-decisions

This authorization does **not**:

- install Headroom now;
- authorize a global/user-scope wrapper;
- authorize a provider proxy;
- authorize Serena installation;
- authorize Headroom memory/cross-agent memory;
- authorize automatic instruction mutation;
- authorize output shaping/effort routing;
- authorize code compression;
- promote a FUT candidate or change roadmap sequencing;
- alter the Docker-first → baseline → Wayfinder → DSH implementation order.
