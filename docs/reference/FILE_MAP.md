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

## Mapped-surface parity (template ↔ live)

- `docs/validation/mapped_surface_contract.json` — authoritative typed relations and the non-isomorphic stamp mapping, transcribed from `install.py`
- `docs/validation/check_mapped_surface_parity.py` — mapped content parity, structured state, watched-red calibration on every run
- `docs/validation/check_stamped_substrate.py` — what a fresh disposable stamp really produces
- `docs/decisions/ADR-0004-MAPPED-SURFACE-PARITY.md` — decision record
- `.claude/skills/sssf/scripts/install.py` — the `stamp()` calls are the mapping's source of truth

## Sandbox orchestration

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

## Durable local system documentation

- `docs/`
