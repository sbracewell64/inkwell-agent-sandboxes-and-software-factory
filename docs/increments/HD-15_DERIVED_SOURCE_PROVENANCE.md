# HD-15 — Preventive exact-provenance contract for derived source

**Status:** PROVEN

**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`

## Problem

A future hardening or migration commit could copy design or source from an
assessment workspace without recording its exact input. Git records the
destination diff but not the source workspace, commit, tree, license, or
caveat, so a later reader cannot distinguish independent repair from imported
work, or learn the limitations that came with it.

The smallest counterfactual: copy a derived module in as an ordinary feature
commit, and nothing in the repository records where it came from.

## Desired outcome

Before any assessment-derived source can enter, a contract exists that binds
every derived file range to an immutable input and to a destination commit and
diff, refuses any claim that exceeds its input proof, and keeps the
`OVERALL_B3_NOT_COMPLETE` could-not-observe caveat visible.

## Non-goals

This increment is a gate, not a door.

- No migration is authorised, and none was performed.
- No importer, migration scaffolding, or import path was created.
- No source was derived, copied, or transcribed from any workspace.
- No SSSF source is certified clean; there is nothing to certify.

## Files / boundaries in scope

- `docs/reference/DERIVED_SOURCE_PROVENANCE.md` — the contract and template.
- `docs/provenance/derived_source/README.md` — the record registry, empty.
- `docs/validation/check_derived_source_provenance.py` — the sole enforcer.
- `ci/checks.json` and `docs/validation/check_ci_contract.py` — gate wiring.

## Design

The validator reports two separate results and never collapses them.

The **contract state** (first printed line, and the process exit code) says
whether the gate itself is installed, structurally sound, and demonstrably
red-capable.

The **population verdict** (second printed line) is four-valued —
`FAIL`, `CANNOT_OBSERVE`, `NOT_APPLICABLE`, `PASS` — with precedence
`FAIL > CANNOT_OBSERVE > NOT_APPLICABLE > PASS`. An incomplete universe never
masks a real violation, and an empty universe never becomes a certification.

Two standing laws are enforced directly in code.

*Absence is not a pass.* With no derived source present the population verdict
is `NOT_APPLICABLE`, a form of could-not-observe. The validator prints the size
of the universe it enumerated, so "we checked and there is none" is
distinguishable from "we did not look" (`CANNOT_OBSERVE`) and from "there is
derived source and it complies" (`PASS`).

*Discovery is not identity.* Every identity field must be exact lowercase hex.
A branch name, a tag name, or a path that merely looks like an input is refused
even when the name resolves to the correct object. The calibration input
repository deliberately carries a branch `assessment/hardening-source` and a
tag `assessment-v1` pointing at the correct commit; the watched-red control
proves both are still refused, and the negative control below proves they would
otherwise have been accepted.

Verification is against bytes, never against field presence. The retained
immutable input is a Git bundle; the validator resolves it into a throwaway
repository and walks commit to tree to blob to bytes, recomputing every
recorded hash. A field that nothing verifies is prose with punctuation.

Every derived file carries the literal marker `SSSF-DERIVED-SOURCE` in its own
bytes. A tracked file bearing the marker that no record claims is a violation.
Only this document and the contract reference are permitted to carry the marker
while teaching it, and the validator refuses if either stops doing so.

## Risks / failure modes

- A future reader mistakes a green check for certification of derived source.
  Mitigated by the separate population verdict line, the explicit
  `NOT_APPLICABLE` note the validator prints, the registry README, and the
  `NOT APPLICABLE — CNO` rows in `docs/baseline/PROOF_MATRIX.md`.
- A real future import ships no immutable input. That is `CANNOT_OBSERVE`, and
  `CANNOT_OBSERVE` is red, so the gate cannot be satisfied by an unverifiable
  claim.
- The pinned calibration object identities stop reproducing on some host. That
  is reported as a calibration failure naming the observed identities, not
  silently skipped.

## Acceptance

Every derived file range maps to an immutable input and to a destination commit
and diff; no claim exceeds its input proof; the B3 could-not-observe caveat
remains visible; and absence reports `NOT_APPLICABLE`, never a pass.

### Deterministic checks

`python docs/validation/check_derived_source_provenance.py`

The calibration harness materialises a throwaway assessment input repository
from pinned Git object identities, bundles it, and drives a throwaway
destination repository through three states — before the derived source exists,
after it lands unrecorded, and after an honest record is committed. These
fixtures are calibration-only; they construct synthetic content in temporary
directories and are not an import path.

Thirty-six controls are watched. Twenty-seven of them are refusals, including
the six the audit required. Pipeline custody fixes during review added the
external-bundle, filename-identity, and symlink-bundle refusals plus the
worktree-isolation green control. The range-completeness ruling added three
refusals and two green-side controls. The count describes the executable suite;
the additions are named because a changed count without an account of what
changed is not independently checkable:

1. a record missing the exact source commit fails;
2. a record missing the exact source tree fails;
3. a record whose only provenance is a branch name fails;
4. a record whose only provenance is a tag name fails;
5. a record missing the `OVERALL_B3_NOT_COMPLETE` caveat fails;
6. a derived range wider than the input range it cites fails;
7. an input range citing lines beyond the proven input fails;
8. a marked file with a derived region outside every declaration fails as an
   uncovered-line violation;
9. any gap in the combined derived and non-derived ranges fails;
10. a non-derived declaration overlapping a derived range fails;
11. a tampered input content hash fails;
12. an input tree not carried by the claimed commit fails;
13. an input commit absent from the retained input fails;
14. a source path absent from the claimed tree fails;
15. a tampered input slice hash fails;
16. a tampered destination hash fails;
17. a base blob not matching the destination diff fails;
18. a base that is not an ancestor of head fails;
19. a recorded derived file that lacks the marker fails;
20. a recorded file unchanged between base and head fails;
21. an untracked destination path fails;
22. a tampered license notice hash fails;
23. a placeholder custody value fails;
24. an immutable input path that is not retained in `HEAD` fails;
25. an external-bundle path fails;
26. a symlink-bundle path fails;
27. a filename-identity mismatch between the record ID and JSON filename fails.

The remaining nine are the separately implemented green-side controls. This
taxonomy names how the controls are implemented, not which verdict they expect:

28. absence of any derived source is `NOT_APPLICABLE`, not a pass;
29. a marked tracked file that no record claims fails;
30. a complete, honest record passes, and the positive control additionally
    requires that at least three byte-level bindings were actually verified;
31. a precedence control commits one violating record alongside one
    unverifiable record and requires the result to be `FAIL` while the
    could-not-observe finding is still reported;
32. a contract document that stops teaching the marker fails;
33. a restoration control requires the honest record to still pass after the
    whole mutation sweep, so no control leaves the fixture permanently red;
34. a worktree-isolation control replaces the checked-out bundle and requires
    the retained `HEAD` bytes to remain authoritative;
35. a complete honest derived/non-derived partition passes independently;
36. an unmarked file reports `NOT_APPLICABLE`, not verified independence.

### Semantic review, if required

Not required. Every claim above is decided by executable code.

## Evidence

- sandbox run: none; this increment performs no provider execution.
- ADW: none.
- commits: see the pull request for this branch.
- logs/artifacts: `docs/evidence/hd15/watched-red-control-matrix.txt`,
  `docs/evidence/hd15/absence-is-not-a-pass.txt`.
- test results: `docs/validation/check_derived_source_provenance.py` reports
  `PASS` for the contract with a `NOT_APPLICABLE` population.

Five independent negative controls were run against deliberately defective
copies of the validator, and each was watched red before the real check was
trusted: weakening exact-identity matching accepted the branch and tag names;
substituting recorded hashes for recomputed ones accepted a tampered input and
broke the precedence control; removing the extent arithmetic accepted a claim
exceeding its input proof; rounding the empty universe to `PASS` was caught by
the absence control; and removing partition enforcement accepted uncovered and
contradictory declarations. Full output is retained in
`docs/evidence/hd15/watched-red-control-matrix.txt`.

## Documentation changed

- `docs/README.md`, `docs/reference/DERIVED_SOURCE_PROVENANCE.md`,
  `docs/reference/COMMANDS.md`, `docs/reference/FILE_MAP.md`,
  `docs/baseline/INCREMENT_LEDGER.md`, `docs/baseline/PROOF_MATRIX.md`,
  `docs/development/TEST_STRATEGY.md`, `TREE.md`.

## Result

The contract and its enforcer are installed and demonstrably red-capable.

The derived-source population is **`NOT_APPLICABLE` — could-not-observe**. The
repository search found no SSSF source identified as migration-derived, and no
such commits or branches. Nothing is certified clean, because there is nothing
to certify.

## Follow-ups

None required. If a migration is ever authorised — it is not authorised now —
it must satisfy this contract, including shipping its immutable input, before
the gate can report anything other than `CANNOT_OBSERVE`.
