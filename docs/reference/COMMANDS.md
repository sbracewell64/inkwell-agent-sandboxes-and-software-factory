# Command Reference

Every command below carries its **lane**. The lane is not decoration: it states what a record of that
command's work may and may not claim.

- `adw` — a bounded AI Developer Workflow, with an ADW ID, typed envelopes, gates, usage, and an
  explicit outcome.
- `lifecycle` — a deterministic, code-owned command. No agent reasoning runs in it.
- `steering` — an ask handed straight to an interactive agent, **outside the ADW trace**.

Only the ADW lane, and only when the workflow it runs executes a deterministic test or quality block,
may claim SSSF workflow success. A `lifecycle` or `steering` command cannot be cited under the trace
and acceptance guarantees of the ADW lane.

The full contracts — allowed purpose, and the claims that cannot be made — are in
[`FRONT_DOOR_LANES.md`](FRONT_DOOR_LANES.md). The machine-readable source is
[`front_door_taxonomy.json`](front_door_taxonomy.json), enforced by
`docs/validation/check_front_door_lanes.py`.

## Application

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `just inkwell run` | lifecycle | `[PORT]` | Boot the app. |
| `just inkwell dev` | lifecycle | `[PORT]` | Boot with reload-on-save. |
| `just inkwell test` | lifecycle | — | Deterministic suite. Green here is not SSSF workflow success. |

## Host validation

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `python docs/validation/check_line_endings.py` | lifecycle | `--require-worktree-lf` | The authoritative strict LF invocation. |

The Windows bootstrap and host doctor invoke that same validator. Validation is read-only; explicit
remediation is documented in `docs/operations/INSTALL_WINDOWS.md`.

## Deterministic CI

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `python tools/ci_gate.py run` | lifecycle | `--evidence ci-evidence.json` | Runs the enumerated offline checks in `ci/checks.json`. |

This repository-owned gate succeeds only after at least one check executes and every result is
`observed-good`; its JSON evidence retains `observed-bad` and `could-not-observe` rather than treating
either as green.

## Factory

Every ADW recipe executes a workflow inside the appropriate working directory and config. Arguments
pass straight through: `"<prompt>" [--adw-id X] [--config Y]`.

| Command | Lane | Deterministic acceptance | May claim workflow success |
| --- | --- | --- | --- |
| `just adw prompt` | adw | no | no |
| `just adw ask` | adw | no | no |
| `just adw scout` | adw | no | no |
| `just adw plan` | adw | no | no |
| `just adw build` | adw | no | no |
| `just adw plan-build` | adw | no | no |
| `just adw build-test` | adw | yes | yes |
| `just adw build-review` | adw | no | no |
| `just adw quality` | adw | yes | yes |
| `just adw document` | adw | no | no |
| `just adw sdlc` | adw | yes | yes |
| `just adw plan-build-test-quality` | adw | yes | yes |
| `just adw simple-sdlc` | adw | yes | yes |

An ADW-lane run without deterministic acceptance is a **traced** run, not an accepted one. Read the
`pi-child` exception in [`FRONT_DOOR_LANES.md`](FRONT_DOOR_LANES.md) before claiming an ADW record
covers what the coding agent's own child processes did.

Validate installed, template, and disposable generated ADW contracts without a provider call:

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `uv run docs/validation/check_adw_synchronization.py` | lifecycle | — | Offline contract validation. |

## Local orchestrators — steering, not ADW

These hand your ask straight to an interactive agent. **No ADW ID, typed envelope, permission fact,
gate, usage record, or `run.finish()` exists for anything they do**, including source they edit or
commit.

| Command | Lane | Exception | Notes |
| --- | --- | --- | --- |
| `just local cc` | steering | `direct-claude-steering` | Claude Code, with `--dangerously-skip-permissions`. |
| `just local pi` | steering | `direct-pi-steering` | Pi, same posture. |
| `just local ipi` | steering | `direct-pi-steering` | Unix-only shell function. |

## Sandbox

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `just sbx mount` | lifecycle | `<run-id> [flags]` | Chains create, fill, setup, observe. |
| `just sbx lifecycle create` | lifecycle | `<run-id> [flags]` | Phase 1. |
| `just sbx lifecycle fill` | lifecycle | `<run-id> [sha]` | Phase 2. |
| `just sbx lifecycle setup` | lifecycle | `<run-id> [config]` | Phase 3. |
| `just sbx lifecycle execute` | lifecycle | `<run-id> "<prompt>" [config] [adw] [extra]` | Phase 4. Returns a **pid, not a result**. |
| `just sbx lifecycle observe` | lifecycle | `<run-id>` | Phase 5. |
| `just sbx lifecycle teardown` | lifecycle | `<run-id> [flags]` | Phase 6. Always an explicit decision. |

`just sbx lifecycle execute` launches an ADW inside the guest. The host holds only that pid; the ADW's
own trace lives on the guest and has to be read there. A successful `execute` is not a successful
workflow.

## Sandbox management

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `just sbx manage doctor` | lifecycle | — | Host prerequisites. |
| `just sbx manage list` | lifecycle | — | Fleet and run records. |
| `just sbx manage harvest` | lifecycle | `<run-id>` | Pull commits back as a bundle. |
| `just sbx manage reap` | lifecycle | `[flags]` | Revoke provisioned keys. |

## Sandbox inspection and steering

| Command | Lane | Exception | Notes |
| --- | --- | --- | --- |
| `just sbx run cmd` | lifecycle | — | `<run-id> "<command>"`. Synchronous escape hatch; prints output. |
| `just sbx run agent` | steering | `direct-claude-steering` | `<run-id> "<delegation>"`. Claude Code inside the box, permissions skipped. |
| `just sbx orch cc` | steering | `direct-claude-steering`, `host-orchestrator` | Host-side orchestrator, permissions skipped. |
| `just sbx orch pi` | steering | `direct-pi-steering`, `host-orchestrator` | Host-side orchestrator. |

`just sbx run agent` is the smallest counterfactual for this whole distinction: it binds a lifecycle
run ID and a Claude session UUID through a host sentinel file, it can edit and commit, and it emits no
ADW ID, typed envelope, permission fact, gate, usage record, or `run.finish()` for that turn.

## Observability

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `just obs rosters` | lifecycle | — | Which rosters exist and who is in them. |
| `just obs sessions` | lifecycle | — | Recent sessions. |
| `just obs phases` | lifecycle | `<adw-id>` | One run's phases. |
| `just obs tail` | lifecycle | `<adw-id>` | Live event tail. |
| `just obs procs` | lifecycle | `<adw-id>` | Processes the trace believes are alive. |
| `just obs kill` | lifecycle | `<adw-id>` | Stop a stuck run's recorded processes. |
| `just obs ui` | lifecycle | — | Boot the observability UI. |

`just obs procs` lists the Pi parent of each agent turn and nothing beneath it. Processes that a Pi
turn itself spawned are not recorded.

## Offline evidence manifest core

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `python3 tools/evidence_manifest.py` | lifecycle | `schema` \| `validate --help` | Schema, serializer, validator. |
| `python3 docs/validation/check_evidence_manifest.py` | lifecycle | — | Positive and watched-red controls. |

Manifest v1 validation is offline evidence checking only. It does not authorize runtime acceptance;
HD-09 owns that integration.

## Front-door lane contracts

| Command | Lane | Arguments | Notes |
| --- | --- | --- | --- |
| `python3 docs/validation/check_front_door_lanes.py` | lifecycle | — | Requires every front door to carry a lane from the taxonomy. |

## Identity warning

`run-id` and `adw-id` are different.

Never pass an ADW ID where a sandbox run ID is required.
