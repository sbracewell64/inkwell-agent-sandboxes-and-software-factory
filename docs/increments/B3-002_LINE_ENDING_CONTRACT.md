# B3-002 — Repository Line-Ending Contract

**Status:** PROVEN
**Starts from:** `sssf-b3-001-windows-portability-baseline`
**Accepted candidate:** `090fbfffda88b9c0d17f63e663c83a1e0979a606`
**Proof date:** 2026-08-14

## Problem

B3-001 proved that the repository did not own its line-ending behavior.

The Windows host had:

`core.autocrlf=true`

while the repository had no `.gitattributes`.

The Git index already stored representative source files as LF, but the Windows working tree materialized many tracked text files as CRLF.

This included every tracked `.just` file and all tracked `.sh` files.

Execution-sensitive source therefore depended on operator-level Git configuration instead of repository-owned policy.

## Desired outcome

Make line-ending behavior deterministic from repository state.

All files Git classifies as text must:

- be normalized as LF in the index;
- be checked out as LF on every platform;
- remain LF even when the Windows host has `core.autocrlf=true`.

Binary files remain subject to Git's normal binary detection rather than being forced through text conversion.

## Repository policy

B3-002 establishes:

`* text=auto eol=lf`

Meaning:

- `text=auto` lets Git distinguish text from binary content;
- text content is normalized in Git;
- `eol=lf` materializes text files with LF working-tree line endings;
- host-global `core.autocrlf` no longer decides repository text-file line endings.

## Why the policy is repository-wide

The B3 inventory found CRLF working-tree materialization across many text classes, including:

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

Limiting the policy only to shell files would leave the underlying portability ambiguity in the remainder of the repository.

The repository-wide text rule is smaller and more deterministic than maintaining a growing extension list.

## Windows-native scripts

At B3-002 start, the repository contained no tracked:

- `.bat`
- `.cmd`
- `.ps1`

files.

No CRLF exception was introduced speculatively.

If a future Windows-native file genuinely requires CRLF, that requirement must be introduced explicitly and proven with that file.

## Existing defensive runtime handling

B3-002 does not remove the previously proven CR-stripping protection in the sandbox lifecycle.

Repository line-ending policy prevents one source of CRLF materialization, while the existing defensive normalization protects a separate process-boundary condition.

Removing that defensive handling would require independent evidence and is outside B3-002.

## Implementation

B3-002 adds:

- `.gitattributes`
- `docs/validation/check_line_endings.py`
- this increment record

The validator checks:

- the effective repository policy;
- effective Git attributes on representative files;
- LF index state;
- LF working-tree state for the strict fresh-checkout proof.

## HD-01 authority correction

A later current-state audit found that the original optional mode allowed an
older supported Windows working tree to retain CRLF while the default validator
and host doctor reported success. Policy, effective attributes, and index state
remained correctly LF; the defect was the masked working-tree state.

HD-01 makes the already-proven strict contract authoritative for every
supported working tree. Both the default validator behavior and the Windows
host doctor now require watched files to be `i/lf w/lf`. The exact supported
invocation is:

`python docs/validation/check_line_endings.py --require-worktree-lf`

`--require-worktree-lf` remains in the command to make the operator-facing
contract explicit, but omitting it no longer weakens validation. A CRLF or
wrong-attribute observation is `observed-bad`; missing or unreadable evidence
is `could-not-observe`. Neither can print PASS.

The validator never repairs a checkout as a side effect. After preserving local
work and confirming `git status --short` is empty, the explicit repair is:

`git checkout-index --force -- .gitattributes justfile just/sandbox/lifecycle/fill.just just/sandbox/lifecycle/setup.just sandbox_mount/guest/provision.sh sandbox_mount/host/run_record.py docs/baseline/PROOF_MATRIX.md`

That command re-materializes the watched files from, without modifying, the
index. The strict validator must then be rerun. The Windows installation
runbook owns the complete operator procedure.

## Renormalization proof

Before the first candidate commit:

`git add --renormalize .`

produced no modifications to existing tracked files.

The only changes remained the three newly introduced B3-002 files.

This proved that the existing Git index was already normalized to LF and that introducing the repository policy did not create an unrelated mass source rewrite.

## First candidate

The first candidate was:

`51dd23c01328a013aa6df3ed8bfcde170d377632`

