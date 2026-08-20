# LAUNCH-1-R1 — Public identity sink correction

## Intent

Repair the existing LAUNCH-1 Windows front door after Browser Sol issue 6
ruling `SOL-FM-SSSF-LAUNCH1-POSTMERGE-20260820-1052`. The operator-facing
identity line must contain exactly the project, repository, root, and handoff;
it must not expose `head=` or `branch=`.

The correction starts from exact current SSSF `main`:

```text
b902cdcecd65c8ba03031875297d31e990f12c11
```

PR #17 and its resulting `main` commit
`312001ddbbead5cc957bc8db19f4b0b2c1d9d34c` remain immutable adverse
provenance. This successor does not rewrite or delete either history.

## Scope and boundary

Only the tracked launcher identity sink and its deterministic behavioral
controls are corrected. The existing transport boundary remains unchanged:

- `E:\SSSF` is resolved independently of caller cwd;
- the launcher enters the existing FirstMate path;
- Bash, Git, and grep refusals remain dependency-specific and actionable;
- only a named non-default Herdr lab is accepted for host validation;
- the shortcut, if inspected, remains pointed at the tracked launcher;
- Docker/SBX-2, Wayfinder, DSH, new orchestration, credentials, and security
  boundaries remain out of scope.

The launcher no longer observes Git source `HEAD` or symbolic branch state:
there is no distinct exact-property owner for either value in this public
transport sink. Other repository artifacts may retain branch/source identity
where their own exact-property contract requires it.

## Deterministic controls

The public sink is asserted positively for `project=sssf`, the canonical
repository, `root=E:\SSSF`, and `handoff=firstmate`. The same behavioral
assertion rejects manufactured `head=` and `branch=` sink variants, so each
prohibited field has a watched-red negative control rather than relying on
absence alone. Attached and detached fixture checkouts both exercise the
handoff without making either state operator-facing identity.

The local test is necessary but not sufficient for acceptance. Final
acceptance also requires direct host validation only through the named guarded
Herdr lab, fresh exact-head Linux and Windows deterministic CI, and a durable
assignment-distinct independent semantic review of the successor PR. The
successor PR must remain open and unmerged; the landing boundary is separate.
Unavailable host-specific dimensions are recorded as could-not-observe, never
as PASS.

## Evidence collected

- `python3 -m unittest -v tests/test_windows_front_door.py` — six tests passed,
  including positive project/repository/root/handoff controls and watched-red
  `head=`/`branch=` sink mutations.
- `docs/evidence/LAUNCH-1-R1_HOST_PROOF.md` — guarded named-lab host proof,
  independent Windows caller directories, FirstMate handoff, and unchanged
  shortcut inspection.
- Fresh exact-head Linux and Windows deterministic CI plus an
  assignment-distinct independent semantic review remain CNO until the
  successor PR is opened and those exact-head observations complete. The
  successor is never merged by this increment.
