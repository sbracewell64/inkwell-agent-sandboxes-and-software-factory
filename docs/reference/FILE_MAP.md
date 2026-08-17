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

## Derived-source provenance contract

- `docs/reference/DERIVED_SOURCE_PROVENANCE.md` — contract, template, and the two standing laws
- `docs/validation/check_derived_source_provenance.py` — sole enforcer and its watched-red controls
- `docs/provenance/derived_source/` — record registry; empty, and emptiness is not a certification
- `docs/evidence/hd15/` — retained negative controls and the observed population

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

## Durable local system documentation

- `docs/`
