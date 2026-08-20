# Command Reference

## Host validation

The authoritative strict LF invocation is:

```text
python docs/validation/check_line_endings.py --require-worktree-lf
```

The Windows bootstrap and host doctor invoke that same validator. Validation is
read-only; explicit remediation is documented in
`docs/operations/INSTALL_WINDOWS.md`.

## Windows FirstMate front door

```bat
E:\SSSF\bin\sssf-firstmate.cmd
E:\SSSF\bin\sssf-firstmate.cmd --print-menu
```

The tracked front door validates the canonical `E:\SSSF` checkout from any
caller directory and hands off to FirstMate's existing primary launcher.
`--print-menu` validates and renders without creating a session; `--detach` is
reserved for bounded host validation.

## Application

```text
just inkwell run
just inkwell dev
just inkwell test
```

## Deterministic CI

```text
python tools/ci_gate.py run --evidence ci-evidence.json
```

This repository-owned gate runs the enumerated offline checks in
`ci/checks.json`. It succeeds only after at least one check executes and every
result is `observed-good`; its JSON evidence retains `observed-bad` and
`could-not-observe` rather than treating either as green.

## Factory

```text
just adw ...
```

ADW recipes execute workflows inside the appropriate working directory/config.

Validate installed, template, and disposable generated ADW contracts without a provider call:

```text
uv run docs/validation/check_adw_synchronization.py
```

Validate mapped-surface parity between installable template bytes and live bytes,
including the watched-red calibration that runs on every invocation, with the
standard library only:

```text
python docs/validation/check_mapped_surface_parity.py
python docs/validation/check_mapped_surface_parity.py --state parity-state.json
```

Check what a fresh disposable stamp actually produces — that the reconciled
substrate arrives and intentional scaffold/user-owned divergence survives:

```text
python docs/validation/check_stamped_substrate.py
```

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

## Offline evidence manifest core

```text
python3 tools/evidence_manifest.py schema
python3 tools/evidence_manifest.py validate --help
python3 docs/validation/check_evidence_manifest.py
```

Manifest v1 validation is offline evidence checking only. It does not authorize runtime acceptance; HD-09 owns that integration.

## Identity warning

`run-id` and `adw-id` are different.

Never pass an ADW ID where a sandbox run ID is required.
