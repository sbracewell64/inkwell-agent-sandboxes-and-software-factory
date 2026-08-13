# Command Reference

## Application

```text
just inkwell run
just inkwell dev
just inkwell test
```

## Factory

```text
just adw ...
```

ADW recipes execute workflows inside the appropriate working directory/config.

## Sandbox

```text
just sbx mount <name>
just sbx lifecycle create <run-id>
just sbx lifecycle fill <run-id>
just sbx lifecycle setup <run-id>
just sbx lifecycle execute <run-id> "<prompt>"
just sbx lifecycle observe <run-id>
just sbx lifecycle teardown <run-id>
```

## Sandbox management

```text
just sbx manage doctor
just sbx manage list
just sbx manage harvest <run-id>
```

## Sandbox inspection/delegation

```text
just sbx run cmd <run-id> "<command>"
just sbx run agent <run-id> "<delegation>"
```

## Observability

```text
just obs sessions
just obs phases <adw-id>
just obs tail <adw-id>
just obs ui
```

## Identity warning

`run-id` and `adw-id` are different.

Never pass an ADW ID where a sandbox run ID is required.
