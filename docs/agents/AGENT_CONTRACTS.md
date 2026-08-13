# Agent Contracts

Canonical details remain in the roster and prompt files. This document explains the intended roles.

## planner

Purpose:

Turn the request into an implementable plan without implementing it.

Important boundary:

- repo writes limited to `specs/`
- runtime handoff directory remains writable
- full application edits are unauthorized

Required behavior:

- inspect only what is needed,
- write plan handoff,
- write/copy durable spec,
- emit typed `PlanOutput`.

## builder

Purpose:

Implement the accepted plan.

Boundary:

- broad repo mutation authority,
- still cannot edit protected factory machinery that grades its own work.

Required behavior:

- implement,
- report changed artifacts,
- emit typed `BuildOutput`.

## scout

Purpose:

Read-only reconnaissance.

Boundary:

`writes: []` with respect to the repo.

## reviewer

Purpose:

Verify what was built against what was asked.

Boundary:

read-only with respect to implementation; a checker should not quietly become the fixer.

## documenter

Purpose:

Write documentation based on the completed change.

Boundary:

documentation paths only.

## Role design rule

One agent, one prompt, one purpose.

If a role repeatedly needs two unrelated kinds of judgment, split the role instead of expanding the prompt indefinitely.
