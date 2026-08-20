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

## Sandbox contract and orchestration

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

## Durable local system documentation

- `docs/`
