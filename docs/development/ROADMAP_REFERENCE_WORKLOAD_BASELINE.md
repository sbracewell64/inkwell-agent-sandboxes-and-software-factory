# Roadmap Amendment — Longitudinal SSSF Reference Workload Baseline

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Purpose:** establish one simple-but-sufficiently-complex end-to-end software project as a stable reference workload for comparing later SSSF architecture generations against the baseline factory.

This amendment does not activate an increment, bypass any existing prerequisite, authorize DSH, or create a new execution/state/observability owner. It reuses the existing ADW, verification, JSONL/SQLite trace, evidence, and acceptance machinery.

## Why this exists

`BASELINE-PR` proves that the accepted Docker-backed SSSF path can complete a real ordinary engineering PR. That commissioning proof is necessary, but it is not by itself a stable longitudinal benchmark: the task may be one-off, its complexity may vary, and later SSSF generations would have no fixed workload against which to compare token use, wall time, retries, defects, or intervention burden.

SSSF should therefore preserve one **Reference Workload Baseline** whose task/input/acceptance contract can be replayed against later accepted factory generations.

The objective is not benchmark theater or model leaderboard scoring. The objective is a reconstructable answer to:

> **Did this SSSF change make the same bounded software-engineering job materially better, worse, safer, simpler, faster, cheaper, or more autonomous?**

## Position in the roadmap

Preferred sequence:

```text
Docker commissioning / accepted Docker-backed SSSF path
        ↓
BASELINE-PR
        ↓
post-Docker / pre-DSH immutable SSSF baseline
        ↓
REF-1 — execute and freeze the Reference Workload Baseline
        ↓
Wayfinder / DSH / later architecture experiments
        ↓
replay REF-1 when a later accepted generation makes a material value claim
```

REF-1 should not delay unrelated dependency-safe work. It becomes comparison-critical only before a later architecture claims improvement over the baseline factory.

If the reference workload can be run cleanly before the exact post-Docker/pre-DSH freeze without weakening that freeze, FirstMate may recommend the narrower sequencing that produces the strongest exact-generation comparison. The selected ordering must preserve an exact baseline SSSF generation and exact reference-run identity.

## Reference project shape

FirstMate should select or create the **smallest project that is complex enough to exercise the actual factory rather than a toy one-file edit**.

Preferred characteristics:

- local/offline and deterministic where practical;
- no paid service or external API dependency;
- no secret/credential requirement;
- no browser/cloud deployment requirement;
- small enough to rerun without becoming an operational burden;
- complex enough to require genuine planning, implementation, deterministic testing, semantic review, and documentation;
- multiple files/modules and at least one nontrivial data or state transformation;
- positive and negative/error-path behavior;
- deterministic automated acceptance tests;
- clear user-visible outcome;
- suitable for a fresh disposable repository or exact resettable starting commit;
- stable task specification that can remain frozen across future comparisons.

A small CLI or local application with a few interacting modules, persistence or structured data, validation/error paths, tests, and documentation is preferable to a trivial text change. Avoid choosing a project whose difficulty is dominated by external services, UI pixel judgment, volatile upstream APIs, or environment setup unrelated to SSSF orchestration quality.

FirstMate should recommend the exact project/task rather than silently inventing unnecessary product scope.

## Baseline execution architecture

The baseline run should deliberately exercise the current SSSF founding architecture:

```text
frozen task contract
    ↓
registered Python ADW
    ↓
bounded specialist agent phase(s)
    ↓ CODE-owned transition(s)
    ↓
deterministic tests / gates
    ↓
independent semantic review where applicable
    ↓
CODE-owned acceptance / terminal state
    ↓
trace + evidence freeze
```

Do not add DSH captain, adaptive topology, parallelism, Agent Lightning, new memory systems, new evaluators, or other future architecture merely to make the reference workload sophisticated. The value of REF-1 is that it represents the simpler accepted factory.

If the baseline registered ADW set already contains an appropriate end-to-end script, use it. Do not create another workflow unless the existing ADWs cannot truthfully execute the reference project.

## Frozen comparison inputs

A valid reference baseline should bind at least:

- `reference_workload_id` and generation;
- exact task/specification bytes or digest;
- exact initial project repository/commit/tree;
- deterministic test/acceptance contract and generation;
- exact SSSF repository/commit/tree;
- exact ADW/workflow identity;
- exact configuration/profile identities that materially affect execution;
- exact AgentBackend/harness/model identities where observable;
- exact SandboxProvider/runtime identity;
- applicable tool/capability policy identity;
- reviewer protocol/assignment identity where applicable;
- run/adw/evidence identities;
- environmental facts material to comparability.

A later replay must either preserve the comparison-relevant inputs or explicitly report what changed. Do not attribute a result to SSSF architecture when the task, model, evaluator, sandbox resources, or material configuration changed without accounting for that change.

## Required metrics

Use existing authoritative trace/evidence owners wherever possible. Do not create a second benchmark telemetry system merely for REF-1.

At minimum record, when observable:

### Efficiency

- total token usage;
- token usage by agent/phase where the existing trace can attribute it;
- total reported inference cost, including `0` or CNO where appropriate;
- end-to-end wall-clock duration;
- duration by phase;
- agent-call count;
- retry/fix/revision counts;
- deterministic command/test invocation count.

### Quality / correctness

