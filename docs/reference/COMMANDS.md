# Command Reference

## Host validation

The authoritative strict LF invocation is:

```text
python docs/validation/check_line_endings.py --require-worktree-lf
```

The Windows bootstrap and host doctor invoke that same validator. Validation is
read-only; explicit remediation is documented in
`docs/operations/INSTALL_WINDOWS.md`.

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

## Record authority

```text
python3 tools/sqlite_authority.py matrix
python3 tools/sqlite_authority.py render
python3 tools/sqlite_authority.py observe --db adws/adw_data/sssf.db
python3 docs/validation/check_sqlite_authority.py
python3 docs/validation/check_sqlite_authority.py --controls
python3 docs/validation/check_sqlite_authority.py --exercise-visualizer [--bun <path>]
```

`observe` is three-valued: exit `0` observed-good, `1` observed-bad, `2` could-not-observe. A
missing or empty database is could-not-observe, never an empty pass. `--controls` prints what each
negative control observed, so a green result can be audited rather than trusted.

`--exercise-visualizer` is the only invocation that needs Bun. It executes the visualizer's real
read surface against a fixture and records the digests of the TypeScript it ran. The CI-registered
invocation stays stdlib-only and fails when those sources change without a re-run, so the recorded
exercise cannot decay into a claim about bytes that have moved.

## Identity warning

`run-id` and `adw-id` are different.

Never pass an ADW ID where a sandbox run ID is required.
