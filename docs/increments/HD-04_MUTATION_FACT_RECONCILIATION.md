# HD-04 — One mutation fact, reconciled bidirectionally against the claims

**Status:** IMPLEMENTED — deterministic controls pass
**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`
**Boundary:** ADW mutation observation, claim gate, permission enforcement, gate
trace/console rendering. Contribution Git context (HD-05), the executor contract,
Pi child custody, and the evidence manifest are untouched.

## Intent

Compute ONE normalized, code-computed mutation fact covering pre/post Git status,
path set, content identity, and permission scope, and compare it with the
envelope's claimed change set in BOTH directions. Have the permission check and
the claim gate consume that same fact rather than two independent snapshots. State
the fact set's boundary in the verdict so an agreeing result cannot be read as an
unqualified clean.

## Reproduced defect

At the starting SHA, `gates.diff_matches_claims` looped `envelope.changed_files`
and checked `Path(f).exists()`. That is one direction, and it proves existence
rather than mutation. On the same repository state it accepted:

- a claim on an existing file the phase never touched (`untouched.py` exists →
  green);
- a claim set that omitted a file the phase really changed (only the claimed
  paths were ever consulted);
- an extra path the phase introduced and never named;

and it wrongly refused a truthful deletion claim, because a deleted path does not
exist. HD-03 had already refused the empty `changed_files=[]` declaration as
COULD_NOT_OBSERVE, so that one case was closed; every nonempty-but-wrong case was
not.

Separately, `permissions.snapshot` fingerprinted tracked paths with `git diff HEAD
--numstat` line counts. Replacing a line with another of the same shape leaves the
fingerprint byte-identical, so a content change on an already-dirty file was
invisible. And `permissions.enforce` took its own snapshot after all gate retries,
so the claim gate and the permission check observed the tree at two different
moments — two sources of truth for one question.

Both defect surfaces are preserved as calibration cases inside
`docs/validation/check_mutation_fact.py` (`path_existence_proxy`,
`numstat_fingerprint`) and are asserted to still behave as they used to, so no
control below can be vacuously red.

## Design

`adws/adw_modules/mutation_fact.py` is new, dependency-free, and owns the fact.

- `observe(repo_root) -> TreeFact` records, per candidate path, the blob identity
  in HEAD and the blob identity on disk, plus whether the path is tracked.
  Candidates are `git diff --name-only --no-renames <base>` united with `git
  ls-files --others --exclude-standard`. A repository with no commit measures
  against the empty tree. Working-tree identity comes from `git hash-object`, so
  the repository's own attributes decide it and the value is the one git would
  store.
- `mutations(before, after) -> tuple[PathMutation, ...]` derives `added`,
  `modified`, `deleted` from content identity alone. A path absent from a fact
  matched the base at that instant, which is what makes a reversion a mutation.
- Renames are derived, not detected: a deletion and an addition whose content
  identity is EQUAL are linked as peers. Git's similarity heuristic and the
  `diff.renames` setting cannot move the answer, and both paths remain mutations
  in their own right, so claiming only a rename's destination still conceals its
  source. An ambiguous pairing walks the path-sorted list, so it is stable across
  repeated observation.
- `reconcile(observation, claims)` compares the claim set with the fact in both
  directions and returns `agreed`, `unclaimed` (moved, never claimed), `unmatched`
  (claimed, never moved), and `unobservable`. Claims are normalized to
  repo-relative POSIX form first, so `./pkg/mod.py`, `pkg\mod.py`, and an absolute
  path are one claim, while a path outside the repository root is refused as
  unplaceable rather than silently treated as a fabrication.

`gates.diff_matches_claims` now reads that fact with
`mutation_fact.observation_of(run)` and never computes one of its own. Each agreed
path records the observed kind and the content identities either side of it; each
discrepancy is a failed check naming the direction it failed in.

`agents.execute` publishes exactly one `MutationObservation` per gate attempt,
computed after that attempt's last send, and hands the same object to
`permissions.enforce(..., after=...)`. `permissions.snapshot` is now a call into
`mutation_fact.observe`, and `changed_paths` is content identity rather than line
counts. One fact, two consumers.

### The observation boundary

The fact set is bounded and every verdict states the bound. `ObservationScope`
(new, in `data_types.py`) travels on the `GateReport`, is rendered by the console
next to the verdict, and is persisted in `gate_results.scope_json`. It carries:

- `observed` — tracked content identity against HEAD; untracked, non-ignored
  working-tree files; renames derived from content identity;
- `out_of_scope` — gitignored files, writes outside the repository root, network
  effects, process effects;
- `unobservable` — any candidate this observation could not read.

A boundary statement is deliberately NOT a check, so it can never turn a report
with no real observations into a PASS. Under the standing law recorded at
`data/captain-rulings-2026-08-17-discovery-is-not-identity.md`, zero findings is
cleanliness only within a stated universe: a nonempty `unobservable` makes the
outcome COULD_NOT_OBSERVE (`INCOMPLETE_OBSERVED_UNIVERSE` / `MUTATION_FACT`)
rather than an agreement, while an observed discrepancy remains FAIL and is never
masked by the hole.

This increment does not attempt to close the out-of-scope classes. Naming them
honestly is the deliverable.

### Compatibility

`GateCNOReason` gained `INCOMPLETE_OBSERVED_UNIVERSE` and `GateCNOSource` gained
`MUTATION_FACT`. A `gate_results` table written by an older SSSF carries that
release's CHECK constraint and would refuse the new closed values at insert time,
so `Tracer._readmit_closed_gate_values` rebuilds the table once when its stored
CHECK predates a current member. The rebuild only ever widens the constraint, runs
after outcome normalization, preserves rows and ids, and restores the connection's
prior foreign-key setting. The CHECK and the migration placeholder counts are now
generated from the enums instead of hand-listed.

Installed modules and factory templates carry the same contract.

## Behavior change to note

`diff_matches_claims` in a directory that is not a git repository is now
COULD_NOT_OBSERVE rather than a pass. Claims cannot be reconciled against a
repository that does not exist, and under HD-03 an unobserved gate does not
advance a phase. ADWs that only read or plan are unaffected; an ADW whose builder
must prove what it changed now requires a repository, which is what proving that
claim actually costs.

## Non-goals

No contribution Git context (required repo/worktree/branch/base/head/paths, and
removing the ambient `git add -A`) — that is HD-05. No change to the executor
contract, Pi child custody, or the evidence manifest. No attempt to observe
ignored files, out-of-repository writes, network effects, or process effects.

## Deterministic acceptance

`docs/validation/check_mutation_fact.py` is registered as the CI check
`mutation-fact-reconciliation-validator` and runs without third-party packages. It
executes 15 controls, each asserting normalized path and content identity rather
than counts, message text, or exit codes:

- an honest exact set agrees, covering modified/added/deleted, so nothing below is
  vacuously red;
- an unchanged existing claimed path is refused;
- an omitted actual changed path is caught;
- an extra actual path is caught;
- an empty claim over a real change is caught;
- a content change on an already-dirty file is detected while the line-count
  fingerprint is asserted to be identical either side of it;
- a rename resolves to both paths, linked by content identity, identically under
  `diff.renames=true` and `false`;
- an ambiguous rename pairing is stable across repeated observation and loses no
  required claim;
- a deletion resolves, a truthful deletion claim agrees, and an unclaimed deletion
  is caught;
- untracked resolves as an addition while a gitignored path stays outside the fact;
- the boundary is stated and real — an ignored write genuinely happened and is
  genuinely absent from the fact;
- an unreadable candidate makes the universe incomplete, never a clean negative;
- claim spellings normalize while an out-of-repository claim is refused;
- no repository is a hole, not an agreement;
- the claim gate and the permission check are wired to one observation.

`tests/test_mutation_fact.py` proves the typed layer: PASS/FAIL/CNO mapping per
direction, the scope on both green and red verdicts, an observed defect never
masked by an observation hole, the gitignored write staying outside a green
verdict, the same-object identity shared by the gate and the permission check,
console output that cannot read as an unqualified clean, `scope_json` persistence,
and both older database vintages readmitting the current closed values.

Validation commands:

```text
python docs/validation/check_mutation_fact.py
PYTHONPATH=adws pytest -q tests/
python tools/ci_gate.py run --evidence ci-evidence.json
```

### Observed evidence

Watched-red first, then green. Six disposable mutations of `mutation_fact.py` were
each observed reddening exactly the controls that own them, and the file was
restored byte-identically afterwards:

| Disposable mutation | Controls observed red |
|---|---|
| `unclaimed` dropped (claims-only direction) | omitted, extra, empty-claim, already-dirty, rename, deletion, untracked |
| existence-only claim matching | unchanged-claimed, untracked |
| content identity replaced by a line-count proxy | already-dirty, rename |
| rename linkage removed | rename |
| observation holes dropped | incomplete-universe, no-repository |
| boundary no longer stated | boundary |

Five further disposable mutations reddened the typed layer: a gate that computes
its own fact, an incomplete universe rendered as PASS, a console that drops the
boundary, the CHECK rebuild removed, and `enforce` taking a second snapshot (which
also reddened `control_one_fact_two_consumers`).

Unmodified results: 15/15 controls PASS; 36 tests pass under
`PYTHONPATH=adws pytest -q tests/` (19 pre-existing HD-03 controls plus 17 new).
`check_adw_synchronization.py`, `check_ci_contract.py`, strict B3-002 line
endings, `git diff --check`, and Ruff `F,E9` over every changed file passed; the
four Ruff findings that remain are pre-existing and in files this increment did
not touch.

The offline gate went from 6 observed-good at the starting SHA to 7 with this
increment's check added. Two results are host-dependent and are recorded as
observed-bad and could-not-observe, not as passes: `check_obs_query.py` and
`just inkwell test` both require `just`, which is absent on this worktree's host
and present on the CI runners. Neither moved between the baseline and this change.

### Named gaps, not passes

The trace UI (`.claude/skills/sssf/apps/visualizer/server/db.ts`) selects gate
columns behind `hasColumn` guards and does not read `scope_json`, so a verdict
rendered there still shows no boundary. That is forward-compatible rather than
broken, and it is left for a later increment on purpose: the visualizer is a Bun
project, Bun is absent on this worktree's host, and its typecheck/lint/build could
not be observed here. Shipping unverified TypeScript to close a rendering gap
would trade a stated gap for an unproven claim.

## Failure modes and rollback

A discrepancy in either direction is a gate FAIL and returns to the same agent
session as a correction. An unreadable candidate is CNO and also does not advance.
A repository that cannot be observed at all is CNO. The permission check falls back
to observing its own fact only when a phase published none.

Rollback is one increment commit. Databases written with the widened CHECK remain
readable by an older SSSF for every value that release knew; a row carrying
`INCOMPLETE_OBSERVED_UNIVERSE` or `MUTATION_FACT` would be unknown to it, and
rollback restores the one-directional existence check along with its defect.
