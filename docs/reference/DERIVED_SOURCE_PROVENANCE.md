# Derived-source provenance contract v1

This is a preventive gate. It authorises no migration, describes no import
procedure, and creates no path that makes importing derived source easier. It
exists so that **if** assessment-derived source ever enters this repository, the
exact input that produced it is bound to immutable Git objects and verified
against bytes before the change can go green.

No SSSF source is currently identified as migration-derived. No migration is
authorised. Beginning one is out of scope for this contract.

## Scope

A file is **derived source** when any part of it was copied, transcribed, or
adapted from a workspace outside this repository's own history. Git records the
destination diff but not the source workspace, commit, tree, license, or
caveat, so without this contract a later reader cannot distinguish independent
repair from imported work, nor learn the limitations that came with it.

## Owner

`docs/validation/check_derived_source_provenance.py` is the sole enforcer. It
is enumerated in `ci/checks.json` and pinned in
`docs/validation/check_ci_contract.py`. There is no second validator and no
second schema.

## The two standing laws

**Absence is not a pass.** When the enumerated universe holds no derived
source, the population verdict is `NOT_APPLICABLE` — a form of
could-not-observe — and is never reported, ranked, or documented as `PASS`.
Zero findings is cleanliness only within a stated universe. The validator
prints the size of the universe it enumerated so a reader can tell "we checked
and there is none" (`NOT_APPLICABLE`) from "we did not look"
(`CANNOT_OBSERVE`) from "there is derived source and it complies" (`PASS`).

**Discovery is not identity.** A branch name, a tag name, a path that looks
like an input, or a commit message that mentions one identifies a *candidate*
and establishes nothing. Only an exact commit, tree, and content hash resolved
against a retained immutable input binds a claim. Name-shaped provenance is
refused even when the name happens to resolve to the correct object, so every
identity field must be exact lowercase hex — 40 characters for a Git object, 64
for a SHA-256 content hash.

## Precedence

`FAIL` > `CANNOT_OBSERVE` > `NOT_APPLICABLE` > `PASS`.

An incomplete universe never masks a real violation, and an empty universe
never becomes a certification.

## Marker

Every derived file must carry the literal token `SSSF-DERIVED-SOURCE` in its
own bytes, so a reader of the file learns it is derived without consulting an
index. A tracked file that carries the marker but is claimed by no record is a
violation: an unrecorded derived file is indistinguishable from independent
repair. This document and `docs/increments/HD-15_DERIVED_SOURCE_PROVENANCE.md`
are the only files permitted to carry the marker while teaching it, and the
validator refuses if either one stops doing so, because a silently reworded
document would leave the marker scan unanchored.

## Records

One record per derived input, stored as
`docs/provenance/derived_source/<record-id>.json`. The registry is empty today
and its emptiness is `NOT_APPLICABLE`, not a pass.

### Required fields

| Field | Meaning |
|---|---|
| `schema_version` | exactly `sssf.derived-source-provenance.v1` |
| `record_id` | kebab-case slug matching the file name |
| `caveats` | must contain `OVERALL_B3_NOT_COMPLETE` |
| `input.source_repository` | the source workspace this input came from |
| `input.source_path` | the path of the input inside that workspace |
| `input.commit` | exact 40-hex commit of the input |
| `input.tree` | exact 40-hex tree of that commit |
| `input.blob` | exact 40-hex blob of the input file in that tree |
| `input.content_sha256` | SHA-256 of the input bytes |
| `input.content_bytes` | byte length of the input |
| `input.immutable_input` | `{"kind": "git-bundle", "path": "<tracked bundle>"}` |
| `extraction.method` | `verbatim-copy`, `transcribed`, or `adapted` |
| `extraction.performed_by` | who performed the extraction |
| `extraction.custody` | where the retained input is held |
| `license.identifier` | SPDX identifier governing the input |
| `license.notice_path` | tracked path of the retained notice |
| `license.notice_sha256` | SHA-256 of the notice bytes |
| `destination.repository` | this repository |
| `destination.base_commit` | exact 40-hex commit before the derived source landed |
| `destination.head_commit` | exact 40-hex commit that landed it |
| `destination.head_tree` | exact 40-hex tree of that head |
| `transformed_files[]` | one entry per derived destination file |
| `transformed_files[].non_derived_ranges` | ordered non-overlapping 1-based inclusive ranges claimed not to be derived; an empty list is valid only when derived ranges cover the whole file |

Each `transformed_files` entry carries `destination_path`,
`destination_blob`, `destination_sha256`, `base_blob` (`null` when the path is
absent at base), and a nonempty ordered `ranges` list. Each range carries
`derived_lines`, `destination_slice_sha256`, `input_lines`, and
`input_slice_sha256`. The entry also carries the required
`non_derived_ranges` list. Derived and non-derived ranges must form a complete,
non-overlapping partition of every line in the marked destination file.

