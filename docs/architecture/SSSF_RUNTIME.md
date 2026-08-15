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
enforcement remains a separate post-agent boundary. Neither is presented as
proof that an envelope listed every real repository mutation; Git/content claim
reconciliation belongs to a later increment.

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
