# BOUND-1 — Boundedness audit and continuous enforcement

> **Planning state:** `ACTIVE`. BOUND-1 left `SEQUENCED` when this isolated
> implementation lineage performed the named-increment activation transition
> recorded under [Activation transition](#activation-transition).
>
> **What this increment is:** a landed implementation. BOUND-1 is **not**
> accepted, **not** certified, and **not** `PROVEN`. It does **not** unlock
> `SBX-2` and does not waive publication, review, landing, security, cost, or
> evidence gates.
>
> **Authority:** Captain-directed cross-cutting requirement recorded in
> `docs/development/BOUNDEDNESS_LAW.md`; activated under Browser Sol standing
> authority, predicate `BOUND1-ACTIVATION-PREDECESSOR-v1`, rulings
> `SOL-FM-BOUND1-MECHANICAL-PREDECESSOR-001` and
> `SOL-FM-BOUND1-PREDECESSOR-PLANNING-BINDING-20260822-1704`.
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

---

# Implementation record

The sections above are the increment's specification, unchanged from the
canonical bytes on `main`. The sections below record what this lineage actually
did against it.

## Non-goals, held

No new scheduler, registry, queue, watcher, database, boundedness authority, or
planning state machine was created. No runtime database, generic
resource-governance framework, Docker/DSH implementation, paid service, or
external monitoring layer was added. No existing process, verification,
evidence, planning, or retention owner was replaced. No evidence retention was
reduced in a way that conflicts with an immutable proof obligation: the earlier
HD-08 watched-red capture at
`docs/evidence/hd08/intermediate-component-tocttou-red-e10712b9ed01.txt` is
retained unchanged, and the recalibrated companion was added alongside it.

## Activation transition

### Predicate reobservation, immediately before mutation

Every axis of `BOUND1-ACTIVATION-PREDECESSOR-v1` was reobserved in this lineage
before any file was written.

| Axis | Observation | Evidence |
| --- | --- | --- |
| `recurrence-architecture-plan-independent-review` | observed-good — `SATISFIED_WITH_EVIDENCE`, unchanged | ruling `SOL-FM-RECURRENCE-PLAN-G5-NATIVE-MERITS-20260822-0324` over reviewed subject digest `3572d7f34c81d9b5f6e1b0a7a517c0b8430ede0934904cac0f1208ec73628782` |
| PR #25 exact candidate identity | observed-good — open, unmerged, exact at `15dec5a2d4d7ce430052d0db0be1078d0a6e50e4`, tree `c1df8377c69797bc9093febb11ebbf528573e3cf` | `git ls-remote origin refs/pull/25/head`; `gh-axi pr view 25` |
| PR #25 base | observed-good — unchanged at `991d3a64f1b96a8b9637f97060d692af3518228f` | `git ls-remote origin refs/heads/main` |
| PR #25 semantic applicability | observed-good — `SEMANTICALLY_ACCEPTED_HELD` still applies; the candidate has not moved since the accepted disposition | ruling `SOL-FM-SSSF-PR25-REPAIR-DELTA-APPROVED-20260822-0103`, exact-head CI run `32542027855` |
| Planning generation | observed-good — exactly `e339b2441de15f54935df80bb7760b274d094242`, tree `38520bf48b5ef90af3aedb6cb996488f95166bc7`, BOUND-1 blob `79cc8a19d88dfc939f52274fdb2607f717661860` | `git ls-remote origin refs/heads/planning/future-sssf`; `git ls-tree -r` |
| Governed planning axes | observed-good — from former authority `d75103fb7ef8dd4ca40f62d40fc7479369bbdf0b` to current planning the delta is three research documents plus the BOUND-1 increment; planning-state, future-candidate, roadmap, DSH-plan, and ADR-0004 bytes are unchanged | `git diff --name-only d75103fb e339b244` |
| Active writer on PR #25 or the planning subject | observed-good — none. The PR #25 owner is `paused` read-only with its exact pushed head preserved; the successor-planning worker is `paused` on `candidate-publication-effect-guard`; every other live task is on a different repository or a distinct preserved branch | fleet task status files under `kun-agent-workspace/state/` |

No axis moved, overlapped, or was could-not-observe, so activation proceeded.
Herdr pane inspection was not performed in this lineage because this brief's
Herdr lifecycle declaration is NOT ENABLED; the status-file observation above is
the evidence used, and it is a positive observation rather than an inference
from absence.

### Bindings taken at activation

Activation bound exact SSSF main `991d3a64f1b96a8b9637f97060d692af3518228f`,
tree `7b88546cd1f63e8304325ee35be37893268ae0e0`, and 49 surfaces.

### Rebinding, after main moved

The activation transition above stands as taken. Main then moved to
`8aadd50461b184cede949f21ecf426146f2915a0` while this lineage was held by the
candidate-publication quarantine, and the audit was re-executed against the
source owners that move brought in rather than kept against the generation it
was activated on.

- **Exact SSSF main:** `8aadd50461b184cede949f21ecf426146f2915a0`
- **Exact SSSF main tree:** `f1b779f73bea2b33810e5663e9dc2f3b82ea9299`
- **Accepted implementation owners bound:** the 53 surfaces enumerated in
  `docs/reference/BOUNDEDNESS_REGISTRY.json`, each naming one owner file and one
  owner symbol in the current source rather than in a planning or research
  snapshot.

Five commits landed in that window — PR #25, #30, #31, #33 and #34. PR #25 is
the one that carries this increment's own specification and
`docs/development/BOUNDEDNESS_LAW.md` into the repository, so the spec sections
above are now main's canonical bytes rather than a copy taken from the planning
blob; this record adds only the activation state to their header. The other four
landed roughly ten thousand lines of new execution surface, and re-reading them
is what produced the four surfaces and the defect recorded under
[What the re-audit added](#what-the-re-audit-added).

The registry records the current two identities in `bound_sssf_main` and
`bound_sssf_tree`, so a later reader can tell which source generation the audit
was actually taken against.

## What landed

### Registry

`docs/reference/BOUNDEDNESS_REGISTRY.json` — one authoritative,
repository-contained, machine-readable registry. 53 surfaces: 43
`EXPLICIT_BOUND`, 7 `DERIVED_BOUND`, 3 `SAFE_UNBOUNDED`. Every entry carries a
stable id, a singular owner, source refs, surface kind, resource dimensions,
classification, policy identity, admission/backpressure, deterministic
`on_limit_behavior`, retention/cleanup, observability, verification refs, and a
three-valued status.

Two scope exclusions are recorded explicitly rather than left as silent gaps:
the Inkwell demonstration application (the factory's workload, not an SSSF
execution surface) and the installer templates (whose installed copies under
`adws/` are the surfaces this registry binds).

### Validator

`docs/validation/check_boundedness.py` — registered in required CI as
`boundedness-registry-validator`. It emits machine-readable
`PASS` / `FAIL` / `CNO` with `FAIL > CNO > PASS`, and returns a distinct
non-zero exit for CNO so that could-not-observe can never be read as a pass.

- **Bidirectional coverage.** Every `BOUNDEDNESS-OWNER` marker in source
  resolves to exactly one registry entry, and every registry entry resolves to
  a marker in its declared owner file. Duplicate ids, duplicate markers,
  competing owners, missing owner files, and orphaned `BOUNDEDNESS-POLICY`
  declarations are all failures.
- **Probes, not prose.** Each `EXPLICIT_BOUND` names a probe that re-reads the
  limit out of the owner's source with `ast` — a module constant, a dataclass
  field default, or a single-site regex for non-Python owners — and fails when
  the registry and the owner disagree. Removing a limit, renaming it, or raising
  it without declaring the boundedness delta all go red here. Where a ceiling is
  genuinely caller-supplied, the entry names the enforcement symbol instead and
  the validator requires that symbol to still exist.
- **Justification anchors.** A `SAFE_UNBOUNDED` entry whose oversight path
  disappeared is no longer justified, so the validator fails if the reclaim
  procedure leaves `docs/operations/RECOVERY.md`, if a declared journal path
  stops being gitignored, or if `run_record.list_runs` stops raising on an
  unreadable record.
- **Increment-protocol enforcement.** Every document under `docs/increments/`
  must declare a `boundedness_delta`, either naming surfaces the registry knows
  or `none` with a specific reason.

### Dynamic boundary proof

Fifteen controls exercise `limit - 1`, `limit`, and `limit + 1` against the real
enforcement owners — not fixtures built to pass. The `+1` case must produce the
declared deterministic result:

`BoundedStreamCapture` (truncate with both counts retained) · `BoundedJournalWriter`
(refuse plus one terminal truncation record) · `ChildDeadline` (a real
overrunning child is cancelled, a well-behaved one is not) · `AttemptBudget`
(reject, with spent attempts never uncharged) · supervisor required ceilings
(refuse a launch with no positive wall clock or output ceiling) ·
`permissions.preserve` (aggregate ceiling, every declined path named) ·
`RECOVERED_LIMIT` · bounded phase-error text · the in-memory lifecycle stores ·
`ResourceBounds` (zero is never an implicit unlimited value) · the CI gate's
bounded check output · the evidence-manifest read-byte and path-depth ceilings.

### Watched-red

Twenty-eight property-specific controls, each mutating a copy of the repository
and each **required to fail for its own reason** — the finding must contain the
fragment that names the property. A generic "the document changed" failure is
explicitly not accepted as evidence for any of them. Before any mutation runs,
the baseline fixture is asserted clean, so a control cannot be red for a reason
that has nothing to do with what it names.

Covered: removed limit · limit raised without a declared delta · removed retry
ceiling · removed child wall-clock ceiling · disabled retention procedure ·
source marker without a registry entry · registry entry without an existing
owner source · registry entry without a source marker · duplicate surface
identity · duplicate owner · missing overflow behaviour · missing classification
· invalid `SAFE_UNBOUNDED` justification · `SAFE_UNBOUNDED` resting on an excuse
the law refuses · CNO narrowed to PASS · derived bound with an orphaned parent ·
derived bound with no recorded derivation · increment without a boundedness
delta · protocol no longer requiring a delta · validator removed from required
CI · governing law weakened · journal path no longer gitignored · zero bound
with no declared meaning · removed durable effect-authority ceiling · removed
planning git byte ceiling · removed planning git deadline · removed doctor
child output ceiling · a boundedness delta declared only in prose rather than
in the fenced form the protocol requires.

### Bounds the audit had to ADD

Surfaces that were genuinely unbounded before this increment, now bound in their
existing owners:

| Surface | Was | Now |
| --- | --- | --- |
| `sssf.permissions.preserve_total_bytes` | per-file ceiling only, so a tree of N dirty paths held N MiB | aggregate ceiling; every declined path is named in a `preserve_bounded` trace event |
| `sssf.agent_pi.raw_output_journal` | grew with whatever the model emitted | aggregate 64 MiB ceiling preserved across reopens with one terminal truncation record; a truncated journal also fails the turn rather than passing as a complete record |
| `sssf.agent_pi.stderr_capture` | `process.stderr.read()` held the whole stream | concurrently drained bounded capture with explicit overflow status |
| `sssf.agent_pi.turn_wall_clock` | no deadline at all | 3600 s `ChildDeadline`; expiry is stated rather than surfacing as a plain nonzero exit |
| `sssf.quality.stdout_capture` / `stderr_capture` | `capture_output=True` held whatever a check produced | bounded captures read on the way in; the `[bounded]` note reaches both the log and the builder |
| `sssf.ci_gate.check_output_capture` | `communicate()` held the whole log | bounded capture; `output_truncated` / `output_bytes_seen` / `output_limit_bytes` land in the CI evidence |
| `sssf.evidence.artifact_read_bytes` | read an artifact of any size into memory | 512 MiB ceiling, REJECT rather than truncate, because a digest over a prefix would claim to identify an artifact it never finished reading |
| `sssf.evidence.artifact_path_depth` | unbounded component walk | 64-component ceiling, refused before the first `open` |
| `sssf.sandbox.lifecycle_record_store` / `destroy_authorization_store` | monotone collections with no ceiling | REJECT at 4096 |
| `sssf.reap.provider_key_page` | a comment reading `UNVERIFIED: whether GET /keys paginates` | an explicit refusal when the provider returns a list at or above the page ceiling, because a silently truncated key list looks exactly like a fleet with nothing to reap |
| `sssf.run.phase_error_text` | clipped at 1000 chars silently | clipped with a marker carrying the original length |

One further defect surfaced while proving a boundary rather than while reading
code: `AttemptBudget(True)` was accepted, because `bool` is an `int` in Python.
It is now refused, consistent with every other ceiling in the repository.

## What the re-audit added

Re-reading the owners that landed while this lineage was held found four
governed surfaces the earlier pass could not have seen, and one defect that only
exists in the combination of the two changes.

| Surface | Was | Now |
| --- | --- | --- |
| `sssf.sandbox.effect_authority_state_store` | the durable one-use effect-authority store recorded one entry per live effect, removed none, and re-read the whole file on every verify. Its in-memory sibling has always REJECTed at 4096; the store that actually gates live effects had no ceiling at all | REJECT at 4096, naming the ceiling and the reclaim procedure. Eviction is deliberately refused as a policy here: dropping a `completed` record silently restores a spent authorization's identity to never-seen, which is the exact state one-use authority exists to deny. An identity already recorded stays usable when the store is full, so a live effect is never orphaned behind a ceiling it did not hit |
| `sssf.planning.git_output_capture` | `capture_output=True` on every git read in the planning validator. This output is not bounded by the checked-out tree: it comes out of an object store the validator does not own | 8 MiB ceiling, REJECT rather than truncate. This validator turns those bytes into authority identities, and a prefix of a ref list is indistinguishable from a complete shorter one, so an over-ceiling read answers nothing and the caller reports could-not-observe |
| `sssf.planning.git_wall_clock` | no deadline at all on those same reads | 30 s, CANCEL and then REJECT |
| `sssf.windows_host.child_output_capture` | the host doctor bounded how long a child could run but never how much it could say inside that window | 8 MiB ceiling, TRUNCATE_WITH_EXPLICIT_STATUS, reusing the CI gate's existing bounded-output owner rather than growing a second one |

Timeout cleanup in the CI gate, planning Git reader, and Windows host child
wrapper owns a fresh process group and terminates that group before joining its
reader. A descendant that inherits the output pipe therefore cannot extend the
declared wall-clock ceiling after its immediate parent is stopped.

The defect: the host doctor's bounded capture and HD-09's could-not-observe
reason lines are individually correct and wrong together. HD-09 reads a child's
own reason lines out of its output; this increment moved the same output behind
a reader thread that has not finished draining when those lines were being read.
The merged result named a variable that did not exist yet, so every child
reporting the reserved could-not-observe exit code crashed the gate instead of
being reported. `tools/ci_gate.py` now names the reason after the reader joins,
and states in the same evidence row when a reason line did not survive the clip.
Two HD-09 controls cover it, and both were watched failing on the merged bytes
before the fix.

## Prove

| Check | Result |
| --- | --- |
| `python3 docs/validation/check_boundedness.py` | PASS — 53 surfaces, 15 boundary owners, 28 watched-red controls |
| `python3 docs/validation/check_ci_contract.py` | PASS — 12 offline checks enumerated |
| `python3 docs/validation/check_planning_foundation.py` | PASS — 20 tests, in 4.4 s against a 60 s budget, with the bounded git reads in place |
| `python3 docs/validation/check_adw_synchronization.py` | PASS |
| `python3 docs/validation/check_sandbox_source_contract.py` | PASS |
| `python3 -m pytest tests/ --ignore=tests/test_gate_outcomes.py` | PASS — 106 passed, 1 skipped, including the HD-09 and HD-10 boundary suites over the changed owners |
| `python3 docs/validation/check_executor_supervisor.py` | PASS |
| `python3 docs/validation/check_sandbox_provider.py` | PASS |
| `python3 docs/validation/check_evidence_manifest.py` | PASS — HD-08 recalibrated against the new tool bytes; the prior capture is retained |
| `python3 docs/validation/check_production_extension_path.py` | PASS |
| `python3 docs/validation/check_sbx0_inventory.py` | PASS |
| `python3 docs/validation/check_agent_bootstrap.py` | PASS |
| `python3 docs/validation/check_line_endings.py --require-worktree-lf` | PASS |
| `python3 docs/validation/check_obs_query.py` | COULD-NOT-OBSERVE on this host — `just` is not installed. The identical failure reproduces in a clean worktree at unmodified `8aadd504`, so it is an environmental gap rather than a BOUND-1 effect. CI pins `just` 1.58.0. |
| `just inkwell test` | COULD-NOT-OBSERVE on this host — `just`/`bun` absent for the same reason. CI pins `bun` 1.3.14. |
| `python3 -m pytest tests/test_gate_outcomes.py` | COULD-NOT-OBSERVE on this host — `pydantic` is not installed, so the module cannot be imported. Not a required-CI check on its own; the gate reaches it through the validators. |
| `python3 docs/validation/check_repository_ownership.py` | COULD-NOT-OBSERVE in this worktree — it reads a `git remote get-url upstream` this disposable worktree does not carry, and raises rather than reporting. The identical crash reproduces at unmodified `8aadd504`. It is not a registered required check. |

No could-not-observe is treated as a pass anywhere in this record. Each of the
four was reproduced at unmodified `8aadd504` in a separate clean worktree before
being called environmental, rather than assumed to be.

## Continuous proof obligations, as landed

- Required CI runs `boundedness-registry-validator` on every pull request and
  every push to `main`.
- Every increment declares a `boundedness_delta` (`docs/development/INCREMENT_PROTOCOL.md`, step 7).
- Dynamic owners expose effective limit, bytes seen, truncation, and overflow
  reason where practical; the registry records where.
- A complete re-audit is due before `SBX-8`, `DSH-3`, `DSH-5`, and `DSH-8`, and
  whenever a new scheduler, executor, durable store, cache, remote transport, or
  autonomous descendant class enters the architecture. Every re-audit updates
  this same registry rather than creating another truth store.

## What remains CNO or unmet

- Assignment-distinct semantic review that no material growth owner was omitted.
- Exact-head CI on the final landed bytes.
- `LandingAuthorization`, the global SSSF landing freeze, and the
  candidate-publication quarantine all still govern this branch.
- The `SBX-2` hold is unchanged; BOUND-1 does not release it.
- Windows-host observation of the changed owners; only provider-free,
  network-free, in-process controls were run here.

## Boundedness delta

```text
boundedness_delta:
  added: [
    sssf.supervisor.stdout_capture, sssf.supervisor.stderr_capture,
    sssf.supervisor.child_wall_clock, sssf.supervisor.attempt_budget,
    sssf.supervisor.descendant_custody_set, sssf.pi_adapter.stdout_bytes,
    sssf.pi_adapter.stderr_bytes, sssf.pi_adapter.event_bytes,
    sssf.pi_adapter.turn_wall_clock, sssf.agent_pi.raw_output_journal,
    sssf.agent_pi.stderr_capture, sssf.agent_pi.turn_wall_clock,
    sssf.agents.json_fix_attempts, sssf.agents.gate_correction_attempts,
    sssf.permissions.preserve_per_file_bytes,
    sssf.permissions.preserve_total_bytes,
    sssf.permissions.recovered_breach_allowance, sssf.run.phase_list,
    sssf.run.agent_map, sssf.run.phase_error_text,
    sssf.run.session_runtime_dir, sssf.quality.stdout_capture,
    sssf.quality.stderr_capture, sssf.quality.output_tail,
    sssf.quality.command_log_artifact, sssf.tracer.event_payload_bytes,
    sssf.tracer.process_command_text, sssf.tracer.durable_journal,
    sssf.changes.diff_lines, sssf.console.line_length,
    sssf.console.phase_results, sssf.sandbox.resource_bounds,
    sssf.sandbox.lifecycle_record_store,
    sssf.sandbox.destroy_authorization_store,
    sssf.ci_gate.check_timeout_seconds, sssf.ci_gate.check_output_capture,
    sssf.evidence.artifact_read_bytes, sssf.evidence.artifact_path_depth,
    sssf.obs_query.result_sets, sssf.windows_host.path_entry_set,
    sssf.windows_host.git_candidate_set, sssf.reap.provider_key_page,
    sssf.sandbox_mount.run_record_store,
    sssf.adw.build_review_revision_loops, sssf.adw.build_test_fix_loops,
    sssf.adw.plan_build_test_fix_loops,
    sssf.adw.plan_build_test_quality_fix_loops,
    sssf.adw.simple_sdlc_fix_loops, sssf.adw.simple_sdlc_revision_loops,
    sssf.sandbox.effect_authority_state_store,
    sssf.planning.git_output_capture, sssf.planning.git_wall_clock,
    sssf.windows_host.child_output_capture
  ]
  changed: []
  retired: []
```

This increment establishes the registry, so every surface it inventoried enters
as `added`. Later increments declare real deltas against it.