Line ranges are 1-based and inclusive. A slice hash is the SHA-256 of the
selected lines concatenated, each terminated by a single LF.

An explicitly declared non-derived range is itself a claim. A false
non-derived claim is a lie this validator cannot catch; the declaration is a
human-authored trust boundary, not an independently inferred fact.

A validator cannot detect undeclared derivation, for the same reason it cannot
detect derivation at all. Only total coverage of a marked file is checkable.
An unmarked file remains out of scope and reports `NOT_APPLICABLE`; out of
scope is not clean and does not mean the file was verified independent.

## Acceptance

The validator resolves the retained bundle into a throwaway repository and
verifies, against bytes:

1. `input.commit` exists there and is a commit; `commit^{tree}` equals
   `input.tree`; `tree:source_path` equals `input.blob`; those blob bytes hash
   to `input.content_sha256` and are `input.content_bytes` long.
2. `destination.head_commit` and `base_commit` exist here, `head^{tree}` equals
   `head_tree`, base is a distinct ancestor of head, and head is reachable from
   the current `HEAD`.
3. Each `destination_path` is tracked, resolves at `head_tree` to
   `destination_blob`, hashes to `destination_sha256`, matches the working-tree
   copy byte for byte, differs from `base_blob`, and carries the marker.
4. `license.notice_path` resolves at `head_tree` and hashes to
   `license.notice_sha256`.
5. Every derived range lies inside the destination file, its bytes hash to
   `destination_slice_sha256`, its cited input range lies inside the proven
   input, and those bytes hash to `input_slice_sha256`.
6. **No claim exceeds its input proof**: a derived range may not span more
   lines than the input range it cites, and an input range may not cite lines
   beyond the proven input.
7. Derived ranges plus explicitly declared non-derived ranges cover every line
   of each marked destination exactly once. An uncovered line or overlap is a
   violation.

A recorded hash or immutable identity that is not verified is prose with
punctuation. The input and destination identities, hashes, byte length, paths,
and range extents above are checked against retained Git objects and bytes; the
remaining custody and classification fields are structurally validated. The
byte-level bindings are calibrated by controls watched failing first.

## Refusals

An absent or unusable bundle is `CANNOT_OBSERVE`, never a pass: a claim whose
input is not retained cannot be verified, so a real future import must ship its
immutable input for this gate to go green. A tracked file that cannot be read,
and a universe that cannot be enumerated, are likewise `CANNOT_OBSERVE`.

## Template

Copy this skeleton and replace every `<...>` placeholder. The template is
deliberately rejected by the validator while placeholders remain, so it can
never be committed as a real record.

```json
{
  "schema_version": "sssf.derived-source-provenance.v1",
  "record_id": "<kebab-case-record-id>",
  "caveats": ["OVERALL_B3_NOT_COMPLETE"],
  "input": {
    "source_repository": "<source workspace repository>",
    "source_path": "<path inside the source workspace>",
    "commit": "<40-hex commit>",
    "tree": "<40-hex tree>",
    "blob": "<40-hex blob>",
    "content_sha256": "<64-hex sha256 of the input bytes>",
    "content_bytes": 1,
    "immutable_input": {
      "kind": "git-bundle",
      "path": "<tracked path of the retained bundle>"
    }
  },
  "extraction": {
    "method": "verbatim-copy",
    "performed_by": "<who performed the extraction>",
    "custody": "<where the retained input is held>"
  },
  "license": {
    "identifier": "<SPDX identifier>",
    "notice_path": "<tracked path of the retained notice>",
    "notice_sha256": "<64-hex sha256 of the notice bytes>"
  },
  "destination": {
    "repository": "<this repository>",
    "base_commit": "<40-hex commit before the derived source landed>",
    "head_commit": "<40-hex commit that landed it>",
    "head_tree": "<40-hex tree of that head>"
  },
  "transformed_files": [
    {
      "destination_path": "<tracked destination path>",
      "destination_blob": "<40-hex blob at head>",
      "destination_sha256": "<64-hex sha256 of the destination bytes>",
      "base_blob": null,
      "ranges": [
        {
          "derived_lines": [1, 1],
          "destination_slice_sha256": "<64-hex sha256 of those destination lines>",
          "input_lines": [1, 1],
          "input_slice_sha256": "<64-hex sha256 of those input lines>"
        }
      ],
      "non_derived_ranges": []
    }
  ]
}
```

## Commands

```text
python docs/validation/check_derived_source_provenance.py
```

The first printed line is the contract state (`PASS`, `FAIL`, or `CNO`). The
second is the population verdict, which is a separate four-valued result and
must not be collapsed into the first. Today the population is
`NOT_APPLICABLE`: the universe was enumerated and holds no derived source, so
there is nothing to certify.
