# Recovery Runbook

## Failed create but VM exists

Check:

```bat
ssh exe.dev ls
type ".sandbox\runs\<run-id>.json"
```

Then test the exact VM host.

Do not create repeated new VMs until the first failure is understood.

## Bad run-record VM name

The Windows proof exposed a trailing carriage return in `vm_name`.

The repair principle is:

- correct the run record only when evidence establishes the intended VM identity,
- then use normal teardown,
- do not delete the VM out-of-band unless the lifecycle path is impossible.

## Teardown failure

Preserve the VM.

A teardown failure before revoke/destroy is recoverable.

The baseline `mktemp` incompatibility was fixed before rerunning teardown, after which both orphaned VMs were removed and keys revoked.

## Orphan check

```bat
ssh exe.dev ls
just sbx manage list
```

Use the repository's reap tooling for managed `sbx-` keys when appropriate.

## Agent-phase failure

Do not weaken the gate to make a run green.

Example baseline behavior:

- Nemotron declared nonexistent artifacts.
- Correct response: gate rejects.
- Incorrect response: remove `artifacts_exist`.

If the model is the weak link, change the roster in a controlled experiment.
