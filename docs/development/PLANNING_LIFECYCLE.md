# Future Planning Lifecycle

This document defines how future SSSF ideas move from conversation into durable engineering work without turning brainstorming into an accidental backlog.

## Governing distinction

**Preserved does not mean approved. Approved does not mean sequenced. Sequenced does not mean active. Active does not mean proven.**

The planning states are:

```text
EXPLORE
  -> PRESERVE
  -> CANDIDATE
  -> DECIDED
  -> SEQUENCED
  -> ACTIVE
  -> PROVEN
```

Side exits are `DEFERRED`, `REJECTED`, and `SUPERSEDED`.

## State meanings

### EXPLORE

Conversation only. Hypotheses, comparisons, research discussion, alternative architectures, and incomplete ideas live here.

- no durable repository entry is required;
- no implementation obligation exists;
- discussion does not imply approval.

### PRESERVE

Worth retaining as a future reference, idea source, or research input, but not yet an implementation candidate.

Examples include external catalogs, research repositories, and potentially useful patterns.

### CANDIDATE

A plausible future primitive that appears to address a real SSSF need and merits formal evaluation.

Before promotion beyond `CANDIDATE`, expand the item against the evaluation standard below.

### DECIDED

The architectural question has been resolved. The decision is authoritative design intent, but it may still have no implementation slot.

Architectural decisions belong in `docs/decisions/` and must not silently contradict current executable behavior.

### SEQUENCED

The decided work has an explicit dependency position in `docs/development/ROADMAP.md`.

`SEQUENCED` means implementation intent is approved, not that engineering should start immediately.

### ACTIVE

A named increment has crossed into the existing `INCREMENT_PROTOCOL.md` lifecycle. From this point, branch, source identity, acceptance, evidence, rollback, and certification are governed by the increment process.

### PROVEN

Implementation, proof, retained evidence, documentation, and immutable source identity agree. The item is part of the trusted system only to the extent recorded by the proof matrix and accepted Git state.

## Promotion rules

Promotion must be explicit. Do not infer promotion from enthusiasm, repeated discussion, or the existence of research.

Browser Sol may maintain these records when the Captain has explicitly made or approved the underlying decision. Browser Sol may recommend promotion during architecture discussion, but must distinguish a recommendation from an accomplished promotion.

Typical language:

- `preserve this` -> `PRESERVE`
- `promote this to candidate` -> `CANDIDATE`
- `we have decided this` -> `DECIDED`
- `sequence this` -> `SEQUENCED`
- implementation authorization with a named increment -> `ACTIVE`

A `SEQUENCED` item does **not** automatically create a FirstMate/control-plane task. Engineering transport begins when the item is activated as bounded work.

## Candidate evaluation standard

Before `CANDIDATE -> DECIDED`, record the answers that materially apply:

| Field | Required answer |
|---|---|
| Problem | What measured baseline limitation exists? |
| Evidence | Where is the limitation observable? |
| Primitive | What exact concept is being added or changed? |
| Owner | CODE / AGENT / ENGINEER, including mixed boundaries |
| Existing owner | What performs this responsibility now? |
| Replacement | What becomes unnecessary? |
| Inputs | Exact structured/context inputs |
| Outputs | Exact typed outputs |
| State | What persists and where? |
| Trigger | What starts it? |
| Verifier | How do we know it worked? |
| Negative control | How do we prove the verifier can fail? |
| Failure behavior | What happens when it does not work? |
| Rollback | How is baseline behavior restored? |
| Documentation | Which docs must change? |
| Documentation verifier | How is drift detected? |
| Telemetry | What evidence determines value? |
| Promotion criteria | What must be true before canonical adoption? |
| Retirement | What old mechanism is removed? |
| Net complexity | Did total live concepts go up or down? |
| Authority class | Which authority boundary is affected? |
| State transition | Which legal factory transition is added or changed? |
| Determinism boundary | Where does semantic judgment stop and rule execution begin? |
| Provenance | Can consequential outputs be traced to inputs, evidence, model/tool identity, and governing artifact version? |

