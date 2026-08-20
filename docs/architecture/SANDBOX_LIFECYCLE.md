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

- resolve the host checkout's public `origin` as `source_repo`,
- require a clean host tree when using the default current source,
- resolve an exact 40-character `source_sha` (host `HEAD` by default),
- clone that repository into the sandbox,
- checkout the exact source commit,
- create the run branch,
- gate actual guest HEAD against `source_sha`,
- persist `source_repo`, `source_sha`, and actual `commit_sha`,
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

Git integrity additionally proves:

- guest `origin` equals recorded `source_repo`,
- guest HEAD equals recorded `source_sha` / `commit_sha`,
- the guest working tree is clean.

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

## SBX-0/SBX-1 provider-neutral projection

The exact SBX-0 source-bound handoff is published once in
[`reference/SBX-0_SEMANTICS_INVENTORY.json`](../reference/SBX-0_SEMANTICS_INVENTORY.json)
and its publication record/validator. It binds the report generation and
content digest, preserves classifications and CNO, and assigns one owner per
fact; it does not become a lifecycle or acceptance store.

The provider-neutral contract, ownership boundary, lifecycle vocabulary, bounded
exports, reconciliation rules, and deterministic fake are owned once by
[`reference/SANDBOX_PROVIDER.md`](../reference/SANDBOX_PROVIDER.md) and
`adws/adw_modules/sandbox_provider.py`. This lifecycle document remains the
historical exe.dev ordering reference; it does not define a second provider
interface. SBX-1 activation/acceptance, Docker mechanics, and live provider
behavior remain outside this publication.
