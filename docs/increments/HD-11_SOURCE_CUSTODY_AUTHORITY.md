# HD-11 — Source Custody Authority

**Status:** PROVEN
**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`

## Problem

`docs/architecture/REPOSITORY_OWNERSHIP.md` opened with a "Current baseline behavior" section claiming that the `fill` lifecycle recipe clones a hard-coded public upstream repository, and closed by repeating that "the current FILL implementation still clones Disler's repository".

Neither statement described the code. B2-002 removed the hard-coded clone authority: FILL derives the sandbox source from the host checkout's `origin`, resolves an exact committed revision, creates the run branch, gates guest `HEAD`, and persists provenance. `docs/architecture/SANDBOX_LIFECYCLE.md`, the B2-002 increment, its tracked run record, `docs/validation/check_sandbox_source_contract.py`, and the recipe itself were all already current. The ownership document was the only thing that was wrong.

The smallest counterfactual is direct: the document's baseline claim and the recipe's origin derivation cannot both describe current behavior.

A reader who trusts the document concludes that current sandboxes execute upstream code, and may then invent duplicate environment variables or bypass the proven FILL path.

The source audit that surfaced this cited the recipe as `fill.just` at the repository root. It is at `just/sandbox/lifecycle/fill.just`. A citation a reader cannot follow is not evidence, which is why followability is now itself an enforced property.

## Desired outcome

`docs/architecture/REPOSITORY_OWNERSHIP.md` is authoritative and current, points at the executable authority and the tracked proof, and cannot silently drift away from the code again.

## Implementation

- Rewrote `docs/architecture/REPOSITORY_OWNERSHIP.md`: removed the obsolete baseline and required-post-baseline-increment text, stated present FILL/SETUP/HARVEST behavior, and added a contract table binding each element to the file and exact token that owns it.
- Preserved the B2-001 canonical remote roles verbatim. They were correct and were named as disconfirming evidence in the audit; they were re-checked against `docs/validation/check_repository_ownership.py`, the configured `origin`, the `increment/*` branches, and the `sssf-*` tags before being kept.
- Added `docs/validation/check_source_custody_authority.py`.
- Enumerated it in `ci/checks.json` and `docs/validation/check_ci_contract.py`, so the ordinary pull-request and `main`-push gate runs it on Linux and Windows.

Historical increment records were not edited. B2-002 describes what was true at the time and remains untouched.

## What the validator asserts

It reads the document and the code together, offline — file bytes only, no network, no git, no subprocess.

- Every contract row must cite a file that exists. Recipe rows are verified by bounded recognizers for the operative assignment or conditional and its refusing exit path after comments and literal-false blocks are removed; duplicate rows are malformed.
- The required row set is derived from the code: the persisted provenance names come out of the `"$RR" set` write in `just/sandbox/lifecycle/fill.just` and are cross-checked against `FIELDS` in `sandbox_mount/host/run_record.py`. Renaming a field in the code turns the document red; naming a field the code does not persist turns it red the other way.
- Canonical and upstream URLs in the document must equal the values `docs/validation/check_repository_ownership.py` declares. Any third repository is refused.
- No claim about what the sandbox clones may name a repository, by URL literal or by the upstream owner's name, because the recipe names none. Claim extraction binds a colon lead-in to the block it introduces, which is exactly how the pre-HD-11 document attributed a hard-coded upstream URL to FILL across a blank line.
- The `origin` derivation must be stated in prose, not only tabulated.

- The remote roles are cited as enforcement, not vocabulary: the table binds them to the `origin != CANONICAL` and push-`DISABLED` assertions in the ownership validator, so a role claim cannot survive the code dropping the check that backs it.
- A missing or unparsable input, or a recipe row outside the accepted bounded syntax, is reported as could-not-observe by row name and is never narrowed into a pass. Structurally verified and unchecked rows are printed on green and red paths.

This implements the standing “discovery is not identity” and property-scoped completeness ruling from Browser Sol, captain-delegated authority, control issue 4 comment 5310771128, recorded at `data/captain-rulings-2026-08-17-discovery-is-not-identity.md`. Substring occurrence is used for exclusion, never as confirmation of a recipe acceptance predicate.

Acceptance covers canonical and upstream roles, the public clone restriction, the exact pin, the dirty-host rule, the guest branch and gate, the persisted fields, the SETUP recheck, and the harvest namespace — 22 reconciled elements.

## Watched-red controls

The first control was watched red against the **shipped** document before it was corrected, so the control is calibrated on the real present-day defect rather than a synthetic one:

`docs/evidence/hd11/pre-fix-hard-coded-upstream-red.txt`

The remaining controls copy the cited files into a throwaway root, mutate exactly one thing, and require a red result for a named reason:

`docs/evidence/hd11/watched-red-control-matrix.txt`

| Control | Must go red because |
| --- | --- |
| hard-coded-upstream | a clone claim names a repository |
| missing-fill-pointer | the FILL pointer is gone |
| missing-b2-002-pointer | the B2-002 pointer is gone |
| canonical-url-divergence | the document's canonical URL is not the code's |
| document-sha-field-divergence | the document renames a persisted SHA field |
| code-sha-field-divergence | the code renames it and the document does not follow |
| unfollowable-citation | a cited path cannot be opened |
| code-token-drift | a cited token no longer occurs in the cited file |
| comment-only-token | a token surviving only in a comment cannot confirm structure |
| dead-branch-token | a token surviving only in a literal-false block cannot confirm structure |
| duplicate-row | duplicated identity is rejected rather than resolved by position |
| unchecked-row | unrecognized bounded syntax is named and prevents satisfaction |

The unmutated copy stays green and provides the genuine-operative non-vacuity control. Two further controls, run by hand and recorded in the same matrix, delete the document and delete a code authority: both are reported as could-not-observe rather than as a pass or a crash.

## Static acceptance evidence

`python3 docs/validation/check_source_custody_authority.py`

Result: `HD-11 source custody authority: PASS` — 22 contract elements reconciled, eight watched-red controls plus the non-vacuity control.

`python3 docs/validation/check_ci_contract.py`

Result: `B4-001 deterministic CI contract: PASS` — 9 offline checks enumerated.

`python3 tools/ci_gate.py run`

On this host: `source-custody-authority-validator` observed-good, alongside seven other observed-good checks.

## Could-not-observe

`just` is not installed on the authoring host, so `inkwell-unit-tests` returned could-not-observe and `sqlite-free-observability-validator` returned observed-bad on a `FileNotFoundError` for `just` rather than a typed refusal. Both are host-environment gaps that predate this increment and are unrelated to the document or the validator; the deterministic CI job installs `just` and executes them. That `check_obs_query.py` raises instead of returning a typed could-not-observe when its tool is absent is a real, separate defect and is recorded here rather than repaired under a documentation increment.

Live sandbox behavior was not exercised. This increment changed no recipe, no lifecycle, and no sandbox behavior, so no live proof was required or claimed.

## Non-goals

- Change FILL, SETUP, HARVEST, or any sandbox behavior.
- Change the run-record schema.
- Rewrite historical increment records.
- Touch the CLI-lane audit or any other increment's documents.

## Result

HD-11 is proven. The source-custody record is current, its citations can be followed, and a deterministic control on the ordinary CI gate turns red if the document and the code stop agreeing.
