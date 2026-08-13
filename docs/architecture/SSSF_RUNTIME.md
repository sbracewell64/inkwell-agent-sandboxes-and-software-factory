# SSSF Runtime

## ADWs

Each `adws/adw_*.py` file is a thin workflow script. Its `Phases:` docstring is the quick chain summary.

Low-level behavior belongs in `adws/adw_modules/`.

## Core modules

- `agents.py` — roster loading, required-agent validation, agent execution
- `agent_pi.py` / harness adapters — model/harness invocation
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

Malformed typed output is corrected in the **same agent session** when possible.

The baseline builder proof demonstrated:

- first builder response: invalid `BuildOutput` JSON,
- SSSF re-prompted the same session,
- second response parsed and passed.

This is preferred to restarting because the correction keeps accumulated task context.

## Acceptance

A phase succeeding at its job is not the same as the full run being accepted.

A test phase may execute successfully and report a failing suite.

Every ADW must end through the run finish path with an explicit accepted condition.
