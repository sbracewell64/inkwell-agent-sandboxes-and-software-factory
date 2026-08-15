# ADR-0003 — One Offline Run-Bound Evidence Manifest Core

**Status:** Accepted
**Date:** 2026-08-15

## Context

Broad artifact directories, empty trace databases, unrelated failed logs, and nearby Git identities cannot prove a specific run or candidate. SSSF needs a deterministic evidence interchange core before runtime acceptance can depend on one. That core must remain offline and must not add credentials or imply authenticity from a content hash.

## Decision

`tools/evidence_manifest.py` is the sole owner of evidence-manifest v1 schema, canonical serialization, and validation.

V1 binds exact repository/base/candidate/branch/worktree, run and optional ADW identity, purpose, terminal outcome, required phases/dimensions, and a nonempty checked artifact inventory. Qualifying and diagnostic artifacts are distinct. External expected identity is required at validation, artifacts are frozen and hashed before parsing, and results are `observed-good`, `observed-bad`, or CNO.

Unknown versions and implicit migrations are refused. SHA-256 is used only for repository-owned content mismatch detection. Signing and key management are out of scope.

## Consequences

Positive:

- empty, unrelated, cross-candidate, diagnostic-only, and tampered evidence cannot qualify;
- canonical bytes remove duplicate and reorder ambiguity;
- the validator works without providers, network access, sandboxes, or credentials;
- retained diagnostics remain inspectable without becoming acceptance evidence.

Cost:

- producers must supply exact external identity and canonical bytes;
- missing or unknown-version evidence stays CNO;
- a future schema requires an explicit owner change and migration decision.

## Rejected alternatives

### Infer acceptance from existing directories or databases

Rejected because existence and schema-only databases are vacuous and do not bind a run/candidate.

### Treat all retained artifacts as qualifying

Rejected because failed and diagnostic artifacts would contaminate acceptance.

### Sign manifests in this increment

Rejected because no existing signing owner supplies that identity and new keys would create an unauthorized credential surface.

### Integrate runtime acceptance now

Rejected because HD-09 owns adoption after the prerequisite runtime and custody interfaces exist.
