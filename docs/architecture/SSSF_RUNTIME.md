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
- `quality.py` — deterministic quality commands
- `permissions.py` — post-agent write-boundary enforcement
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

Existing genuine controls keep their bounded meaning: nonempty artifact gates
prove the declared artifact observations they actually recorded, and permission
enforcement remains a separate post-agent boundary. Before an agent runs, that
boundary preserves up to 1 MiB of each already-dirty file. It restores those
bytes when necessary and permits at most three fully recovered out-of-scope
writes to continue; an unrecovered or larger breach fails the phase. Neither
control is presented as proof that an envelope listed every real repository
mutation; Git/content claim reconciliation belongs to a later increment.

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

That internal-contract validator checks each surface independently and does not
compare installed and template CONTENT; it is preserved unchanged and its verdict
is not broadened by the parity work below. See the claim-boundary section of
`docs/increments/HD-02_ADW_SYNCHRONIZATION.md`.

## Mapped-surface parity

The surfaces are a mapping, not a mirror: `install.py` stamps template paths to
different live paths, so a relative-path or subtree comparison is not a parity
model. `docs/validation/mapped_surface_contract.json` transcribes that mapping
from install.py's `stamp()` calls and assigns every governed path one relation —
`EXACT_MIRROR`, `CONTRACT_ONLY`, `TEMPLATE_SCAFFOLD`, `USER_OWNED`, `LIVE_ONLY` —
with owner, rationale and evidence wherever divergence is intentional.

`docs/validation/check_mapped_surface_parity.py` enforces it: mapped content
identity for `EXACT_MIRROR`, named-property enforcement for relations that permit
body divergence, coupled groups that must stamp together, and CNO for a vacuous,
unreviewable, stale, or unclaimed declaration. Undeclared divergence is never
silently accepted. It emits `matched / intentional-divergence / drift /
unresolved` as structured state bound to the sha256 of the verifier and contract
bytes, and re-runs its watched-red calibration on every invocation, so it cannot
report PASS without having just demonstrated it still fails.

`docs/validation/check_stamped_substrate.py` closes the remaining gap by running
the real installer into a disposable directory: it asserts the reconciled
substrate arrives and that intentional scaffold/user-owned divergence survives.
Decision record: `docs/decisions/ADR-0004-MAPPED-SURFACE-PARITY.md`.
