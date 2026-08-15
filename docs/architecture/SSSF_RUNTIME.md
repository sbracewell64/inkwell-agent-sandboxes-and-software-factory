# SSSF Runtime

## ADWs

Each `adws/adw_*.py` file is a thin workflow script. Its `Phases:` docstring is the quick chain summary.

Low-level behavior belongs in `adws/adw_modules/`.

## Core modules

- `agents.py` — roster loading, required-agent validation, agent execution
- `agent_pi.py` / harness adapters — typed harness invocation
- `pi_json_adapter.py` — strict no-session Pi JSON/print contract
- `subprocess_supervisor.py` — bounded provider-neutral native process ownership
- `data_types.py` — typed envelopes
- `gates.py` — claim verification
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

## Correction semantics

The frozen baseline builder proof used same-session correction: its first
`BuildOutput` was invalid and its second response parsed and passed. B4-002
changes current execution semantics deliberately. Malformed output and gate
violations now launch separate strict no-session attempts, all charged to one
explicit total native-attempt budget. Typed envelopes and correction prompts
carry only the context SSSF chooses; no ambient Pi session is resumed.

This tradeoff removes an unbounded/ambient sequencing authority from Pi. The
historical baseline proof remains historical evidence rather than a claim
about the current adapter.

## Acceptance

A phase succeeding at its job is not the same as the full run being accepted.

A test phase may execute successfully and report a failing suite.

Every ADW must end through the run finish path with an explicit accepted condition.
