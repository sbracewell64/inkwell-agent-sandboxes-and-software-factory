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

## Mutation fact and claim reconciliation

- `adws/adw_modules/mutation_fact.py` — sole owner of what the working tree did,
  and of the bidirectional comparison against an envelope's claims
- `adws/adw_modules/gates.py` — `diff_matches_claims` reads that fact; it never
  computes one
- `adws/adw_modules/permissions.py` — enforces the write boundary over the SAME
  fact, handed in rather than re-observed
- `docs/validation/check_mutation_fact.py` — CI-registered controls, dependency-free
- `tests/test_mutation_fact.py` — the typed gate, console, and trace layer

## Offline evidence manifest core

- `tools/evidence_manifest.py` — sole v1 schema/serializer/validator owner
- `docs/reference/EVIDENCE_MANIFEST.md` — contract and non-acceptance boundary
- `docs/validation/check_evidence_manifest.py` — positive and watched-red controls
- `docs/validation/fixtures/evidence_manifest/` — canonical offline fixtures

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
