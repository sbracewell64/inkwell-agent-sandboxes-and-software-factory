# System Overview

SSSF here is three nested systems.

## Tier 1 — Inkwell

A deliberately small application used as a payload for factory runs.

- server: Bun + `bun:sqlite`
- public app port: 4501
- deterministic test suite: `apps/inkwell/server.test.ts`

## Tier 2 — Super Simple Software Factory

Deterministic Python ADWs own the workflow graph. Agents are bounded workers inside phases.

Core areas:

- `adws/adw_*.py` — thin workflow definitions
- `adws/adw_modules/` — execution, gates, envelopes, permissions, quality, tracing, Git
- `adws/adw_sssf_config/` — agent rosters
- `adws/adw_data/` — runtime sessions and SQLite trace

## Tier 3 — Sandbox lifecycle

The host creates and manages an isolated execution environment.

Current provider: exe.dev.

Lifecycle:

`create -> fill -> setup -> execute -> observe -> teardown`

The sandbox contains the code and coding agents. Long-lived orchestration credentials stay on the host.

## Command authority

- `just inkwell ...` — application
- `just adw ...` — factory workflows
- `just sbx ...` — sandbox lifecycle and host operations
- `just obs ...` — trace readback
- `just local ...` — local orchestrator launch

## Two work-entry paths

### Direct (`lifecycle` lane)

`just sbx lifecycle execute`

The host starts the ADW deterministically. Lowest orchestration overhead.

### Agent-mediated (`steering` lane)

`just sbx run agent`

An in-sandbox orchestrator receives a delegation and decides which factory action to launch.

The delegation is intentionally outside the ADW trace. Its lifecycle and session identities cannot
be cited as ADW acceptance or SSSF workflow success; see
[`FRONT_DOOR_LANES.md`](../reference/FRONT_DOOR_LANES.md).

## State identities

Do not confuse:

- `run_id` — sandbox/lifecycle identity
- `adw_id` — one factory workflow run inside a sandbox
- agent session ID — one model/harness session inside an ADW phase

A single sandbox can contain multiple ADW runs.
