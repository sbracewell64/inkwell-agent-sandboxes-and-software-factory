# HD-08 — Offline Evidence Manifest Core

**Status:** PROVEN
**Starts from:** `04e5484a6190f033d25e1626b96a4cca93b7f755`

## Problem

SSSF had no general nonempty manifest binding evidence to one repository candidate, run, optional ADW, phase, purpose, terminal result, and acceptance dimension. Broad artifact directories, schema-only databases, and unrelated failed logs could be mistaken for proof.

## Desired outcome

Provide one provider-independent schema/serializer/validator owner with canonical bytes, offline artifact verification, three-valued outcomes, qualifying-vs-diagnostic separation, fixtures, and watched-red controls.

## Non-goals

- no runtime, ADW completion, sandbox, export, or acceptance integration (HD-09);
- no provider execution, credential, signing, or key surface;
- no changes to PR 1, B3-005 records, sandboxes, canonical installation, proof clones, DSH, migration, or expansion;
- no claim that repository-owned hashes establish cryptographic identity or authenticity.

## Files / boundaries in scope

- owner: `tools/evidence_manifest.py`;
- deterministic validator: `docs/validation/check_evidence_manifest.py`;
- positive fixture: `docs/validation/fixtures/evidence_manifest/positive/`;
- contract and rationale: `docs/reference/EVIDENCE_MANIFEST.md` and ADR-0003;
- ledger/proof/reference routing updates.

## Design

The v1 manifest uses exact external validation context rather than trusting self-declared identity. Nonempty, sorted requirements and inventory eliminate vacuous PASS. Each item repeats run, optional ADW, phase, purpose, producer, terminal outcome, class, and claimed dimensions. Diagnostic items are checked but cannot claim a dimension. Qualifying items count only after identity, terminal, path, bytes, hash, and type checks succeed.

Canonical UTF-8 JSON and strict ordering/sequence rules reject duplicate or identity-preserving reorder ambiguity. Artifact reads open the root, every intermediate directory, and the final regular file through descriptor-relative no-follow operations; they compare descriptor identity and freeze bytes before hashing and parsing. Unsupported descriptor primitives or changed identity are CNO, never a weaker pathname fallback. Unknown versions refuse implicit migration as CNO.

## Risks / failure modes

- Missing/unreadable/empty evidence or an unknown version is CNO, never PASS.
- Deterministic identity/hash/schema/path contradictions are observed-bad.
- A qualifying schema-only SQLite database is CNO.
- SHA-256 detects content mismatch only; it is not signing/authentication.
- V1 validity does not authorize runtime acceptance.

## Acceptance

### Deterministic checks

```text
python3 docs/validation/check_evidence_manifest.py
python3 tools/evidence_manifest.py validate ...positive fixture and exact context...
python3 -m compileall -q tools/evidence_manifest.py docs/validation/check_evidence_manifest.py
```

The controls cover positive canonical round-trip, complete offline hash inventory, and a bound SQLite ADW session plus empty directory/database/manifest/inventory, wrong run/ADW/repository/base/candidate/branch/worktree role/phase, unrelated database/session and failed item, diagnostics only, tamper, missing phase/dimension, duplicates/reorder, traversal/symlink, malformed/duplicate-key/noncanonical JSON, and unknown version.

### Semantic review

Independent review is delegated to the required no-mistakes pipeline before publication.

## Evidence

- sandbox run: not applicable; offline core only
- ADW: not applicable
- fixture: `docs/validation/fixtures/evidence_manifest/positive/manifest.json`
- pre-fix watched-red capture: `docs/evidence/hd08/intermediate-directory-symlink-swap-red.txt`, bound to `7148f45b5e906e4fcf220d7c9d32212f6fae985a`
- pre-fix wrong-phase coverage capture: `docs/evidence/hd08/wrong-phase-control-red-73d8a831.txt`, bound to `73d8a8313f3a9b70edbba42a9e8862d0e7feb164`
- supplemental content-addressed capture: `docs/evidence/hd08/intermediate-component-tocttou-red-e10712b9ed01.txt`, bound to defective program digest `e10712b9ed01f400731798338ed99ad87cf76bf0069963c2e11280dc0b4cf53e` derived from `tools/evidence_manifest.py` digest `445acc4f2d0a8a59fd3543d5591ca810d72c8864cb88005aa85951e5f89b6687`
- test result: validator prints `HD-08 evidence manifest controls: PASS`, `wrong-phase-control: PASS`, `intermediate-directory-symlink-swap: PASS`, and `intermediate-component-tocttou-control: PASS`

## Documentation changed

Reference contract, ADR-0003, increment ledger, proof matrix, file map, command reference, and documentation router.

## Result

The offline manifest core is deterministic and nonvacuous. It remains intentionally disconnected from runtime acceptance.

## Follow-ups

HD-09 may integrate this owner only after its dependencies are proven. It must not infer acceptance from legacy directories or empty databases.
