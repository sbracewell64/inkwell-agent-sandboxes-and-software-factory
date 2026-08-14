# B3-002 — Repository Line-Ending Contract

**Status:** IN_PROGRESS
**Starts from:** `sssf-b3-001-windows-portability-baseline`

## Problem

B3-001 proved that the repository did not own its line-ending behavior.

The Windows host has:

`core.autocrlf=true`

and the repository previously had no `.gitattributes`.

The Git index already stored representative source files as LF, but the Windows working tree materialized many tracked text files as CRLF.

This included every tracked `.just` file and all tracked `.sh` files.

Execution-sensitive source therefore depended on operator-level Git configuration instead of repository-owned policy.

## Desired outcome

Make line-ending behavior deterministic from repository state.

All files Git classifies as text should:

- be normalized as LF in the index;
- be checked out as LF on every platform;
- remain LF even when the Windows host has `core.autocrlf=true`.

Binary files remain subject to Git's normal binary detection rather than being forced through text conversion.

## Policy

The repository-owned policy is:

`* text=auto eol=lf`

Meaning:

- `text=auto` lets Git distinguish text from binary content;
- text content is normalized in Git;
- `eol=lf` materializes text files with LF working-tree line endings;
- host-global `core.autocrlf` no longer decides repository text-file line endings.

## Why the policy is repository-wide

The B3-001/B3-002 inventory found CRLF working-tree materialization across far more than shell files.

Affected text classes included:

- `.just`
- `.sh`
- `.py`
- `.md`
- `.json`
- `.yaml`
- `.ts`
- `.css`
- `.html`
- other text assets

Limiting the policy only to shell files would preserve the underlying portability ambiguity for the rest of the repository.

A single repository-wide text rule is smaller and more deterministic than maintaining a growing extension list.

## Windows-native scripts

At B3-002 start, the repository contained no tracked:

- `.bat`
- `.cmd`
- `.ps1`

files.

No CRLF exception is introduced speculatively.

If a future Windows-native file genuinely requires CRLF, that requirement must be added explicitly and proven when the file is introduced.

## Existing defensive runtime handling

B3-002 does not remove the previously proven CR-stripping protection in the sandbox lifecycle.

Repository line-ending policy prevents one source of CRLF materialization, but the defensive runtime normalization protects a separate process-boundary condition.

Removing it would require independent evidence and is outside this increment.

## Implementation

B3-002 adds:

- repository-root `.gitattributes`;
- `docs/validation/check_line_endings.py`;
- this increment record.

The validator checks:

- the effective repository policy;
- effective Git attributes on representative files;
- LF index state;
- optionally, LF working-tree state for fresh-checkout proof.

## Renormalization proof

Before the candidate commit:

`git add --renormalize .`

produced no modifications to existing tracked files.

This proves the existing Git index was already normalized and the new policy did not create a mass source rewrite.

## First candidate

The first candidate commit was:

`51dd23c01328a013aa6df3ed8bfcde170d377632`

The line-ending behavior itself passed a fresh Windows checkout proof with:

`core.autocrlf=true`

Observed representative files reported:

`i/lf w/lf attr/text=auto eol=lf`

and the fresh checkout was clean.

However, that candidate is not accepted as the final B3-002 closure candidate because its staged hygiene gate reported:

`docs/increments/B3-002_LINE_ENDING_CONTRACT.md:306: new blank line at EOF.`

The commit was made despite that failed check.

Inspection also showed that the Markdown record had been saved with escaped Markdown syntax and excessive blank lines.

Because B3-002 had not been tagged or advanced to canonical `main`, these candidate-artifact defects are being corrected within B3-002 rather than hidden or repaired in a later increment.

The first candidate remains part of Git history and remains useful evidence that the semantic line-ending policy worked.

## Corrected candidate strategy

After correcting the candidate artifacts:

1. `git diff --check` must pass before commit.
2. The validator must pass.
3. The corrected candidate must be committed and pushed.
4. A second fresh Windows checkout must be made with `core.autocrlf=true`.
5. The strict validator must require LF working-tree state.
6. Representative execution-sensitive files must report `i/lf` and `w/lf`.
7. The second fresh checkout must be clean.

The corrected candidate SHA will become the final runtime-independent proof target for B3-002.

## Non-goals

- Change runtime semantics.
- Rewrite unrelated source files.
- Remove existing CR defensive handling.
- Modify the user's global Git configuration.
- Add Windows bootstrap behavior.
- Fix host observability.
- Replace exe.dev.
- Introduce Windows-native scripts.
- Add speculative CRLF exceptions.

## Acceptance

1. `.gitattributes` defines `* text=auto eol=lf`.
2. Representative `.just`, `.sh`, `.py`, and documentation files resolve `text=auto` and `eol=lf`.
3. Existing representative index content remains LF.
4. Renormalization produces no unrelated mass source diff.
5. A fresh Windows checkout made with `core.autocrlf=true` materializes representative text files as LF.
6. The fresh checkout is clean.
7. Existing lifecycle compatibility protections remain present.
8. No global Git configuration is modified.
9. `git diff --check` passes before the corrected candidate is committed.
10. Documentation and validator source are valid UTF-8.
11. B3-001's immutable tag remains unchanged.
12. The failed hygiene check on the first candidate remains explicitly recorded.

## Evidence

Semantic line-ending policy proof: PASS on first candidate.

Corrected candidate hygiene and second fresh-checkout proof: pending.

## Result

Pending corrected candidate proof.