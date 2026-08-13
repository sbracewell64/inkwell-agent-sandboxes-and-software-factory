# Sandbox Lifecycle

Current lifecycle authority is under `just/sandbox/lifecycle/`.

## Phase 1 — create

Order is deliberately:

`run record -> VM -> runtime key`

Why:

- the run record exists before resources can be orphaned,
- a failed VM before key mint does not leave an invisible spend-capable key,
- failure does not auto-destroy evidence.

## Phase 2 — fill

- clone the public repo into the sandbox,
- create the run branch,
- record the base SHA,
- inject the disposable runtime OpenRouter key,
- never inject the host provisioning key.

## Phase 3 — setup

Guest provisioning:

- Bun
- just
- model registry
- app dependencies
- visualizer build
- trace DB initialization
- uv cache warming
- health gate

## Phase 4 — execute

Starts an ADW inside the box, normally detached, and records a PID.

## Phase 5 — observe

Starts:

- Inkwell on 4501
- observability UI on 4600

The app may be public; the factory-floor UI remains owner-gated.

## Phase 6 — teardown

Order matters:

`spend -> artifacts -> harvest -> revoke key -> destroy VM -> close record -> gate`

The irreversible action is VM destruction, so anything that reads from the VM happens first.

## Shared durable lifecycle state

`sandbox_mount/host/run_record.py` is the shared state handle across otherwise separate phase processes.

Never replace this with implicit shell-session state.

## Local Windows compatibility notes

See `operations/INSTALL_WINDOWS.md`.
