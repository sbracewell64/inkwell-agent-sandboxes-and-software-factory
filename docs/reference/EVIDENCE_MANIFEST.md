# Offline Evidence Manifest v1

## Scope

HD-08 defines the offline, run-bound evidence-manifest core. It does **not** integrate manifests into ADW completion, sandbox lifecycle, export, or runtime acceptance. A valid v1 manifest is an observed-good statement about the bounded files checked by this validator; it does not authorize acceptance. HD-09 owns that later transition.

The sole executable owner is `tools/evidence_manifest.py`. It owns:

- the `sssf.evidence-manifest.v1` schema and `schema` projection;
- canonical JSON serialization;
- external-context and artifact validation;
- the three-valued result.

Do not create a second serializer or infer this schema from broad artifact directories, trace databases, or narrative proof records.

## Identity and evidence fields

A manifest contains exactly:

- `schema_version`;
- `repository`: canonical HTTPS URL, exact lowercase 40-character base and candidate Git SHA, branch, and worktree role;
- `run`: run ID, ADW ID or explicit `null` when no ADW applies, and terminal outcome;
- one purpose token;
- nonempty sorted `required_phases` and `required_dimensions`;
- a nonempty, path-sorted `inventory`.

Every inventory item binds a zero-based sequence, normalized relative artifact path, artifact type, byte length, SHA-256, producer, run ID, ADW ID, phase, purpose, terminal outcome, evidence class, and sorted claimed acceptance dimensions. The run/ADW/purpose identities on an item must equal the manifest identity. External expected repository, source, branch/worktree, run, ADW, purpose, phase, and dimension values are mandatory validator inputs, so a self-consistent manifest for the wrong candidate cannot qualify.

`evidence_class` is either:

- `qualifying`: terminal outcome must be `succeeded`, claims at least one declared dimension, and may satisfy required phase/dimension coverage only after its bytes and type validate;
- `diagnostic`: retained and hash-checked, but must claim no acceptance dimension and never contributes to qualification.

Unlisted nearby files and unrelated failed runs have no effect. A failed or cross-run item cannot satisfy another candidate, run, ADW, phase, or dimension. Every declared required phase and every declared required dimension needs at least one verified qualifying item. The checked inventory itself must be nonempty.

## Canonical bytes and paths

Canonical manifest bytes are UTF-8 JSON with:

- object keys sorted lexicographically;
- no insignificant whitespace;
- no NaN/infinity;
- one final LF.

Arrays that carry identities are sorted and duplicate-free. Inventory order is canonical path order, with `sequence` equal to the zero-based position. Reorder, duplicate paths, duplicate JSON keys, or noncanonical bytes are observed-bad rather than silently normalized.

Artifact paths are normalized relative POSIX paths. Absolute paths, `..`, backslashes, symlinks in any path component, non-regular files, and escapes from the supplied artifact root are refused.

## Freeze-before-parse rule

For each artifact the validator opens a regular file without following a final symlink, reads it once, and compares file identity/size/timestamps before and after the read. The resulting in-memory bytes are the frozen snapshot. SHA-256 and byte length are checked before any JSON, JSONL, text, or SQLite parsing. Parsing never reopens the source artifact. SQLite is parsed from a temporary immutable snapshot; a qualifying SQLite database must contain at least one user-table row and positively find the manifest ADW ID in an `adw_id` column (or the run ID in a `run_id` column when no ADW applies). A schema-only or unrelated-session database is CNO.

SHA-256 here is repository-owned mismatch/tamper detection. It is not a signature, identity proof, credential, or authenticity claim. V1 adds no keys or signing surface.

## Three-valued result

- `observed-good`: canonical known-v1 manifest, exact external identity, nonempty checked inventory, all hashes/types valid offline, successful qualifying evidence, and complete required phase/dimension coverage.
- `observed-bad`: deterministic contradiction such as wrong identity, malformed known schema/artifact, tamper/hash mismatch, duplicate/reorder ambiguity, failed qualifying item, or path/symlink escape.
- `could-not-observe` (CNO): missing, empty, unreadable, or unstable required evidence; empty/schema-only qualifying database; diagnostic-only coverage; absent required phase/dimension; or unknown schema version.

Observed-bad takes precedence when both a contradiction and an absence are found. Neither nonzero inventory directory contents nor an empty database is inferred as PASS.

CLI exit codes are `0` observed-good, `1` observed-bad, and `2` CNO. Callers must also read the printed observation and must not collapse CNO into PASS or FAIL.

## Version and migration refusal

V1 accepts only the exact `sssf.evidence-manifest.v1` version. Unknown, older, or future versions are CNO. There is no implicit upgrade, field defaulting, or migration by directory inspection. A future version requires an explicit schema/serializer/validator change and a separately reviewed converter if migration is authorized; v1 continues to refuse bytes it does not own.

## Commands

Print the generated schema projection:

```text
python3 tools/evidence_manifest.py schema
```

Run all positive fixtures and watched-red controls:

```text
python3 docs/validation/check_evidence_manifest.py
```

The full validation CLI requires `--manifest`, `--artifact-root`, repository/base/candidate/branch/worktree/run/purpose identity, at least one `--require-phase`, and at least one `--require-dimension`; pass `--adw-id` only where an ADW applies. See `python3 tools/evidence_manifest.py validate --help`.
