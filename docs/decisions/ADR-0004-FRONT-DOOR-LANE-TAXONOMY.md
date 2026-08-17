# ADR-0004 — Every Front Door Declares a Lane, and Every Lane Declares What It Cannot Claim

**Status:** Accepted
**Date:** 2026-08-17

## Context

Several SSSF front doors invoke an agent outside the ADW trace. `just local cc` and `just sbx orch cc`
run Claude with `--dangerously-skip-permissions` outside the trace entirely. `just sbx run agent` binds
a lifecycle run ID and a Claude session UUID through a host sentinel file and emits no ADW phase, gate,
usage, or tool trace — yet it can edit and commit. Pi children carry their own gap: exactly one pid is
reported per Pi turn, so nothing that turn spawns is recorded.

None of that is a defect in the commands. Direct steering is intentionally a separate orchestration and
steering lane, and the retained session and run identifiers, the synchronous terminal output, and the
comparatively rich ADW Pi parent tracing are all correct as they are.

The defect was in the documentation: it presented these as ordinary front doors with no explicit
acceptance or provenance exception. The harm that follows is a claim, not a crash — direct steering
changes source or decides progression, and an operator later cites normal SSSF trace and acceptance
guarantees that never wrapped that work.

## Decision

Every front door of this repository declares exactly one lane — `adw`, `lifecycle`, or `steering` — in
a machine-readable registry, `docs/reference/front_door_taxonomy.json`.

Every lane and every exception in that registry states **two** things: its allowed purpose, and the
claims that cannot be made from it. The negative half is mandatory. A taxonomy that records only what a
lane IS leaves exactly the gap that produced this defect.

Only the `adw` lane, and only when the workflow it runs executes a deterministic test or quality block,
may claim SSSF workflow success. That rule is encoded rather than asserted: `may_claim_workflow_success`
must equal `lane == "adw" and deterministic_acceptance` for every entry.

Exceptions are narrow and named: `direct-claude-steering`, `direct-pi-steering`, `host-orchestrator`,
and `pi-child`. Each names the bounded set of front doors it covers and records what that lane genuinely
preserves, so a later increment cannot "fix away" behaviour that is deliberate.

`docs/validation/check_front_door_lanes.py` enforces the whole contract in the deterministic offline
gate, and asserts the property rather than a proxy: the front-door set is discovered from the `just`
module and import graph bytes, lanes resolve by structural lookup, cannot-claim statements are read as
structured fields, and both human-facing documents are parsed as tables.

## Consequences

Positive:

- a front door added without a lane fails the gate, so it cannot ship presenting guarantees it does not
  offer;
- a reader meeting a front door in `COMMANDS.md` meets its limits in the same place;
- direct steering is legitimised rather than tolerated — it is a labelled lane with a stated purpose,
  not an undocumented gap;
- the ADW lane's own limits are stated too: a traced run without deterministic acceptance is not an
  accepted run, and an ADW record does not vouch for what a Pi turn's own children did.

Cost:

- three artifacts must stay in step — the registry, the contract document, and the command reference —
  though the lint fails rather than lets them drift;
- a moved recipe requires its registered source to be corrected;
- classification is a judgement that must be made deliberately for each new front door.

## Rejected alternatives

### Write the lane label into each `.just` recipe

Rejected for now. `just` is not installed on the authoring host, so the effect of an added comment on
`just --list`'s doc-comment association was could-not-observe, and this increment is documentation plus
a docs lint — editing the executable command surface is outside its fence. The registry is bound to the
recipe bytes by discovery, which achieves the coupling without touching source custody.

### Search the documentation for lane keywords near each command

Rejected. A keyword search passes on a mention in prose. The lint must establish that a front door
carries a classification from the taxonomy, not that some keyword appears nearby.

### Maintain the front-door list by hand

Rejected. A hand-maintained list cannot report that it is incomplete, which is the failure mode being
closed. Discovery reads the `just` graph and refuses any construct it has not been calibrated against.

### Instrument the steering lanes now instead of documenting them

Rejected here, not on the merits. Capturing structured events, model, usage, terminal, or cancel data
into a run-bound steering record is HD-10 and is blocked on the CLI-lane audit. Documenting the current
exception was explicitly allowed to start independently, and it is what this decision covers.
