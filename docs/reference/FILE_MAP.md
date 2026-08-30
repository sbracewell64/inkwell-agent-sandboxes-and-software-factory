# File Map

Use `TREE.md` for the complete concise map. This page groups files by architectural responsibility.

## Workflow authority

- `adws/adw_*.py`
- `adws/adw_modules/`

## Agent configuration

- `adws/adw_sssf_config/`
- `adws/adw_data/prompt_engineering/`
- `adws/adw_data/harness_engineering/`

## Runtime evidence

- `adws/adw_data/sessions/`
- `adws/adw_data/sssf.db`

Never hand-edit session evidence.

## Offline evidence manifest core

- `tools/evidence_manifest.py` — sole v1 schema/serializer/validator owner
- `docs/reference/EVIDENCE_MANIFEST.md` — contract and non-acceptance boundary
- `docs/validation/check_evidence_manifest.py` — positive and watched-red controls
- `docs/validation/fixtures/evidence_manifest/` — canonical offline fixtures

## Validator observation boundary

- `tools/ci_gate.py` — three-valued gate runner and owner of the reserved
  could-not-observe exit code validators report their own observation failure with
- `docs/increments/HD-09_VALIDATOR_OBSERVATION_BOUNDARY.md` — the invariant, the
  contract, and its proof
- `tests/test_validator_observation_boundary.py` — executable red/green over the
  validator and gate binaries, including the control that a real predicate
  failure still reports observed-bad
- `tools/windows_host.py` — the Windows bootstrap and host doctor; owns the same
  boundary for its own child tools, keeping an absent tool a doctor finding while
  everything derived from a child that never ran is could-not-observe
- `docs/increments/HD-10_HOST_DOCTOR_OBSERVATION_BOUNDARY.md` — the host-doctor
  instance of the invariant and its proof
- `tests/test_windows_host_observation_boundary.py` — executable red/green over
  the host doctor, including the controls that a present-but-failing tool is
  still FAIL and that a present tool is really executed

## Sandbox contract and orchestration

- `docs/reference/SBX-0_SEMANTICS_INVENTORY.json` — durable SBX-0 source-generation/content-digest handoff and classification-compatible owner-per-fact inventory
- `docs/increments/SBX-0_SEMANTICS_INVENTORY.md` — publication scope, observation rules, and non-promotion boundary
- `docs/validation/check_sbx0_inventory.py` — deterministic inventory validator and watched-red controls
- `adws/adw_modules/sandbox_provider.py` — SBX-1 typed provider contract, SSSF lifecycle seam, and deterministic fake
- `docs/reference/SANDBOX_PROVIDER.md` — sole public provider contract/owner-boundary reference
- `just/sandbox/`
- `sandbox_mount/host/`
- `sandbox_mount/guest/`

## App

- `apps/inkwell/`

## Agent knowledge

- `.claude/skills/sssf/`
- `.claude/skills/sssf-sandbox-orchestrator/`
- `.claude/skills/sandbox-exe-dev/`

## Historical/generated material

- `specs/`
- `app_docs/`
- `ai_docs/`

## Windows operator entry

- `bin/sssf-firstmate.cmd` — tracked transport-only Windows handoff at canonical `E:\\SSSF`
- `tests/test_windows_front_door.py` — caller-cwd and visible-refusal behavior checks
- `docs/operations/INSTALL_WINDOWS.md` — Windows installation and front-door runbook

## Planning foundation

authoritative planning source: planning/future-sssf; commit: eab880656b4ef00174ea514cca128f6336632fcf; tree: 5328b8a437d894682f4ac1c5d7ae581694410c43; generation: planning/future-sssf@eab880656b4ef00174ea514cca128f6336632fcf:5328b8a437d894682f4ac1c5d7ae581694410c43

- `docs/development/PLANNING_LIFECYCLE.md` — sole closed transition-contract owner
- `docs/development/PLANNING_STATE.json` — durable current state, projection scope, and transition evidence
- `docs/development/INCREMENT_PROTOCOL.md` — boundedness-delta increment contract
- `docs/development/BOUNDEDNESS_LAW.md` — current boundedness law
- `docs/development/FUTURE_CANDIDATES.md` — complete current-authority future-item state projection
- `docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md` — mandatory SEQUENCED pre-SBX-2 boundedness predecessor
- `docs/decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md` — FUT-003 decision boundary
- `docs/decisions/ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md` — FUT-001 DSH decision boundary
- `docs/validation/check_planning_foundation.py` — sole offline planning validator

## Durable local system documentation

- `docs/`
