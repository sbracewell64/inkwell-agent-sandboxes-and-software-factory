# Front Door Lanes and Exception Contracts

Every front door of this repository belongs to exactly one lane, and every lane and exception states two things: what it is allowed to be used for, and the claims that cannot be made from it.

The second half is the point. A taxonomy that records only what a lane IS leaves the gap that produced this defect: direct steering changes source or decides progression, and an operator later cites normal SSSF trace and acceptance guarantees that never wrapped that work. The harm is a claim, not a crash, so the limits are written here, beside the front doors, where a reader meets them.

Steering is **intentionally** a separate orchestration and steering lane. Nothing here asks for it to be removed, discouraged, or reimplemented as an ADW. It is labelled so that what it is cannot be mistaken for what it is not.

`docs/reference/front_door_taxonomy.json` is the machine-readable source of these labels.
`docs/validation/check_front_door_lanes.py` enforces them; see [Enforcement](#enforcement).

## The acceptance rule

Only the ADW lane, and only when the workflow it ran executed a deterministic test or quality block, may claim SSSF workflow success. Every other lane, and every exception below, is barred from that claim.

## Lanes

### `adw`

**Allowed purpose.** Run a bounded AI Developer Workflow. The workflow opens a session with an ADW ID, records typed phase envelopes, runs code-owned gates, accounts tokens and cost per agent turn, registers the live coding-agent process, and ends at an explicit run.finish() outcome.

**Cannot claim.**

- An ADW record cannot claim deterministic acceptance of the software unless the workflow it ran executed a deterministic test or quality block. A run that produced only a traced envelope is a traced run, not an accepted one.
- An ADW record cannot claim provenance over work it did not perform. Steering turns taken before, during, or after the run leave nothing in its trace, so its ADW ID does not vouch for them.
- An ADW record cannot claim that a commit on the branch is its own output merely because the two are adjacent in history.

**May claim ADW acceptance:** yes
**May claim SSSF workflow success:** yes

The ADW lane's entitlement is a ceiling, not a grant. An individual ADW front door may claim SSSF workflow success only when the workflow it runs executes a deterministic test or quality block; the table below records that per front door.

### `lifecycle`

**Allowed purpose.** Run a deterministic, code-owned command: boot or test the application, drive a sandbox lifecycle phase, manage or inspect the fleet, read the trace, run an offline validator, or list the command surface. No agent reasoning runs in this lane.

**Cannot claim.**

- A lifecycle command cannot claim ADW acceptance. It opens no ADW session, writes no typed envelope, runs no gate, and calls no `run.finish()`.
- A lifecycle command cannot claim SSSF workflow success. A zero exit says the command did what it was asked; it says nothing about whether any workflow was accepted.
- A lifecycle command that launches a workflow elsewhere cannot claim that workflow's outcome. It holds a process identifier, not a result, and the workflow's own trace is the only record of what happened.

**May claim ADW acceptance:** **no**
**May claim SSSF workflow success:** **no**

### `steering`

**Allowed purpose.** Hand an ask straight to an interactive agent that orchestrates, investigates, or steers. This is deliberately a separate orchestration and steering lane, not a degraded ADW. It is how an engineer drives the factory rather than how the factory does its work, and it must not be removed, discouraged, or reimplemented as an ADW.

**Cannot claim.**

- A steering turn cannot claim an ADW ID, a typed phase envelope, a gate outcome, a permission fact, a usage or cost record, or a `run.finish()` outcome, because none of those are written for it.
- A steering turn cannot claim ADW acceptance for source it edited or committed, however ordinary the resulting change looks in the diff.
- A steering turn cannot claim SSSF workflow success, and a later reader cannot infer one from the commit it produced or from the terminal output it printed.
- A steering turn cannot be cited under the trace and acceptance guarantees of the ADW lane. Those guarantees never wrapped its work, and citing them over it is the exact defect this taxonomy exists to prevent.

**May claim ADW acceptance:** **no**
**May claim SSSF workflow success:** **no**

## Exceptions

An exception is narrow: it names a bounded set of front doors, states what that lane is deliberately for, records what it genuinely preserves, and then states what it may not be cited for. `pi-child` narrows the ADW lane from inside; the others sit outside the ADW trace entirely.

### `direct-claude-steering` — lane `steering`

**Allowed purpose.** Hand a prompt straight to Claude Code, outside the ADW trace, to orchestrate the factory, investigate a repository, or steer an agent already running inside a mounted sandbox. Retained deliberately.

**Preserved deliberately, and not to be removed.**

- The Claude session UUID and, for `just sbx run agent`, the lifecycle run ID are retained and rebound on every later turn.
- Terminal output is synchronous and visible to the operator as the turn happens.

**Cannot claim.**

- A direct Claude steering turn cannot claim bounded permissions. `just local cc`, `just sbx orch cc`, and `just sbx run agent` all pass `--dangerously-skip-permissions`.
- A direct Claude steering turn cannot claim an ADW ID, a typed envelope, a gate outcome, a usage or cost record, or a `run.finish()` outcome. `just sbx run agent` binds a lifecycle run ID and a Claude session UUID through a host sentinel file and emits none of the rest.
- A direct Claude steering turn cannot claim SSSF workflow success for source it edited or committed. The smallest counterfactual is `just sbx run agent`: it can edit and commit, and no ADW ID, typed envelope, permission fact, gate, usage record, or `run.finish()` exists for that turn.
- A direct Claude steering turn cannot claim that Claude ran as an ADW coding agent. `adws/adw_modules/agent_cc.py` raises NotImplementedError for `coding_agent claude_code` in v1, so Claude work in this repository is steering-lane work by construction.

**May claim ADW acceptance:** **no**
**May claim SSSF workflow success:** **no**

**Front doors under this exception:** `just local cc`, `just sbx orch cc`, `just sbx run agent`.

### `direct-pi-steering` — lane `steering`

**Allowed purpose.** Boot Pi as an interactive orchestrator against a skill file, outside the ADW trace, to drive the factory or the sandbox phases. Retained deliberately, on the same footing as the Claude steering front doors.

**Preserved deliberately, and not to be removed.**

- Terminal output is synchronous and visible to the operator as the turn happens.
- Pi keeps its own session state on disk, independent of the ADW session store.

**Cannot claim.**

- A direct Pi steering turn cannot claim an ADW ID, a typed envelope, a gate outcome, a usage or cost record, or a `run.finish()` outcome. Nothing in `adws/adw_modules/tracer.py` is written for it.
- A direct Pi steering turn cannot claim SSSF workflow success for source it edited or committed.
- A direct Pi steering turn cannot claim the process accounting the ADW lane gives a Pi turn. No processes row is written, so just obs procs cannot find it and just obs kill cannot stop it.

**May claim ADW acceptance:** **no**
**May claim SSSF workflow success:** **no**

**Front doors under this exception:** `just local ipi`, `just local pi`, `just sbx orch pi`.

### `host-orchestrator` — lane `steering`

**Allowed purpose.** Boot an orchestrator agent on the HOST, where the exe.dev account and OPENROUTER_PROVISIONING_KEY live, to drive the sandbox phases: mount, execute, observe, harvest, and tear down. Retained deliberately: these credentials never reach a sandbox, so this lane cannot be moved into one.

**Preserved deliberately, and not to be removed.**

- The host holds the credentials the sandbox lane needs and never forwards them into a guest.
- Terminal output is synchronous and visible to the operator as the turn happens.

**Cannot claim.**

- A host-orchestrator turn cannot claim to be sandboxed. It runs on the host with host credentials, and the isolation the sandbox lane provides does not apply to anything it changes there.
- A host-orchestrator turn cannot claim an ADW ID, a phase, a gate, or acceptance for anything it decided or changed on the host.
- A host-orchestrator turn cannot claim SSSF workflow success on behalf of a sandbox it mounted. The guest run's own trace is the only record of that, and it has to be read on the guest.

**May claim ADW acceptance:** **no**
**May claim SSSF workflow success:** **no**

**Front doors under this exception:** `just sbx orch cc`, `just sbx orch pi`.

### `pi-child` — lane `adw`

**Allowed purpose.** Run the Pi coding agent as the child process of an ADW phase. This exception narrows the ADW lane rather than sitting outside it: the parent Pi turn is traced comparatively richly, with a processes row, streamed events, the phase envelope, its gates, and per-turn token and cost usage.

**Preserved deliberately, and not to be removed.**

- The parent Pi turn is registered in the processes table as kind agent with its pid and command, so just obs procs and just obs kill can reach it.
- Streamed Pi events, the phase envelope, its gate outcomes, and per-turn token and cost usage are recorded against the ADW ID.

**Cannot claim.**

- An ADW record cannot claim to have traced anything the Pi turn itself spawned. `adws/adw_modules/agent_pi.py` reports exactly one pid to `on_spawn` and `on_exit`, so just obs procs lists the Pi parent and nothing beneath it.
- An ADW record cannot claim per-descendant tool, model, permission, or usage provenance. Usage is accounted per Pi turn, not per process that turn started.
- An ADW record cannot claim that bounded subprocess supervision covered the run. The production launch path is `agent_pi.run`, and the supervised adapter in `adws/adw_modules/pi_json_adapter.py` is not imported by `adws/adw_modules/agents.py`.

**May claim ADW acceptance:** yes
**May claim SSSF workflow success:** yes

Those two entitlements are the ADW lane's, inherited unchanged and still capped by the front door's own deterministic acceptance. What this exception removes is narrower and stated above: the record covers the Pi turn, not what the Pi turn started.

**Front doors under this exception:** `just adw ask`, `just adw build`, `just adw build-review`, `just adw build-test`, `just adw document`, `just adw plan`, `just adw plan-build`, `just adw plan-build-test-quality`, `just adw prompt`, `just adw scout`, `just adw sdlc`, `just adw simple-sdlc`.

## Every front door

One row per front door, with its lane. A front door absent from this table is unlabelled, and the lint fails on it.

### The `just` command surface

51 recipes, discovered from the `just` module and import graph rather than listed by hand.

| Command | Lane | Exceptions | May claim workflow success | What it is |
| --- | --- | --- | --- | --- |
| `just adw ask` | adw | `pi-child` | no | One named agent, one prompt, traced end to end. No gate runs, so nothing here is accepted. |
| `just adw build` | adw | `pi-child` | no | One-shot implementation, gated on the diff matching the claims. |
| `just adw build-review` | adw | `pi-child` | no | Builder then an agent reviewer with a bounded revise loop. The reviewer is an agent, so its verdict is not deterministic acceptance. |
| `just adw build-test` | adw | `pi-child` | yes | Builder then the deterministic test block with a bounded fix loop. |
| `just adw default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just adw document` | adw | `pi-child` | no | Write up the work just done from the diff, gated on artifacts existing and being non-empty. |
| `just adw plan` | adw | `pi-child` | no | Produce a plan, gated on artifacts existing and being non-empty. |
| `just adw plan-build` | adw | `pi-child` | no | Planner then builder, gated on artifacts and on the diff matching the claims. |
| `just adw plan-build-test-quality` | adw | `pi-child` | yes | Plan and build, then the deterministic quality block, which includes the test block. |
| `just adw prompt` | adw | `pi-child` | no | One agent, one prompt, traced end to end. No gate runs, so nothing here is accepted. |
| `just adw quality` | adw | — | yes | The deterministic quality block only: lint, typecheck, and build. It calls no agent, so no Pi child exists for it. |
| `just adw scout` | adw | `pi-child` | no | Read-only recon, gated on artifacts existing. |
| `just adw sdlc` | adw | `pi-child` | yes | Plan, build, then the deterministic test block with a bounded fix loop. |
| `just adw simple-sdlc` | adw | `pi-child` | yes | Plan, build, deterministic test, agent review, and document, committing plan, code, and docs separately. |
| `just default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just inkwell default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just inkwell dev` | lifecycle | — | no | Boot the Inkwell application with reload-on-save. |
| `just inkwell run` | lifecycle | — | no | Boot the Inkwell application. |
| `just inkwell test` | lifecycle | — | no | Run the deterministic application test suite the factory's test phase runs. |
| `just local cc` | steering | `direct-claude-steering` | no | Boot Claude Code as a factory-level orchestrator on this machine, with permissions skipped. |
| `just local default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just local ipi` | steering | `direct-pi-steering` | no | Boot the Unix-only ipi shell function as a factory-level orchestrator on this machine. |
| `just local pi` | steering | `direct-pi-steering` | no | Boot Pi as a factory-level orchestrator on this machine. |
| `just obs default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just obs kill` | lifecycle | — | no | Stop a stuck ADW's recorded processes, skipping any pid that has been recycled. |
| `just obs phases` | lifecycle | — | no | Read one ADW's phases out of the trace database. |
| `just obs procs` | lifecycle | — | no | List the processes the trace believes one ADW is running. |
| `just obs rosters` | lifecycle | — | no | List which agent rosters exist and who is in them. |
| `just obs sessions` | lifecycle | — | no | Read recent ADW sessions out of the trace database. |
| `just obs tail` | lifecycle | — | no | Tail one ADW's live event stream. |
| `just obs ui` | lifecycle | — | no | Boot the observability UI over the trace database. |
| `just sbx default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just sbx lifecycle create` | lifecycle | — | no | Sandbox phase 1: create the VM and open its run record. |
| `just sbx lifecycle default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just sbx lifecycle execute` | lifecycle | — | no | Sandbox phase 4: launch an ADW inside the guest, detached, and record its pid. The host holds a pid, not a result; the ADW's own trace lives on the guest. |
| `just sbx lifecycle fill` | lifecycle | — | no | Sandbox phase 2: clone the repository into the VM at a pinned commit. |
| `just sbx lifecycle observe` | lifecycle | — | no | Sandbox phase 5: read the guest's state back to the host. |
| `just sbx lifecycle setup` | lifecycle | — | no | Sandbox phase 3: provision the guest toolchain and roster. |
| `just sbx lifecycle teardown` | lifecycle | — | no | Sandbox phase 6: destroy the VM. Always a separate, explicit decision. |
| `just sbx manage default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just sbx manage doctor` | lifecycle | — | no | Check the host prerequisites for the sandbox lane. |
| `just sbx manage harvest` | lifecycle | — | no | Pull a run's commits back from its sandbox as a bundle. |
| `just sbx manage list` | lifecycle | — | no | List the sandbox fleet and its run records. |
| `just sbx manage reap` | lifecycle | — | no | Revoke provisioned keys across the fleet. |
| `just sbx mount` | lifecycle | — | no | Chain create, fill, setup, and observe for one sandbox. Stops before teardown by design. |
| `just sbx orch cc` | steering | `direct-claude-steering`, `host-orchestrator` | no | Boot Claude Code as a host-side sandbox orchestrator, with permissions skipped and the host credentials in reach. |
| `just sbx orch default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |
| `just sbx orch pi` | steering | `direct-pi-steering`, `host-orchestrator` | no | Boot Pi as a host-side sandbox orchestrator, with the host credentials in reach. |
| `just sbx run agent` | steering | `direct-claude-steering` | no | Hand a prompt to Claude Code inside a mounted sandbox over a resumable session, with permissions skipped, and keep talking to it. |
| `just sbx run cmd` | lifecycle | — | no | Run any command inside a mounted sandbox synchronously and print its output. The generic inspection escape hatch. |
| `just sbx run default` | lifecycle | — | no | List this namespace's command surface. Runs nothing else. |

### Documented commands outside `just`

6 commands the command reference shows an operator directly.

| Command | Lane | Exceptions | May claim workflow success | What it is |
| --- | --- | --- | --- | --- |
| `python docs/validation/check_line_endings.py` | lifecycle | — | no | The authoritative strict LF working-tree validator. Read-only. |
| `python tools/ci_gate.py run` | lifecycle | — | no | The repository-owned deterministic offline gate over ci/checks.json. |
| `uv run docs/validation/check_adw_synchronization.py` | lifecycle | — | no | Validate installed, template, and generated ADW contracts without a provider call. |
| `python3 tools/evidence_manifest.py` | lifecycle | — | no | The offline evidence-manifest v1 schema, serializer, and validator tool. |
| `python3 docs/validation/check_evidence_manifest.py` | lifecycle | — | no | The offline evidence-manifest positive and watched-red controls. |
| `python3 docs/validation/check_front_door_lanes.py` | lifecycle | — | no | This taxonomy's lint: discovers every front door from the just graph bytes and requires each to carry a lane. |

## Enforcement

`docs/validation/check_front_door_lanes.py` runs in the deterministic offline gate (`ci/checks.json`). It asserts the property, never a proxy:

- the front-door set is **discovered from the `just` graph bytes**, so a new recipe is an unlabelled front door the moment it is written, and a keyword in prose cannot satisfy it;
- a lane value outside the taxonomy has nowhere to resolve, so it fails;
- a lane or exception entry whose `cannot_claim` list is empty fails;
- a `steering` lane or exception that declares it may claim ADW acceptance or SSSF workflow success fails;
- `may_claim_workflow_success` is checked against the rule, not trusted: it must equal `lane == "adw" and deterministic_acceptance` for every front door;
- this document and `COMMANDS.md` are parsed as tables, so documentation cannot drift from the registry.

Each of those is calibrated watched-red on every run against a bounded mutation of the real registry, and discovery itself is calibrated by adding a recipe to a copy of the graph and requiring exactly that recipe to appear. A control that stays green against its own defect is reported as a failure rather than a pass.

## Adding a front door

1. Add the recipe or command.
2. Add its entry to `docs/reference/front_door_taxonomy.json` with its lane, its exceptions, and whether the workflow it runs executes a deterministic test or quality block.
3. Add its row to this document, and to `COMMANDS.md` if the command reference shows it.
4. Run `python3 docs/validation/check_front_door_lanes.py`.

If a front door's lane cannot be determined, it is could-not-observe: do not label it by guess. Record the ambiguity as a defect and resolve it before the front door ships.
