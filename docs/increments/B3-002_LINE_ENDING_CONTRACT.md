\# B3-002 — Repository Line-Ending Contract



\*\*Status:\*\* IN\_PROGRESS

\*\*Starts from:\*\* `sssf-b3-001-windows-portability-baseline`



\## Problem



B3-001 proved that the repository does not own its line-ending behavior.



The Windows host has:



`core.autocrlf=true`



and the repository had no `.gitattributes`.



The index already stored representative source files as LF, but the Windows working tree materialized many tracked text files as CRLF.



This included every tracked `.just` file and all tracked `.sh` files.



Execution-sensitive source therefore depended on operator-level Git configuration instead of repository-owned policy.



\## Desired outcome



Make line-ending behavior deterministic from repository state.



All files Git classifies as text should:



\- be normalized as LF in the index;

\- be checked out as LF on every platform;

\- remain LF even when the Windows host has `core.autocrlf=true`.



Binary files must remain subject to Git's normal binary detection rather than being forced through text conversion.



\## Policy



The repository-owned policy is:



`\* text=auto eol=lf`



Meaning:



\- `text=auto` lets Git distinguish text from binary content;

\- text content is normalized in Git;

\- `eol=lf` materializes text files with LF working-tree line endings;

\- host-global `core.autocrlf` no longer decides repository text-file line endings.



\## Why the policy is repository-wide



The B3-001/B3-002 inventory found CRLF working-tree materialization across far more than shell files.



Affected text classes included:



\- `.just`

\- `.sh`

\- `.py`

\- `.md`

\- `.json`

\- `.yaml`

\- `.ts`

\- `.css`

\- `.html`

\- other text assets



Limiting the policy only to shell files would preserve the underlying portability ambiguity for the rest of the repository.



A single repository-wide text rule is smaller and more deterministic than maintaining a growing extension list.



\## Windows-native scripts



At B3-002 start, the repository contained no tracked:



\- `.bat`

\- `.cmd`

\- `.ps1`



files.



No CRLF exception is therefore introduced speculatively.



If a future Windows-native file genuinely requires CRLF, that requirement must be added explicitly and proven when the file is introduced.



\## Existing defensive runtime handling



B3-002 does not remove the previously proven CR-stripping protection in the sandbox lifecycle.



Repository line-ending policy prevents one source of CRLF materialization, but the defensive runtime normalization protects a separate process-boundary condition.



Removing it would require independent evidence and is outside this increment.



\## Implementation



B3-002 adds:



\- repository-root `.gitattributes`;

\- `docs/validation/check\_line\_endings.py`;

\- this increment record.



The validator checks:



\- the exact repository policy;

\- effective Git attributes on representative files;

\- LF index state;

\- optionally, LF working-tree state for a fresh-checkout proof.



\## Proof strategy



The existing working tree is not manually mass-rewritten.



Instead:



1\. establish the policy;

2\. verify existing index content is already normalized;

3\. create an exact candidate commit;

4\. publish the candidate branch;

5\. perform a fresh Windows checkout with `core.autocrlf=true`;

6\. require the fresh checkout's representative text files to report `w/lf`;

7\. verify the fresh checkout is clean.



This distinguishes repository policy from incidental state in the already-existing working tree.



\## Non-goals



\- Change runtime semantics.

\- Rewrite source files merely to change line endings.

\- Remove existing CR defensive handling.

\- Modify the user's global Git configuration.

\- Add Windows bootstrap behavior.

\- Fix host observability.

\- Replace exe.dev.

\- Introduce Windows-native scripts.

\- Add speculative CRLF exceptions.



\## Acceptance



1\. `.gitattributes` defines `\* text=auto eol=lf`.

2\. Representative `.just`, `.sh`, `.py`, and documentation files resolve `text=auto` and `eol=lf`.

3\. Existing representative index content remains LF.

4\. Renormalization produces no unrelated mass source diff.

5\. A fresh Windows checkout made with `core.autocrlf=true` materializes representative text files as LF.

6\. The fresh checkout is clean.

7\. Existing lifecycle compatibility protections remain present.

8\. No global Git configuration is modified.

9\. `git diff --check` passes.

10\. Documentation and validator source are valid UTF-8.

11\. B3-001's immutable tag remains unchanged.



\## Evidence



Pending candidate implementation and fresh-checkout proof.



\## Result



Pending.

