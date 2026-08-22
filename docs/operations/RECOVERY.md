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

## Reclaiming the trace journal

`adws/adw_data/sssf.db` and the per-session `adws/adw_data/sessions/<adw_id>/`
runtime (its `events.jsonl`, envelopes, and context handoff) are the local
observability journal. They grow with every run and are deliberately not
evicted in place: an operator diagnosing a run reads the whole history, and a
tracer that silently dropped older sessions would be worse than a large file.
Both paths are gitignored, are never accepted evidence, and are declared
`SAFE_UNBOUNDED` in `docs/reference/BOUNDEDNESS_REGISTRY.json` under
`sssf.tracer.durable_journal` and `sssf.run.session_runtime_dir`.

Reclaim deliberately, not automatically. Move aside rather than delete, so a
run still under discussion is recoverable:

```bash
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
mv adws/adw_data/sssf.db      "adws/adw_data/sssf.db.$STAMP"
mv adws/adw_data/sessions     "adws/adw_data/sessions.$STAMP"
```

A new run recreates both. Nothing in the factory reads the journal to decide an
outcome, so reclaiming it costs history and nothing else.

Oversight: `docs/validation/check_boundedness.py` fails if this section
disappears, because the `SAFE_UNBOUNDED` justification for the journal names it
as the archive strategy.
