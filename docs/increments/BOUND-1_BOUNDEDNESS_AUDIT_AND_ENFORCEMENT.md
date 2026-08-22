# BOUND-1 — Boundedness audit and continuous enforcement

> **Planning state:** `SEQUENCED`, not `ACTIVE`, not `PROVEN`.
>
> **Authority:** Captain-directed cross-cutting requirement recorded in `docs/development/BOUNDEDNESS_LAW.md`.
>
> **Required timing:** complete and qualify before `SBX-2` activation. Do not disturb unrelated exact-head work already in flight.
>
> **Sequence effect:** this is a pre-SBX-2 cross-cutting gate only; it does not otherwise change Docker → baseline → Wayfinder → DSH ordering.

## Intent

Audit every current SSSF state surface that can grow with work, time, input, retries, descendants, observations, or retained output, then land a deterministic mechanism that continuously prevents silent reintroduction of unbounded growth.

Governing law:

> **Every list, queue, log, retry chain, event stream, child-agent set and retained-artifact surface needs an explicit bound or an explicit reason it is safely unbounded.**

The implementing increment must use the generalized form and requirements in `docs/development/BOUNDEDNESS_LAW.md`.

## Non-goals

- no new scheduler;
- no new runtime database;
- no generic resource-governance framework;
- no Docker/DSH implementation merely to perform the audit;
- no replacement of existing process, verification, evidence, planning or retention owners;
- no arbitrary reduction of evidence retention that conflicts with immutable proof obligations;
- no new paid service or external monitoring layer.

## Starting-state requirement

When activated, bind exact current canonical SSSF main/tree and current accepted owners. Re-observe source rather than assuming the research/planning snapshot still describes the implementation.

## Activation predecessor predicate

The smallest closed activation predicate is `BOUND1-ACTIVATION-PREDECESSOR-v1`, defined by Browser Sol ruling `SOL-FM-BOUND1-MECHANICAL-PREDECESSOR-001` at planning generation `e3e47458e6e2e9f40be6462eb0d7a81b2148ce88` / tree `3aab919810d41bbe9acc567fdca6dbdfb70bfbd6`, with this BOUND-1 document at blob `50195d65e1ec2d59d256352cf11c207212e26b91`.

Activation eligibility requires exactly these predecessor axes:

1. `recurrence-architecture-plan-independent-review` is `SATISFIED_WITH_EVIDENCE`, established by ruling `SOL-FM-RECURRENCE-PLAN-G5-NATIVE-MERITS-20260822-0324` over reviewed subject digest `3572d7f34c81d9b5f6e1b0a7a517c0b8430ede0934904cac0f1208ec73628782`.
2. `sssf-fut003-planning-foundation-repair-pr25` is bound to exact candidate `15dec5a2d4d7ce430052d0db0be1078d0a6e50e4` and has one of these terminal semantic dispositions:
   - `SEMANTICALLY_ACCEPTED_HELD`;
   - `LANDED_WITH_POST_MERGE_EXACT_MAIN_PROOF`;
   - `SUPERSEDED_BY_QUALIFIED_SEMANTIC_SUCCESSOR`.

At predicate definition time PR #25 satisfies the second axis as `SEMANTICALLY_ACCEPTED_HELD` under ruling `SOL-FM-SSSF-PR25-REPAIR-DELTA-APPROVED-20260822-0103` with exact-head CI run `32542027855` successful.

PR #25 landing is **not** required for BOUND-1 activation. PR #26 (`sssf-pr26-b4-002-head-scope-correction`) is not an activation predecessor and its landing is also not required. Publication-effect guards, LandingAuthorization consumers, Control #8 implementation, and later Control #9 implementation increments retain their own effect/landing/custody gates but do not broaden this activation predicate unless a direct resource dependency is observed.

Immediately before activation, re-observe:

- the exact PR #25 candidate identity and the continued applicability of its semantic disposition;
- the governed planning extent, lifecycle/state declarations, admission/exclusion rules, and normalization/canonicalization relevant to that disposition;
- that no active writer or mutation owner is changing the PR #25 candidate or its authoritative planning subject;
- the then-current exact SSSF main/tree and accepted implementation owners.

Unrelated supporting-research movement does not invalidate the predicate. A material change to BOUND-1 starting-state/sequence bytes, a material change to the governed planning axes above, candidate movement, active overlapping mutation, or inability to observe any required axis makes activation `CNO` until the predicate is re-qualified. Satisfying this predicate makes BOUND-1 activation-eligible; it does not itself activate BOUND-1, qualify the increment, unlock SBX-2, or waive publication, review, landing, security, cost, or evidence gates.

## Audit scope

At minimum inspect:

- accumulating in-memory/durable collections;
- queues, pending sets, scheduler backlogs, mailboxes/inboxes;
- process output buffers;
- logs, traces, event histories and evidence journals;
- caches and list/API accumulators;
- retry, repair and refinement chains;
- process/worker/sandbox concurrency sets;
- retained artifacts/evidence/archives;
- repository/worktree/sandbox caches and cleanup queues;
- schedule/reconciliation/delivery queues;
- currently implemented or contractually represented DSH child/depth/fan-out/budget surfaces;
- any additional monotone/growth state found during direct source inspection.

