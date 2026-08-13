# Repository Ownership and Sandbox Source

## Current baseline behavior

The current `fill` lifecycle recipe clones a hard-coded public repository:

`https://github.com/disler/inkwell-agent-sandboxes-and-software-factory.git`

It can optionally pin a SHA, tag, or branch **that exists in that clone**.

## Consequence

Local commits under `E:\SSSF` are not automatically visible to a newly created sandbox.

After the local baseline starts diverging from the upstream repository, a new sandbox will still clone the upstream source unless the fill/source mechanism is changed.

This is a critical boundary for post-baseline development.

## Required post-baseline increment

Before relying on new sandboxes to test local evolution:

1. establish a durable remote you control (normally a personal GitHub fork),
2. push the frozen baseline branch/tag,
3. make the sandbox source repository configurable,
4. preserve the upstream URL as an explicit default/reference,
5. pin sandbox fills to exact commits during proof runs.

Suggested contract:

```text
SSSF_REPO_URL=<public clone URL>
SSSF_PIN=<exact commit/tag when proving an increment>
```

Do not embed a personal repository URL in multiple lifecycle scripts.

## Acceptance

A fresh sandbox must be able to:

- clone the configured owned repository,
- check out an exact frozen commit,
- prove guest HEAD equals the requested commit,
- run the same setup/observe/teardown lifecycle,
- harvest changes back without ambiguity.

## Why this precedes major augmentation

Without canonical source ownership, the host can say “current SSSF” while the sandbox executes a different upstream revision.

That destroys reproducibility.

The repository source and exact commit therefore become explicit inputs to every post-baseline sandbox proof.

## Proven ownership state — B2-001

Canonical evolving repository:

`https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`

Remote roles:

- `origin` — operator-owned canonical repository; writable.
- `upstream` — Disler's repository; reference-only.
- `main` — latest accepted/proven platform line.
- `increment/*` — bounded development increments.
- `sssf-*` — immutable proven milestones and evidence.

Accepted increments are proved on increment branches, then canonical `main` is fast-forwarded to the exact accepted commit.

This does not yet solve sandbox source ownership. The current FILL implementation still clones Disler's repository. B2-002 will make repository URL and exact source revision explicit sandbox inputs.