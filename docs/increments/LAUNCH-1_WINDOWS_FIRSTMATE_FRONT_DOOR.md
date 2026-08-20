# LAUNCH-1 — Windows FirstMate Front Door

## Intent

Implement the smallest tracked Windows double-click front door for the
operator-owned SSSF checkout. It must resolve `E:\SSSF` without relying on the
caller cwd and enter the existing FirstMate → SSSF supervision/admission path.

## Baseline

```text
starts_from: bee9296a4c94b1dc3da6991acd1755a91fa681eb
increment: LAUNCH-1
branch: fm/sssf-launch-1
```

## Scope and boundary

`bin/sssf-firstmate.cmd` is a transport adapter only. It validates the exact
canonical root, checks the canonical Git origin and checkout identity, checks
that FirstMate's existing launcher/admission/session-start path and `sssf`
registry entry are present, prints non-secret identity, and hands control to
FirstMate's `bin/fm-launch.sh`.

It does not run `just`, launch Claude directly, choose a task, schedule work,
retry, accept work, mutate Docker/SBX state, activate Wayfinder, or activate
DSH. FirstMate retains its own home and owns project selection, supervision,
and admission.

## Failure contract

The front door refuses with an actionable message for:

- a missing `E:\SSSF` checkout;
- missing WSL;
- missing Bash, Git, or grep in WSL, with dependency-specific repair guidance;
- a wrong WSL root, missing Git checkout, missing required SSSF files, or a
  non-canonical origin;
- unreadable or unregistered FirstMate configuration/scripts; and
- an invalid command-line mode or invalid named Herdr lab value.

The normal no-argument mode opens FirstMate's existing menu. `--print-menu`
performs identity/configuration validation and renders that menu without
creating a session. `--detach` selects Claude and returns after starting the
FirstMate primary; it exists for bounded host validation and is not the
shortcut target.

## Behavioral proof

`python3 -m unittest -v tests/test_windows_front_door.py` covers:

- actual Windows CMD/WSL `--print-menu` launches from two independent caller
  directories (`C:\Windows` and `C:\Users\Public`) and reports
  `root=E:\SSSF`, the canonical repository, and `handoff=firstmate`;
- the tracked source contract is transport-only and contains no direct factory,
  Docker, Wayfinder, or DSH activation;
- an unknown argument returns a visible usage refusal with exit status `2`;
- live HEAD and honest attached/detached branch identity derivation; and
- dependency-specific Bash, Git, and grep preflight diagnostics before use.

A direct host launch was also observed through the tracked front door in the
named disposable Herdr lab only:

```text
cmd.exe /d /c call <tracked launcher> --detach
front_door_launch_rc=0
identity: project=sssf, canonical repository, root=E:\SSSF, handoff=firstmate
lab inventory: workspace label=firstmate; tab label=firstmate; pane agent=claude; agent_status=idle
pane identity: Claude Code Fable 5 with high effort · Claude Max
```

The lab was provisioned and torn down only with the named guarded
`bin/fm-herdr-lab.sh` helper from the regenerated brief; its default-session
tripwire remained intact. The primary's own working home is deliberately
FirstMate's home: this transport increment proves the canonical SSSF identity
and handoff, not a second project-bound FirstMate home. Project choice remains
with the existing FirstMate registration/admission path.

## Shortcut evidence

The authorized reversible shortcut was created only after the tracked launcher
and behavioral tests were stable:

```text
path: C:\Users\Public\Desktop\SSSF FirstMate.lnk
target: E:\SSSF\bin\sssf-firstmate.cmd
arguments: none
working directory: E:\SSSF
```

The shortcut points directly at the tracked launcher and contains no private or
credential value. It is intentionally public-desktop scoped so the recorded
path contains no operator username.

## Three-valued limits

- **Observed-good:** tracked launcher contract, independent-cwd host menu
  launch, canonical root identity, named-lab FirstMate/Claude launch, and
  shortcut target inspection.
- **Could-not-observe:** a post-merge launch from the canonical checkout after
  the new file is installed there; this worktree's launcher was invoked against
  the already-present canonical `E:\SSSF` checkout and handed into the current
  FirstMate home. No claim is made that the unmerged canonical checkout already
  contains the new tracked file.
- **Not activated:** Docker/SBX mutation, Wayfinder, and DSH remain outside the
  increment.