### Research-assisted discovery lens

The initial discovery pass may use the semantic questions preserved from `dzhng/skills` `audit-performance`, recorded at exact reviewed upstream identity in `docs/development/DZHNG_SKILLS_RESEARCH.md`.

For each candidate path/surface, ask at least:

- what triggers the work;
- what quantity can amplify: rows, bytes, pages, retries, descendants, files, jobs, events, duration, or another resource dimension;
- what the worst-case amplification depends on: input, history, tenants, outage duration, backlog, repeated failure, or time;
- what must change before another retry/poll/scan can make forward progress;
- whether a poison/terminal item can permanently occupy a queue head or fixed prefix;
- whether a partial recovery repeatedly restarts the same prefix instead of persisting progress;
- whether both sides of a transport and every durable/in-memory queue are bounded;
- whether an existing owner, cap, deadline, backoff, index, eviction rule, or healing mechanism already makes the candidate safely bounded;
- what deterministic overload/overflow behavior occurs when the boundary is reached.

This lens improves **surface discovery only**. An agent report, performance ledger, or semantic dismissal cannot establish boundedness. Registry ownership, source/enforcement evidence, boundary behavior, and the canonical validator remain authoritative. A candidate dismissed because it appears cheap or self-healing must still be represented if it is a growth surface covered by the governing law; the registry records the actual bound/derivation/invariant.

## Required registry

Produce one authoritative repository-contained machine-readable registry, recommended:

`docs/reference/BOUNDEDNESS_REGISTRY.json`

Every surface has one stable ID, one owner, source refs and one classification:

- `EXPLICIT_BOUND`
- `DERIVED_BOUND`
- `SAFE_UNBOUNDED`

Missing classification is non-compliant.

`SAFE_UNBOUNDED` is exceptional and requires the full safety/falsification fields specified by the governing law.

## Required validator

Produce one canonical deterministic validator, recommended:

`docs/validation/check_boundedness.py`

Required properties:

- bidirectional source declaration ↔ registry coverage;
- duplicate/missing/orphan owner rejection;
- bound/derivation validation;
- declared boundedness-delta validation;
- deterministic overflow-policy presence;
- `SAFE_UNBOUNDED` justification validation;
- machine-readable PASS/FAIL/CNO with FAIL > CNO > PASS;
- CI registration as a required check.

Changed-code discovery heuristics may supplement the source declarations but cannot become the authority.

## Required increment-protocol integration

The canonical increment protocol must require each implementation increment to declare added/changed/retired bounded surface IDs or `boundedness_delta: none` plus a specific not-applicable reason.

The planning branch already carries this requirement; BOUND-1 must ensure the accepted implementation eventually owns and enforces it rather than merely citing planning prose.

## Dynamic boundary proof

For each applicable dynamic bound, qualify `limit - 1`, `limit`, `limit + 1` or closest meaningful equivalents.

The `+1` case must produce the declared deterministic overflow/backpressure/retention result, never uncontrolled growth or semantically silent dropping.

## Watched-red

At minimum non-vacuously demonstrate detection of:

- removed limit;
- increased limit without declared delta;
- removed retry ceiling;
- disabled retention/eviction;
- removed child/depth/fan-out ceiling where applicable;
- source marker lacking registry entry;
- registry entry lacking source owner;
- duplicate surface/owner;
- missing overflow behavior;
- invalid `SAFE_UNBOUNDED`;
- CNO narrowed to PASS.

Generic digest mismatch is not sufficient watched-red evidence.

## Continuous proof obligations

After BOUND-1 lands:

- required CI runs the boundedness validator;
- implementation increments carry boundedness deltas;
- dynamic owners expose effective limit/utilization/overflow facts where practical;
- complete re-audit occurs before SBX-8, DSH-3, DSH-5 and DSH-8 and whenever a new scheduler/executor/store/cache/remote-transport/autonomous-descendant class enters the architecture;
- all re-audits update the same registry rather than creating another truth store.

## Acceptance

BOUND-1 is not complete until:

1. current growth surfaces are inventoried with stable IDs and singular owners;
2. every surface is explicitly/derived bounded or validly justified safe-unbounded;
3. overflow behavior is explicit;
4. required dynamic boundaries are tested;
5. registry and validator exist;
6. source↔registry coverage is bidirectional;
7. watched-red controls are property-specific and non-vacuous;
8. required CI runs the validator;
9. increment protocol boundedness-delta enforcement is accepted;
10. remaining CNO is explicit and non-PASS;
11. assignment-distinct semantic review finds no material omitted growth owner;
12. exact-head normal tests/validators/review/landing requirements pass.

## Governing review question

> **What grows, who owns the bound, what happens at +1, and how will CI know if that protection disappears?**