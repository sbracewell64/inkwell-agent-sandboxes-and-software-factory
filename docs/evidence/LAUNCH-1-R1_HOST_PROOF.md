# LAUNCH-1-R1 guarded host proof

- **Successor source:** tracked launcher from the LAUNCH-1-R1 worktree, starting
  from `b902cdcecd65c8ba03031875297d31e990f12c11`
- **Guard:** `/home/shane/kun-agent-workspace/bin/fm-herdr-lab.sh`
- **Disposable lab:** `fm-lab-sssf-launch-1-3261882-26077`
- **Lifecycle:** provision and teardown were run only through the guard; the
  guard completed its default-session tripwire checks before teardown returned.

## Observations

The tracked launcher was invoked through Windows CMD with `--print-menu` from
both `C:\Windows` and `C:\Users\Public`. Each returned `0` and printed this
public identity line:

```text
SSSF front door: project=sssf repository=sbracewell64/inkwell-agent-sandboxes-and-software-factory root=E:\SSSF handoff=firstmate
```

Neither output contained `head=` or `branch=`. The same tracked launcher was
then invoked with `--detach`; it returned `0` and entered the existing
FirstMate path. Guarded Herdr observations found:

- workspace label: `firstmate`;
- tab label: `firstmate`;
- pane agent: `claude`;
- agent status: `idle`.

These are observed-good host dimensions for this named lab. No claim is made
about an uninstalled or otherwise unavailable host dimension.

## Shortcut inspection

The pre-existing reversible shortcut was inspected without modification:

```text
path: C:\Users\Public\Desktop\SSSF FirstMate.lnk
target: E:\SSSF\bin\sssf-firstmate.cmd
arguments: none
working directory: E:\SSSF
```

The tracked target did not change, so no shortcut update was required.
