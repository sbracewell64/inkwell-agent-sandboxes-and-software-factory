# B2-002 — Sandbox Source Contract

**Status:** IN_PROGRESS  
**Starts from:** `sssf-b2-001-canonical-repository`

## Problem

The host now has a canonical operator-owned repository, but sandbox FILL still hard-codes Disler's upstream repository. A host checkout can therefore evolve while a new sandbox silently executes different source.

## Desired outcome

Every sandbox run records and proves both:

- the repository it cloned;
- the exact commit it executed.

The default source is the host checkout's `origin` and exact `HEAD`.

## Source contract

- `source_repo` — repository URL resolved from the host checkout's `origin`.
- `source_sha` — exact 40-character host `HEAD` commit at FILL time.
- `commit_sha` — actual guest HEAD after clone/checkout and gate.
- Accepted FILL requires `source_sha == commit_sha`.
- SETUP independently verifies the guest Git origin equals `source_repo`, guest HEAD equals the recorded SHA, and the tree is clean.

## Non-goals

- Replace exe.dev.
- Add another sandbox provider.
- Change ADW behavior.
- Change model rosters.
- Add arbitrary source-provider abstractions.
- Change canonical repository ownership established by B2-001.

## Acceptance

1. `fill.just` contains no hard-coded Disler clone authority.
2. FILL resolves the host `origin` and exact host `HEAD`.
3. The run record persists `source_repo` and `source_sha`.
4. FILL rejects a guest HEAD that differs from `source_sha`.
5. SETUP independently verifies guest `origin`, exact HEAD, and clean tree.
6. A fresh sandbox created from this increment proves the exact B2-002 commit is executing.
7. Teardown succeeds and leaves no VM or runtime key behind.

## Evidence

Pending implementation and live sandbox proof.

## Result

Pending.