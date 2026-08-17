# HD-14 — Front-Door Lane and Exception Contracts (documentation half)

**Status:** PROVEN
**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`

## Problem

Several front doors invoke an agent outside the ADW trace.

- `just local cc` and `just sbx orch cc` invoke Claude with `--dangerously-skip-permissions`, outside
  the ADW trace entirely.
- `just sbx run agent` binds a lifecycle run ID and a Claude session UUID through a host sentinel file
  but emits no ADW phase, gate, usage, or tool trace.
- Pi children carry their own gap: `adws/adw_modules/agent_pi.py` reports exactly one pid to
  `on_spawn`/`on_exit`, so nothing the Pi turn itself spawns is recorded.

The documentation presented all of these as ordinary front doors, with no explicit acceptance or
provenance exception.

The smallest counterfactual: `just sbx run agent` can edit and commit, and no ADW ID, typed envelope,
permission fact, gate, usage record, or `run.finish()` exists for that turn.

**The harm is a claim, not a crash.** Direct steering changes source or decides progression, and an
operator later cites normal SSSF trace and acceptance guarantees that never wrapped that work.

## Desired outcome

An explicit, machine-readable exception taxonomy in which each entry states its allowed purpose **and,
decisively, the claims that cannot be made from it**; every front door labelled `lifecycle`,
`steering`, or `adw`; and only ADW plus deterministic acceptance entitled to claim SSSF workflow
success.

## Non-goals

This increment is **documentation plus a docs lint. No instrumentation.**

- No structured event, model, usage, terminal, or cancel capture into a run-bound steering record.
  That is HD-10 and is not authorised here.
- No change to any `.just` file, to `adws/`, or to any executable command behaviour. Source custody is
  preserved exactly; the only executable addition is the new offline validator.
- No attempt to make direct steering into an ADW. Direct steering is **intentionally** a separate
  orchestration and steering lane. Nothing here removes or discourages it.

Explicitly preserved because they are already correct: the Claude session ID and lifecycle run ID are
retained, synchronous terminal output stays visible, ADW Pi parent tracing stays comparatively rich,
and `adws/adw_modules/agent_cc.py` continues to refuse Claude as an ADW coding agent.

## Files / boundaries in scope

- machine-readable registry: `docs/reference/front_door_taxonomy.json`;
- contract document: `docs/reference/FRONT_DOOR_LANES.md`;
- operator surface: `docs/reference/COMMANDS.md`;
- deterministic lint: `docs/validation/check_front_door_lanes.py`, registered in `ci/checks.json`;
- decision record: `docs/decisions/ADR-0004-FRONT-DOOR-LANE-TAXONOMY.md`;
- evidence: `docs/evidence/hd14/`;
- ledger/proof/reference routing updates.

## Design

Three lanes, exhaustive over the front-door surface:

| Lane | What runs in it |
|---|---|
| `adw` | A bounded AI Developer Workflow: ADW ID, typed envelopes, gates, usage, process record, `run.finish()`. |
| `lifecycle` | A deterministic, code-owned command. No agent reasoning. |
| `steering` | An ask handed straight to an interactive agent, outside the ADW trace. |

Four exceptions, each carrying both halves — allowed purpose, what it genuinely preserves, and the
claims that cannot be made from it:

- `direct-claude-steering` — `just local cc`, `just sbx orch cc`, `just sbx run agent`;
- `direct-pi-steering` — `just local pi`, `just local ipi`, `just sbx orch pi`;
- `host-orchestrator` — `just sbx orch cc`, `just sbx orch pi`;
- `pi-child` — every ADW front door that calls an agent. This one narrows the ADW lane from inside
  rather than sitting outside it.

`direct-pi-steering` is beyond the three the audit named, and is present because `just local pi`,
`just local ipi`, and `just sbx orch pi` are steering-lane front doors whose harness is Pi, not Claude.
Labelling them under a Claude exception would have been a guess; leaving them unlabelled would have
been the original defect.

The acceptance rule is encoded, not asserted: `may_claim_workflow_success` must equal
`lane == "adw" and deterministic_acceptance` for every front door. Deterministic acceptance means the
workflow executes `quality.run_inkwell_tests` or `quality.run_inkwell_quality`. Five ADW front doors
qualify (`build-test`, `quality`, `sdlc`, `plan-build-test-quality`, `simple-sdlc`); the other eight
are traced, not accepted. No `lifecycle` or `steering` front door qualifies, including
`just inkwell test`, whose green suite is a green suite and not a workflow outcome.

### Why the lint asserts a property and not a proxy

A keyword search would pass on a mention in prose. This fleet has closed that exact defect three times
this week in three different repositories. So:

- the front-door set is **discovered from the `just` module and import graph bytes**, never from a
  hand-maintained list. A recipe with no registry entry is an unlabelled front door. Discovery refuses
  any column-0 construct it has not been calibrated against, because a silently skipped line is
  exactly how a front door goes unlabelled;
- each entry's lane is resolved by **structural lookup** in the taxonomy, so a value outside the
  taxonomy has nowhere to resolve;
- each lane and exception's cannot-claim statement is read as a **structured field** that must be
  nonempty. The negative half is not optional;
- `FRONT_DOOR_LANES.md` and `COMMANDS.md` are parsed as **tables**, and every cannot-claim statement
  must appear in the contract document verbatim, so documentation cannot drift from the registry.

### Lane determination

Every one of the 51 discovered `just` recipes and 6 documented commands had a determinable lane, read
off the bytes of its recipe body and, for the ADW lane, the `session.ensure` / phase / gate / quality
calls in the workflow it invokes. None was could-not-observe, so none was labelled by guess. A future
front door whose lane cannot be determined is could-not-observe and must be reported, not labelled;
`FRONT_DOOR_LANES.md` says so where the reader adds one.

### One deliberate omission

The lane labels are not written into the `.just` files themselves. `just` is not installed on the
authoring host, so the effect of an added comment on `just --list`'s doc-comment association could not
be observed rather than guessed at. The registry plus the two documents carry the label, and the lint
binds them to the recipe bytes.

## Risks / failure modes

- A new front door with no registry entry fails the lint rather than shipping unlabelled.
- A front door whose recipe moves file must have its registered `source` corrected; a stale source
  fails.
- An absent registry, absent contract document, or unreadable/unknown-schema registry is
  COULD-NOT-OBSERVE and exits non-zero. It is never a pass.
- Discovery losing the audit's three named carriers is COULD-NOT-OBSERVE, so an under-enumerating
  parser cannot report a quiet green.
- The lint governs claims, not runtime behaviour. It cannot detect a steering turn that happened; it
  can only ensure no front door is documented as offering guarantees it does not.

## Acceptance

### Deterministic check

```text
python3 docs/validation/check_front_door_lanes.py
```

Registered in `ci/checks.json` as `front-door-lane-taxonomy-validator`, so it runs on Ubuntu and
Windows in the deterministic offline gate.

### Red-capable controls, watched failing first

Recorded in `docs/evidence/hd14/`.

| Control | Observed |
|---|---|
| An UNLABELLED front door fails the docs lint | RED before repair: all 51 discovered front doors reported unlabelled against the real files, taxonomy and contract document absent — `unlabelled-front-door-red.txt` |
| A real new unlabelled recipe fails | RED end-to-end: `just local steer-quietly` appended to `just/local.just`, reported unlabelled, file restored byte-identical — `lane-controls.txt` |
| A softened cannot-claim statement in the contract document fails | RED: "cannot claim bounded permissions" reworded to "should probably not claim tightly bounded permissions" — `lane-controls.txt` |
| A front door labelled outside the taxonomy fails | RED, in-lint, every run |
| A taxonomy entry missing its cannot-claim statement fails | RED, in-lint, every run |
| A steering or host-orchestrator entry claiming ADW acceptance fails | RED, in-lint, every run |
| A steering front door claiming workflow success fails | RED, in-lint, every run |
| An ADW front door without deterministic acceptance claiming workflow success fails | RED, in-lint, every run |
| Discovery reads the bytes, not a memorised list | RED, in-lint: a recipe added to a copy of the graph must surface as exactly that front door |
| A correctly labelled front door with a complete taxonomy entry PASSES | GREEN on the repaired tree with 51 + 6 labelled front doors, so none of the above is vacuously red |

Each in-lint control mutates a deep copy of the real registry and runs the same `validate_taxonomy()`
the real check runs. A control that stays green against its own defect is reported as a failure, never
as a pass.

### Semantic review

Independent review is delegated to the required no-mistakes pipeline before publication.

## Evidence

- `docs/evidence/hd14/unlabelled-front-door-red.txt`
- `docs/evidence/hd14/lane-controls.txt`

## Follow-on

Capturing structured events, model, usage, terminal, or cancel data into a run-bound steering record
is HD-10 and remains blocked on the CLI-lane audit. This increment documents the exception; it does not
close it.
