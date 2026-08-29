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
REF-1 DESIGN REVIEW — future-roadmap coverage + external benchmark research
        ↓
REF-1 — execute and freeze the approved Reference Workload Baseline
        ↓
Wayfinder / DSH / later architecture experiments
        ↓
replay REF-1 after each significant accepted SSSF advancement
        ↓
FirstMate compares candidate result against the preserved reference generation
```

REF-1 should not delay unrelated dependency-safe work. It becomes comparison-critical before a significant accepted SSSF advancement is credited as an improvement over the prior accepted factory generation.

If the reference workload can be run cleanly before the exact post-Docker/pre-DSH freeze without weakening that freeze, FirstMate may recommend the narrower sequencing that produces the strongest exact-generation comparison. The selected ordering must preserve an exact baseline SSSF generation and exact reference-run identity.

## Mandatory pre-freeze REF-1 design review

Before the **first** REF-1 execution is allowed to become the frozen baseline, FirstMate must perform a plan-only benchmark-design review. The purpose is to avoid freezing a convenient workload that later proves too narrow to evaluate the roadmap SSSF is actually pursuing.

The design review must assess the proposed reference project against the then-current roadmap and answer whether the workload provides meaningful observational surface for future changes in at least:

- ordinary serial Python ADW execution;
- workflow/orchestrator selection where later admitted;
- bounded specialist-agent backend changes;
- Docker/SandboxProvider behavior;
- verification, review, acceptance, retry, recovery and quiescence behavior;
- token/cost/latency and intervention burden;
- future parallel-ADW execution, where a replay can exercise a parallel-capable variant without changing the underlying product requirement beyond comparability;
- DSH specialist-node admission and later DSH capabilities that are actually admitted;
- context/compaction/memory changes that claim execution value;
- model/config/routing improvements that claim factory value;
- observability/control-plane improvements where the workload can expose their operational consequences;
- maker/checker, provenance, boundedness, exact identity and other acceptance-critical invariants.

The reference task does **not** need to exercise every future mechanism in its initial baseline configuration. It must instead provide enough product/task structure that future accepted architectures can solve materially the same job while exercising their new machinery without rewriting the benchmark into a different task.

FirstMate must explicitly identify roadmap objectives that the proposed workload cannot meaningfully test. For each uncovered objective, classify it as:

- `ACCEPTABLE_NONCOVERAGE` — the objective cannot reasonably be exercised by one stable workload or is better tested by its own dedicated qualification fixture;
- `REF_1_DESIGN_GAP` — the workload can and should be improved before freezing;
- `CNO` — current roadmap or implementation detail is insufficient to decide.

Any material `REF_1_DESIGN_GAP` must be corrected before the first baseline run is frozen. FirstMate may update the task, project shape, fixtures, acceptance contract or metric plan at this stage. After REF-1 is frozen, normal same-work/evaluator-drift rules apply and the original generation must not be silently rewritten.

### Required external benchmark research

As part of the pre-freeze design review, FirstMate must perform current online research into credible software-engineering agent benchmarks, reference workloads and evaluation practices that could improve REF-1 design.

Research should include, where relevant and current at review time:

- public coding-agent/software-engineering benchmarks;
- repository-level issue-resolution benchmarks;
- agentic coding evaluation suites;
- long-horizon or multi-step software-engineering task benchmarks;
- benchmark-design guidance for reproducibility, contamination/leakage resistance, deterministic grading, cost/token accounting, wall-time measurement, model/config attribution and longitudinal comparison;
- benchmark failure modes such as overfitting to one task, evaluator drift, environment variance, hidden external dependencies, non-reproducible starting state, or metrics that reward speed/cost while masking correctness regressions.

Examples worth investigating may include benchmark families such as SWE-bench and newer credible successors/alternatives, but **no named benchmark is preselected or automatically authoritative**. FirstMate must re-observe the current state of the field at review time and cite exact sources/versions/dates used.

FirstMate must compare at least three plausible approaches when feasible:

1. the locally designed REF-1 workload;
2. adaptation of a credible public benchmark/reference task into an offline, reproducible SSSF fixture;
3. a hybrid design that preserves a local stable product task while borrowing stronger grading/measurement/reproducibility techniques from external benchmarks.

The selected design should optimize for **longitudinal usefulness to SSSF**, not leaderboard compatibility. A public benchmark should not be adopted merely because it is popular if it introduces volatile dependencies, licensing/custody problems, hidden evaluator complexity, excessive run cost, contamination risk, weak coverage of SSSF-specific invariants, or poor reset/replay characteristics.

### Pre-freeze approval criteria

FirstMate should recommend freezing REF-1 only when the proposed workload is:

- complex enough to expose meaningful differences in planning/build/test/review/recovery behavior;
- small and deterministic enough for repeated execution after significant roadmap advancements;
- stable enough that task/evaluator bytes can remain frozen for a long period;
- broad enough to remain useful when SSSF later introduces registered parallel ADWs and bounded DSH specialist nodes;
- instrumentable through existing JSONL/SQLite/evidence owners;
- able to measure token/cost/time/intervention deltas without adding a second telemetry system;
- resistant to false improvement from evaluator relaxation, changed starting state, hidden environment changes or trivial shortcut solutions;
- simple enough that benchmark machinery does not become an architectural subsystem of its own.

If the initial proposed REF-1 is inferior to a researched alternative or hybrid under these criteria, **FirstMate is authorized to revise the proposed REF-1 design before first execution/freeze**. This is design refinement, not permission to bypass normal execution/acceptance gates or to alter a REF-1 generation after it has been frozen.

The pre-freeze report must preserve the rejected alternatives and reasons so later maintainers can understand why the final reference workload was chosen.

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
8. **Significant-advancement replay:** after each significant accepted SSSF advancement, rerun REF-1 against the new exact factory generation before that advancement is credited as a material improvement. Trivial documentation, formatting, or otherwise non-behavioral changes do not trigger a replay.
9. **FirstMate comparison obligation:** FirstMate must compare the new REF-1 result against the preserved baseline and the immediately prior accepted comparison generation, identify material deltas, distinguish architectural changes from model/config/runtime changes, and report regressions/CNO rather than smoothing them away.
10. **No benchmark gate inflation:** REF-1 is a comparison/evidence obligation for significant advancements; it does not replace the increment's own correctness, safety, review, or landing gates.

## Significant advancement trigger

A change should be treated as significant for REF-1 replay when it materially alters one or more of:

- ADW/workflow structure or workflow selection;
- AgentBackend/harness integration;
- DSH admission or materially different DSH capability;
- serial versus parallel execution/fan-out/join behavior;
- SandboxProvider/runtime execution path;
- retry, repair, refinement, cancellation, recovery, or quiescence behavior;
- verification/review/acceptance machinery;
- model routing or configuration policy when intended as a factory improvement;
- context/memory/compaction behavior that materially affects agent execution;
- substantial observability/control-plane changes claimed to improve autonomy, correctness, latency, cost, or operator burden;
- any other architecture change for which FirstMate or Browser Sol intends to claim material factory value.

When classification is genuinely ambiguous, prefer a replay if the run cost/effort is low; otherwise record why the change is non-significant. Do not create a semantic-review bureaucracy around trivial changes.

## Required FirstMate comparison report

For each significant replay, FirstMate should produce a concise durable comparison containing at least:

- baseline REF-1 generation and exact run identity;
- immediately prior accepted comparison generation, if one exists;
- candidate SSSF exact commit/tree and material runtime/model/config identities;
- accepted/failed/CNO status;
- token delta total and by phase where comparable;
- wall-time delta total and by phase where comparable;
- agent-call/retry/revision delta;
- deterministic gate/test/review delta;
- Captain/Browser-Sol intervention delta;
- sandbox/concurrency/resource delta where comparable;
- cleanup/quiescence result;
- correctness/safety/provenance/maker-checker regressions or improvements;
- changed comparison inputs that limit attribution;
- conclusion using a small vocabulary such as `IMPROVED`, `REGRESSED`, `MIXED`, `NO_MATERIAL_CHANGE`, or `CNO`, with the underlying metrics retained rather than collapsed into an opaque score.

`IMPROVED` must not be emitted when a required correctness, safety, provenance, maker/checker, acceptance, or quiescence property regressed merely because tokens or latency improved.

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

- the mandatory pre-freeze design review completed and its external sources/alternatives are durably identified;
- all material `REF_1_DESIGN_GAP` findings were corrected or explicitly escalated before freeze;
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
- rerunning does not overwrite the original evidence generation;
- a significant advancement cannot be labeled `IMPROVED` without a bound REF-1 replay/comparison or an explicit CNO/non-comparability record.

## FirstMate planning obligation

FirstMate should perform a plan-only assessment and recommend:

1. the exact reference project/task that provides enough complexity without unnecessary scope;
2. a roadmap-objective coverage matrix showing what REF-1 can and cannot meaningfully evaluate;
3. current online benchmark/evaluation research with exact sources/versions/dates and at least three plausible design approaches where feasible;
4. whether the local REF-1 design should be retained, adapted from a public benchmark, or replaced by a hybrid design;
5. which existing baseline ADW should execute it;
6. whether any minimal deterministic fixture/test scaffolding is required;
7. the exact immutable input/evaluator/run identities to freeze;
8. the metric extraction mapping from existing SQLite/JSONL/evidence owners;
9. which metrics are already available versus currently CNO;
10. the narrowest sequencing point relative to `BASELINE-PR` and the post-Docker/pre-DSH freeze;
11. the ordinary increment/activation needed to execute and freeze REF-1;
12. the exact significant-advancement classifier and the smallest reliable mechanism that causes FirstMate to request/perform a REF-1 replay at those checkpoints;
13. the durable comparison-report location/format that reuses existing owners rather than creating a new benchmark state machine;
14. how later DSH, parallel-ADW, orchestration, Agent Lightning, observability, or other material changes should invoke REF-1 comparison before claiming improvement.

## Simplification constraints

REF-1 must obey the SSSF simplification hierarchy:

- no new benchmark database;
- no standing benchmark daemon;
- no benchmark-specific agent orchestrator;
- no opaque composite score;
- no new workflow if an existing ADW is sufficient;
- no external service merely to make the benchmark realistic;
- no mandatory rerun for changes too small to make a material value claim;
- prefer deterministic read-only projections over new stateful machinery;
- prefer an existing increment/roadmap transition hook for significant-advancement replay over a new scheduler/monitor;
- external benchmark research may improve REF-1 design but must not import unnecessary benchmark infrastructure into SSSF.

**Default:** research and validate the benchmark design before first execution; then freeze one stable reference task, one exact starting project state, one accepted baseline Python ADW run, one existing trace/evidence spine, and append-only later comparisons after significant accepted advancements.