- final deterministic test/gate outcomes;
- semantic review outcome and blocking-finding count;
- number and class of failed attempts;
- number and class of `COULD_NOT_OBSERVE` outcomes;
- post-acceptance regression result if the contract requires one;
- exact accepted artifact/project identity.

### Factory behavior

- selected ADW/workflow identity;
- phase sequence actually executed;
- human/Captain interventions required after initial task submission;
- Browser Sol decisions required, if any;
- sandbox/resource count and peak concurrency where observable;
- cancellation/recovery events;
- cleanup/quiescence result;
- provenance/maker-checker/landing evidence status.

### Output size/context

Where useful and deterministic, record project file count, changed-file count, diff insertions/deletions, generated artifact count, and other simple workload-size facts so later comparisons can detect a materially different output rather than misread it as an efficiency improvement.

## Existing SQLite/JSONL integration

The reference workload uses the existing SSSF trace spine:

```text
typed run/phase/agent/gate events
        ↓
raw durable JSONL/history
        +
existing SQLite query projection (`sssf.db`)
        ↓
reference metric projection / human-readable report
```

The current baseline tracer already records session `total_tokens`, `total_cost`, phase lifecycle, event token fields, envelopes, gates, processes, and agent-session facts. REF-1 should consume those owners rather than duplicating them.

Any small reference-report generator should be a deterministic read-only projection over accepted trace/evidence data. It must not become a second state authority.

## Repeatability and comparison law

A later SSSF generation receives improvement credit only if the comparison is meaningful.

Required rules:

1. **Same-work requirement:** the frozen reference task and acceptance contract remain equivalent unless a new reference generation is explicitly created.
2. **Exact-generation attribution:** every result binds the exact SSSF generation and material backend/model/config/runtime generations actually used.
3. **No silent evaluator drift:** acceptance criteria cannot be relaxed to manufacture improvement.
4. **Three-valued metrics:** unavailable metrics are CNO/unknown, never `0` and never implied improvement.
5. **No single-metric optimization:** lower tokens or lower wall time do not override correctness, safety, provenance, maker/checker, cleanup, or acceptance regressions.
6. **Comparable model policy:** if model/provider/profile changes materially, report the comparison as architecture+model/config change or run a controlled comparison where practical; do not attribute the entire delta to SSSF architecture.
7. **Stable baseline preservation:** never overwrite the original run/evidence. Later replays append comparison generations.
8. **No forced rerun cadence:** replay REF-1 when a material architecture change claims value, not after every trivial commit.

## Candidate scorecard

A future comparison report may use a compact table such as:

| Metric | Baseline REF-1 | Candidate generation | Delta | Comparable? |
|---|---:|---:|---:|---|
| Accepted | PASS | PASS/FAIL/CNO | — | yes/no |
| Total tokens | observed | observed | % | yes/no |
| Wall time | observed | observed | % | yes/no |
| Agent calls | observed | observed | n | yes/no |
| Retries/revisions | observed | observed | n | yes/no |
| Blocking review findings | observed | observed | n | yes/no |
| Captain interventions after launch | observed | observed | n | yes/no |
| CNO outcomes | observed | observed | n | yes/no |
| Clean quiescence | PASS | PASS/FAIL/CNO | — | yes/no |

This is a projection, not an aggregate scalar score. SSSF should not collapse correctness, safety, cost, autonomy, and latency into one opaque number unless a later separately justified decision requires it.

## Qualification / watched-red controls

Before REF-1 is treated as a valid baseline, prove at least:

- a clean reset reproduces the exact initial project identity;
- task/spec bytes are immutable for the generation;
- deterministic acceptance tests are pinned and maker-protected under applicable policy;
- the run uses an accepted registered Python ADW rather than an ad hoc transcript-driven workflow;
- required phases/events appear in the trace;
- token/cost/time metrics are harvested from authoritative owners or marked CNO;
- a deliberately missing metric is reported CNO rather than zero;
- a deliberately changed task/evaluator/model/config is detected as non-equivalent or explicitly qualified;
- failed/rejected runs do not become the reference PASS;
- raw evidence and the human-readable metric report bind the same run identity;
- rerunning does not overwrite the original evidence generation.

## FirstMate planning obligation

FirstMate should perform a plan-only assessment and recommend:

1. the exact reference project/task that provides enough complexity without unnecessary scope;
2. which existing baseline ADW should execute it;
3. whether any minimal deterministic fixture/test scaffolding is required;
4. the exact immutable input/evaluator/run identities to freeze;
5. the metric extraction mapping from existing SQLite/JSONL/evidence owners;
6. which metrics are already available versus currently CNO;
7. the narrowest sequencing point relative to `BASELINE-PR` and the post-Docker/pre-DSH freeze;
8. the ordinary increment/activation needed to execute and freeze REF-1;
9. how later DSH, parallel-ADW, orchestration, Agent Lightning, observability, or other material changes should invoke REF-1 comparison before claiming improvement.

## Simplification constraints

REF-1 must obey the SSSF simplification hierarchy:

- no new benchmark database;
- no standing benchmark daemon;
- no benchmark-specific agent orchestrator;
- no opaque composite score;
- no new workflow if an existing ADW is sufficient;
- no external service merely to make the benchmark realistic;
- no mandatory rerun for changes too small to make a material value claim;
- prefer deterministic read-only projections over new stateful machinery.

**Default:** one frozen reference task, one exact starting project state, one accepted baseline Python ADW run, one existing trace/evidence spine, and append-only later comparisons.