Do not require this full table for `EXPLORE` discussion. It is a promotion gate, not a brainstorming tax.

## Durable locations

| State | Durable location |
|---|---|
| EXPLORE | Architecture conversation; no repository record required |
| PRESERVE | `FUTURE_CANDIDATES.md` or an existing research/reference record |
| CANDIDATE | `FUTURE_CANDIDATES.md` with evaluation status |
| DECIDED | ADR plus affected architecture docs |
| SEQUENCED | `ROADMAP.md` plus ADR/candidate linkage, and a typed edge in the roadmap's dependency graph |
| ACTIVE | Named increment, branch/PR, increment record |
| PROVEN | Accepted increment, evidence, docs, proof matrix, immutable Git identity |

## Dependency representation

A planning state says *how far* an item has come. It does not say *what blocks it*. Those are separate questions and they have separate owners.

Blocking is represented by typed edges and predecessor predicates in the roadmap's [machine-readable dependency graph](ROADMAP.md#machine-readable-dependency-graph), never by the order sections happen to appear in. Two consequences:

- a hard prerequisite (`HARD_PREREQUISITE`) and a mandatory-but-nonserializing commissioning proof (`NONSERIALIZING_COMMISSIONING`) are distinguishable without reading prose, and a blocked item exposes its exact dependency cone;
- accidental serialization by prose order is not a dependency, and a status projection must not read as globally stalled while independent executable nodes remain.

A gate may be reclassified from hard to soft only by explicit architecture or planning authority. Registering an item, adding an edge, or naming a predicate never advances that item's planning state.

### The graph's validator

Because the typed edges govern, the graph is enforced rather than merely declared. `docs/validation/check_planning_dependency_graph.py` is its canonical owner and runs in the offline gate through `ci/checks.json` alongside every other validator. It proves:

- the schema generation is recognized, so an unknown or stale graph fails closed rather than being skipped;
- node, predicate and status-axis identities are unique, and no name is reused across those namespaces;
- every edge endpoint, owner reference, register reference, predicate target and status-axis blocker resolves;
- only the declared edge-kind vocabulary appears, and only the declared authority classes and status-axis values;
- registration never promotes lifecycle state — a node may claim `ACTIVE` or `PROVEN` only if it already held that state, no axis may be registered `PASS`, and a node whose owning section declares a planning state must agree with it;
- Docker-first sequencing, the `WAYFINDER-0/1` hard pre-DSH chain and the Agent Lightning containment prerequisites are present and still hard, the Poker School relation is still nonserializing, and the Captain/source blocker still exempts the DSH cone;
- the graph stays reachable from `docs/manifest.yaml` and from this document;
- controls whose own review has not returned are referenced only inside the one authorized pending-dependency predicate.

Each of those properties is paired with a watched-red control that plants the exact defect in a copy of the real sources. A control that goes red for an unrelated reason is treated as a failure of the control, not as evidence, and the unmodified sources are asserted green in the same run so the set can never pass vacuously.

Anything the parser does not recognize is a red result. An unreadable graph is could-not-observe, never a pass.

## Authority boundary with FirstMate

Future planning is not an execution queue.

```text
Captain + Browser Sol
  explore / preserve / evaluate / decide / sequence
                |
                | activation boundary
                v
FirstMate + SSSF engineering flow
  investigate / implement / review / prove / land
```

FirstMate should not interpret `EXPLORE`, `PRESERVE`, or `CANDIDATE` items as assigned engineering work.

## Maintenance rule

When a future-planning discussion reaches a new durable state, Browser Sol should update the smallest authoritative document needed:

1. candidate register for `PRESERVE` or `CANDIDATE`;
2. ADR for `DECIDED` architecture;
3. existing roadmap for `SEQUENCED` work;
4. increment records only after `ACTIVE`.

Avoid duplicate planning documents. Extend the existing authority surface whenever one already exists.
