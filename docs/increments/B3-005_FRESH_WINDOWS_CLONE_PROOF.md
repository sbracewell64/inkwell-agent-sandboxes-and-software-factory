# B3-005 — Fresh Windows Clone End-to-End Proof

**Status:** PRE_CERTIFICATION — PROOF IN PROGRESS
**Commission:** `SOL-FM-SSSF-B3-005-001`
**Starts from:** `sssf-b3-004-closure-hygiene-correction`
**Base SHA:** `04e5484a6190f033d25e1626b96a4cca93b7f755`
**Branch:** `increment/b3-005-fresh-windows-clone-proof`

## Intent

Establish the remaining B3 portability proof from a genuinely fresh Windows-native clone while preserving source custody, sandbox lifecycle ordering, credential boundaries, deterministic acceptance, and three-valued evidence.

## PRE_CERTIFICATION boundary

This increment prepares only reversible branch, proof, evidence, and pull-request work. It does not:

- merge the contribution branch;
- advance canonical `main`;
- create, move, or rewrite a final B3 freeze tag;
- classify Windows-native equivalence as PASS without the commissioned Browser Sol review;
- turn missing or unreadable evidence into PASS.

## Proof design

The proof harness is:

`docs/evidence/B3-005_WINDOWS_NATIVE_PROOF.ps1`

It asks Windows `userenv.dll` to create an environment block for the current Windows user with `CreateEnvironmentBlock(..., inherit=false)`. It then clears a `cmd.exe` child's environment and supplies only that native block. This makes process-environment construction independent of the inherited WSL worker environment. The harness records process creation, the exact child environment, raw persistent HKCU/HKLM environment values before and after, PATH, executable resolution, commands, output, exit status, and artifact hashes.

The bootstrap phase must prove, in order:

1. the newly allocated proof path did not already exist;
2. the exact clone command, repository, branch, HEAD, status, and remote;
3. Git Bash `bin` and `usr\bin` PATH absence;
4. `sh`, `cygpath`, and `zsh` resolution absence;
5. root `just` and `just local` before bootstrap;
6. repository-owned `bin\sssf-windows.cmd --sandbox`;
7. post-bootstrap Git Bash tool resolution;
8. B3-004 sqlite-free observability;
9. no tracked proof-clone edit.

The lifecycle phase will create, fill, setup, and observe exactly one disposable exe.dev sandbox. It will stage only the existing host provisioning credential in the ignored proof-clone `.env`; the lifecycle mints and injects only its bounded per-run runtime key. It will independently verify guest repository, exact SHA, and cleanliness before relying on guest results.

The teardown phase will use only the repository lifecycle and preserve its required order:

`spend -> artifacts -> harvest -> revoke -> destroy -> close -> gate`

## Stop and rollback rules

- A source defect stops the current proof. The proof clone is never patched and continued.
- A correction is made only on this contribution branch, after which the disposable proof clone is discarded and recreated.
- Missing, unreadable, unavailable, or ambiguous evidence is CNO.
- Disposable runtime resources are removed through the existing lifecycle, never manual cleanup.
- Long-lived host credentials and native authentication homes remain outside guest and tracked source custody.

## Evidence and closure

The exact proof identities, retained logs, lifecycle result, candidate identity, acceptance table, ledger entry, and proof-matrix rows will be added after execution. Until then no B3-005 dimension is represented as PASS.
