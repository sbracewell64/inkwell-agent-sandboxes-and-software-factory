# SSSF Runtime

## ADWs

Each `adws/adw_*.py` file is a thin workflow script. Its `Phases:` docstring is the quick chain summary.

Low-level behavior belongs in `adws/adw_modules/`.

## Core modules

- `agents.py` — roster loading, required-agent validation, agent execution
- `agent_pi.py` / harness adapters — model/harness invocation; this is the path
  ADW phases actually run, and it forwards configured `harness_engineering`
  extensions to Pi
- `pi_json_adapter.py` — strict no-session Pi JSON/print contract; substrate for
  a later integration, not yet on the ADW execution path
- `subprocess_supervisor.py` — bounded provider-neutral native process ownership
- `data_types.py` — typed envelopes and the canonical gate outcome contract
- `gates.py` — claim verification with explicit evidence requirements
- `mutation_fact.py` — the one code-computed record of what the working tree
  actually did, and the bidirectional comparison against an envelope's claims
- `quality.py` — deterministic quality commands
- `permissions.py` — post-agent write-boundary enforcement, over the same fact
- `tracer.py` — SQLite trace
- `session.py` — ADW session lifecycle
- `runner.py` — phase execution
- `git_helper.py` — commit operations

## Phase model

A phase has:

- name,
- kind (`agent`, `code`, `engineer`, etc.),
- owner,
- description,
- optional retry budget,
- inputs/previous envelope,
- output contract,
- gates.

## Gate outcome semantics

`data_types.py` owns the one gate outcome model: `PASS`, `FAIL`, or
`COULD_NOT_OBSERVE` (CNO). It cannot be used as a Boolean. CNO always carries a
closed reason and source.

Every `GateReport` declares `nonempty_required`. A failed observed check is
`FAIL`; qualifying positive checks are `PASS`; zero required checks, zero
discovered gates, an exception while collecting evidence, or a legacy/untyped
return is CNO. Only explicit `PASS` advances an agent phase. The console and UI
render CNO amber, never green, and the trace stores outcome, reason, source,
checks, and the nonempty requirement.

Nonempty artifact gates keep their bounded meaning: they prove the declared
artifact observations they actually recorded, and nothing more.

## Mutation fact and claim reconciliation

`mutation_fact.py` computes ONE observation per gate attempt: per-path git blob
identity in HEAD and on disk, for every path the tree differs on plus every
untracked, non-ignored file. Content identity, never line counts — a line replaced
by another of the same shape moves the identity and left the old fingerprint
unchanged. Mutation kinds (`added`, `modified`, `deleted`) derive from that
identity, and a rename is a deletion and an addition carrying equal bytes, linked
as peers, with both paths still required.

`diff_matches_claims` reads that observation and compares it with
`envelope.changed_files` in both directions: a claimed path that did not move is a
FAIL, and a path that moved without being claimed is a FAIL. Claims normalize to
repo-relative POSIX form first, so a spelling difference is not a fabrication and
a path outside the repository root is refused rather than silently accepted.

`permissions.enforce` is handed the same observation object. Two snapshots of one
tree read at two moments are two sources of truth; there is one.

### The boundary, which every verdict states

The fact set observes tracked content identity against HEAD and untracked,
non-ignored files. It does NOT observe gitignored files, writes outside the
repository root, network effects, or process effects. `ObservationScope` carries
that universe on the report, the console prints it beside the verdict, and the
trace stores it in `gate_results.scope_json`.

Agreement therefore means agreement WITHIN that fact set and must never be read as
"nothing else happened". A candidate the observation could not read makes the
outcome COULD_NOT_OBSERVE (`INCOMPLETE_OBSERVED_UNIVERSE` / `MUTATION_FACT`), never
a clean negative; an observed discrepancy remains FAIL and is never masked by the
hole. Outside a git repository there is no fact, so the gate is CNO rather than a
pass.

What a contribution is measured against — repository, worktree, branch, base,
head, and the ambient `git add -A` — is not defined here and belongs to HD-05.

Legacy `gate_results.passed` is retained only as a compatibility projection
(`1` PASS, `0` FAIL, `NULL` CNO). Schema migration preserves an old explicit
negative as FAIL but downgrades old Boolean green to CNO because vacuous and
nonvacuous historical positives cannot be distinguished. Readers missing the
typed columns also project CNO rather than consulting the legacy Boolean.

## Correction semantics

Malformed typed output is corrected in the **same agent session** when possible.

The baseline builder proof demonstrated:

- first builder response: invalid `BuildOutput` JSON,
- SSSF re-prompted the same session,
- second response parsed and passed.

This is preferred to restarting because the correction keeps accumulated task context.

B4-002 lands the strict no-session execution substrate but does not wire it into
this path, so these semantics are unchanged. Adopting bounded no-session
correction attempts is a later, separately reviewed integration step.

## Acceptance

A phase succeeding at its job is not the same as the full run being accepted.

A test phase may execute successfully and report a failing suite.

Every ADW must end through the run finish path with an explicit accepted condition.

## Static synchronization

`docs/validation/check_adw_synchronization.py` is the authority for the installed, skill-template, and disposable generated ADW contract. It checks a nonempty surface inventory, statically resolves imported module attributes, requires concrete typed agent calls and exactly one `run.finish()` as the final top-level return from `main()` after a bounded fallthrough prefix, reconciles PEP 723 dependencies with imports, and matches prompt Report fields to output models. Its generated import smoke does not execute `main()` or call a provider.
