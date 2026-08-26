# ADR-0004 — SSSF Windows FirstMate Front Door

- **Status:** accepted for LAUNCH-1; public identity corrected by the current-main LAUNCH-1-R2 successor
- **Date:** 2026-08-20
- **Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`

## Decision

Add one tracked SSSF Windows front door at
`bin/sssf-firstmate.cmd`. It owns only the transport handoff:

1. require the canonical Windows checkout at `E:\SSSF`;
2. enter WSL with `--cd E:\SSSF`, independently of the caller's current directory;
3. verify the WSL checkout, canonical repository identity, and non-secret Git
   identity;
4. verify that the existing FirstMate launcher, admission script, session-start
   script, and registered `sssf` project are present; and
5. hand off to FirstMate's existing `fm-launch.sh` primary path.

The launcher exports the canonical SSSF identity as non-secret handoff context,
but does not bind a project, choose work, run a factory recipe, or replace
FirstMate's supervision/admission authority. FirstMate retains its own home and
project-registration semantics; `E:\SSSF` is the validated source identity for
the handoff, not a second FirstMate home.

### Current-main public identity correction

PR #17 and resulting `main` commit
`312001ddbbead5cc957bc8db19f4b0b2c1d9d34c` remain adverse provenance. PR #19
at `6f409ff111ddca747e76f1fde20645f98e09d7d2` remains unchanged predecessor
evidence. Starting from exact current `main`
`991d3a64f1b96a8b9637f97060d692af3518228f`, the successor removes unused Git
HEAD/branch observations from the public transport sink so it emits exactly
project, repository, root, and handoff. This does not ban exact source identity
from artifacts with a distinct exact-property owner.

The default mode opens the existing FirstMate menu. `--print-menu` is a
side-effect-free inspection mode. `--detach` is a bounded host-validation mode
that selects the installed Claude entry and returns after the FirstMate primary
has been started. A named `fm-lab-*` session may be supplied only through the
host-validation seam; `default` is refused.

## Alternatives rejected

- **Direct Claude or `just local cc`:** bypasses FirstMate supervision and
  admission.
- **New project orchestrator or task dispatcher:** exceeds a transport-only
  front door and would duplicate FirstMate authority.
- **Binding FirstMate's private `FM_HOME` to `E:\SSSF`:** conflates FirstMate
  home state with project identity and writes operational state into the project
  checkout.
- **Shortcut to an untracked wrapper or direct model CLI:** would not provide a
  stable tracked transport boundary.

## Consequences

- Double-click launch is independent of caller cwd and fails visibly when the
  canonical checkout, WSL, FirstMate path, registry, or required scripts are
  missing.
- The outer launch exposes only project, repository, root, and handoff. No
  credentials, auth-home paths, `head=`, or `branch=` values are embedded.
- Project selection and all subsequent supervision/admission remain in the
  existing FirstMate path.
- Host-specific live launch evidence is retained as observed-good only for the
  named disposable Herdr lab; any unavailable host dimension remains CNO.