Its semantic line-ending behavior passed a fresh Windows checkout proof with:

`core.autocrlf=true`

Representative execution-sensitive files reported:

`i/lf w/lf attr/text=auto eol=lf`

and the fresh checkout was clean.

However, the candidate was not accepted because:

`git diff --cached --check`

had reported:

`docs/increments/B3-002_LINE_ENDING_CONTRACT.md:306: new blank line at EOF.`

The commit was made despite that failed hygiene gate.

Inspection also showed that the Markdown increment record contained escaped Markdown syntax and excessive blank lines.

B3-002 had not been tagged and had not been advanced to canonical `main`, so these candidate-artifact defects were corrected inside the still-open increment.

The failed first candidate remains in Git history and remains recorded here rather than being hidden.

## Corrected candidate

The corrected candidate is:

`090fbfffda88b9c0d17f63e663c83a1e0979a606`

Before committing the correction:

`git diff --cached --check`

passed.

After committing:

`git show --check --oneline HEAD`

reported no whitespace defect.

The corrected candidate was pushed to:

`increment/b3-002-line-ending-contract`

Remote and local candidate SHAs both resolved to:

`090fbfffda88b9c0d17f63e663c83a1e0979a606`

## Independent fresh Windows checkout proof

A second, separate checkout was cloned from the corrected candidate into:

`E:\SSSF-B3-002-PROOF-2`

The proof checkout was explicitly configured with:

`core.autocrlf=true`

The proof checkout HEAD resolved to:

`090fbfffda88b9c0d17f63e663c83a1e0979a606`

The strict validator was run:

`python docs/validation/check_line_endings.py --require-worktree-lf`

Result:

`B3-002 line-ending contract: PASS`

It additionally reported:

- representative tracked text files have LF index state;
- representative working-tree files are LF;
- observed `core.autocrlf: true`.

Independent `git ls-files --eol` inspection showed:

`just/sandbox/lifecycle/fill.just`

`i/lf w/lf attr/text=auto eol=lf`

`just/sandbox/lifecycle/setup.just`

`i/lf w/lf attr/text=auto eol=lf`

`justfile`

`i/lf w/lf attr/text=auto eol=lf`

`sandbox_mount/guest/provision.sh`

`i/lf w/lf attr/text=auto eol=lf`

`sandbox_mount/host/run_record.py`

`i/lf w/lf attr/text=auto eol=lf`

`git status --short`

produced no output in the second proof checkout.

## Global configuration boundary

B3-002 did not modify the user's global Git configuration.

The fresh proof clone used a clone-local:

`core.autocrlf=true`

setting to prove that repository-owned attributes override the hostile Windows default.

## Acceptance

1. `.gitattributes` defines `* text=auto eol=lf`.
2. Representative `.just`, `.sh`, `.py`, and documentation files resolve `text=auto` and `eol=lf`.
3. Existing representative index content remains LF.
4. Renormalization produced no unrelated mass source diff.
5. A fresh Windows checkout with `core.autocrlf=true` materialized representative text files as LF.
6. The fresh checkout was clean.
7. Existing lifecycle compatibility protections remained unchanged.
8. No global Git configuration was modified.
9. The corrected candidate passed its whitespace gate before commit.
10. Documentation and validator source validated as UTF-8.
11. B3-001 remained frozen at `c46c7ba37b94b1926f2d7e4633f66bc305f1c84b`.
12. The failed hygiene gate on the first candidate remains explicitly recorded.

All B3-002 acceptance criteria are satisfied.

## Result

B3-002 establishes a repository-owned line-ending contract.

Windows checkout behavior for text source is no longer determined by the operator's global `core.autocrlf` setting.

The corrected candidate was independently proven in a fresh Windows checkout with `core.autocrlf=true`, while representative execution-sensitive files remained LF in both the index and working tree.

No existing source file required a content rewrite to establish the policy.

The original defensive Windows lifecycle protections remain intact.

**Result: PASS**

## Boundedness delta

```text
boundedness_delta: none
boundedness_reason: this increment predates the boundedness registry. Its
  growth surfaces, where it created any, were inventoried and bound
  retrospectively by BOUND-1 against the post-increment source rather than
  claimed here after the fact. See
  docs/reference/BOUNDEDNESS_REGISTRY.json and
  docs/development/BOUNDEDNESS_LAW.md.
```
