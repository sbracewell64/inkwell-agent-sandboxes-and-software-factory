# Operations Runbook

## Preflight

```bat
just sbx manage doctor
just inkwell test
```

Do not create a sandbox if the host preflight is red.

## Mount

```bat
just sbx mount <task-name>
```

Capture the emitted `run_id`.

Mount intentionally stops after observe.

## Inspect fleet

```bat
just sbx manage list
```

## Direct work path

```bat
just sbx lifecycle execute <run-id> "<prompt>"
```

This starts an ADW deterministically, normally detached.

## Agent-mediated path

```bat
just sbx run agent <run-id> "READ and EXECUTE .claude/skills/sssf/SKILL.md. Then: <work>"
```

Use when kickoff judgment is needed.

## Inspect the sandbox

```bat
just sbx run cmd <run-id> "cat run.log"
```

Use direct inspection for diagnosis, not as a substitute for trace/acceptance.

## Trace

Inside a suitable environment:

```text
just obs sessions
just obs tail <adw_id>
```

## Harvest

Harvest is non-destructive:

```bat
just sbx manage harvest <run-id>
```

Result lands under:

`refs/sandbox/<run-id>`

Harvest does not merge.

## Teardown

```bat
just sbx lifecycle teardown <run-id>
```

Teardown is explicit because destruction removes the live evidence environment.

## Failure rule

On a lifecycle failure:

1. do not immediately destroy the VM,
2. inspect run record,
3. inspect control-plane VM state,
4. inspect exact failing phase,
5. repair only the proven cause,
6. teardown through the lifecycle command when done.
