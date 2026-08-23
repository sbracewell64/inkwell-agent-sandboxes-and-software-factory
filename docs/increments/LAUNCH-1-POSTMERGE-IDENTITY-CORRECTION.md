# LAUNCH-1-R2 — Current-main public identity sink correction

## Intent and provenance

Repair the landed LAUNCH-1 Windows front door under Browser Sol ruling
`SOL-FM-SSSF-LAUNCH1-POSTMERGE-20260820-1052`. The operator-facing identity
line contains exactly project, repository, root, and handoff; it does not expose
`head=` or `branch=`.

```text
starts_from: 991d3a64f1b96a8b9637f97060d692af3518228f
increment: LAUNCH-1-R2
```

Original PR #17 and resulting `main`
`312001ddbbead5cc957bc8db19f4b0b2c1d9d34c` remain immutable adverse
provenance. PR #19 at exact head
`6f409ff111ddca747e76f1fde20645f98e09d7d2`, tree
`a6a758134715d552ee13032bbeced0cade6ec74a`, remains unchanged predecessor
evidence. Neither predecessor's review, CI, or host evidence transfers to this
successor.

## Scope and boundary

Only the tracked launcher public identity sink, its deterministic behavioral
controls, and the durable records for that correction change. The existing
transport boundary remains unchanged:

- `E:\SSSF` resolves independently of caller cwd;
- the launcher enters the existing FirstMate path;
- Bash, Git, and grep refusals remain dependency-specific and actionable;
- only a named non-default Herdr lab is accepted for lifecycle validation;
- the public shortcut remains pointed at the tracked launcher;
- Docker/SBX-2, Wayfinder, DSH, new orchestration, application behavior,
  credentials, and security boundaries remain out of scope.

The launcher no longer observes Git HEAD or symbolic branch state because this
public transport sink has no distinct owner for those properties. Other
artifacts may retain exact source identity where their own contract requires it.

## Deterministic controls

The behavioral assertion owns the complete public line and therefore positively
controls all four required fields, ordering, uniqueness, and the absence of any
extra field. Attached and detached fixture checkouts execute the same handoff.
Separate mutations append `head=stale` and `branch=stale` at the real `printf`
sink; each mutant must execute successfully before the exact identity assertion
rejects it. Static controls preserve canonical root/repository, FirstMate
launcher/admission/session-start checks, transport-only topology, and the
prohibited-field contract.

The full host test additionally applies the complete identity assertion to
tracked `--print-menu` executions from independent Windows caller directories.
Unavailable host dimensions are CNO, never PASS.

## Acceptance boundary

Local controls are necessary but insufficient. Final acceptance requires:

1. fresh exact-successor host validation, with lifecycle behavior only through a
   separately authorized guarded non-default Herdr lab;
2. fresh exact-head Ubuntu and Windows deterministic CI;
3. an assignment-distinct independent semantic review of the final successor;
4. a separate lawful landing decision.

The repository CI matrix is general regression evidence: `ci/checks.json` does
not schedule this host-topology-dependent launcher suite. Launcher-specific
acceptance therefore remains separately bound to the deterministic fixture and
supported Windows/WSL host observations rather than treating CI as proof of a
check it did not execute.

## Evidence accounting

The prior PR #19 host narrative is retained through its immutable Git object and
PR, not copied as successor proof. A fresh successor host record may be added
only after observation and must bind the tested source commit/tree, launcher
blob, commands, outputs, guard/lab identity when applicable, and shortcut
inspection. Exact-head CI and assignment-distinct review remain CNO until the
successor PR exists and those observations complete.
