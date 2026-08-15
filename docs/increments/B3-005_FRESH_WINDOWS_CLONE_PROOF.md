# B3-005 — Fresh Windows Clone End-to-End Proof

**Status:** PRE_CERTIFICATION — REOPENED; ACCEPTANCE CORRECTION AWAITS FRESH REPROOF
**Commission:** `SOL-FM-SSSF-B3-005-001`
**Starts from:** `sssf-b3-004-closure-hygiene-correction`
**Base SHA:** `04e5484a6190f033d25e1626b96a4cca93b7f755`
**Branch:** `increment/b3-005-fresh-windows-clone-proof`
**Proof candidate:** `efd84ab02fee4cb4c8e1e116616e039ba84a0546`
**Proof run:** `b3-005-proof-20260815-b30005`

## Problem

B3-003 proved repository-owned Windows session bootstrap from a fresh Command Prompt, and B3-004 removed the Windows external-sqlite dependency. B3 still lacked one integrated proof from a genuinely fresh Windows clone through bootstrap, complete host doctor, sandbox create/fill/setup/observe, source verification, observability, ordered teardown, and residue controls.

The commission permits reversible PRE_CERTIFICATION preparation. It forbids merge, canonical-main advancement, a final B3 freeze tag, security weakening, metered-path enablement, or conversion of missing/held evidence into PASS.

## Desired outcome

Establish and retain:

1. exact base, branch, host, clone, guest, run, and candidate identity;
2. a Windows-native process environment independent of the inherited worker;
3. pre-bootstrap Git Bash PATH/executable negative controls;
4. root `just` and `just local` before bootstrap;
5. bootstrap-only session PATH reconstruction with unchanged persistent PATH;
6. full host doctor and composed sandbox doctor;
7. exactly one complete disposable sandbox lifecycle;
8. independent guest repository/SHA/cleanliness proof;
9. B3-004 sqlite-free Windows observability;
10. artifact/harvest custody before teardown's irreversible actions;
11. runtime-key revocation, VM absence, closed record, and no residual runtime key;
12. clean proof-clone status with no patch-and-continue;
13. explicit PASS/FAIL/CNO/HOLD classification for every unresolved dimension.

## Design

The proof harness is:

`docs/evidence/B3-005_WINDOWS_NATIVE_PROOF.ps1`

It calls Windows `CreateEnvironmentBlock` for the current Windows user with `inherit=false`, clears a child `ProcessStartInfo` environment, populates it only from the native environment block, and launches absolute `cmd.exe /d`. It captures exact process creation, child environment, registry environment state, command output, exit status, and hashes.

The lifecycle remains repository-owned. No new lifecycle path or cleanup sequence is introduced. Teardown retains the existing load-bearing order:

`spend -> artifacts -> harvest -> revoke -> destroy -> close -> gate`

No ADR is required because B3-005 does not change system architecture, lifecycle authority, security boundaries, or source provenance. It adds a bounded proof harness and durable evidence.

## Implementation and proof history

### Proof-harness bootstrap correction

The first proof clone stopped when the harness ran composed sandbox doctor before approved ignored host configuration existed. The clone was not edited or continued. The harness correction was committed only on the contribution branch, and the proof restarted from a newly allocated clone at exact candidate:

`efd84ab02fee4cb4c8e1e116616e039ba84a0546`

### Fresh Windows bootstrap

The successful clone at `E:\SSSF-B3-005-PROOF-20260815-154222` began without Git Bash `bin`/`usr\bin`, `sh`, `cygpath`, or `zsh`. Root `just` and `just local` worked before bootstrap.

`bin\sssf-windows.cmd --sandbox` then reconstructed the session PATH, passed host doctor, passed composed sandbox doctor, and passed B3-004 observability without external sqlite3. Persistent HKCU/HKLM environment values remained unchanged.

### Review-required equivalence seam

The actual method/evidence was routed through FirstMate and posted to control issue #3:

`https://github.com/sbracewell64/firstmate-sol-control/issues/3#issuecomment-5302981383`

Browser Sol had not ruled at closure preparation. This dimension remains `CNO / HOLD` and is not represented as PASS.

### Exactly one sandbox

Run `b3-005-proof-20260815-b30005` completed create, fill, setup, and observe from the fresh proof clone. Host, run record, FILL gate, SETUP Gate A, and independent guest inspection agreed on canonical repository, exact candidate SHA, and clean guest source.

The app returned HTTP 200 and the owner-gated observability endpoint returned HTTP 307.

### Three-valued findings

SETUP printed insufficient-credit failures for all four roster models and then contradicted those lines by reporting Gate C/D/E PASS. The roster-model dimension is `FAIL / UNRESOLVED`, never PASS. No credit purchase or metered-path enablement was attempted.

The first lifecycle harness also over-scoped the Windows external-sqlite absence condition to the Linux guest. `/bin/sqlite3` was observed and the extra check failed. That does not negate the successful Windows B3-004 proof. The harness was corrected on the contribution branch to apply external executable absence only on Windows and the stdlib query contract cross-platform. The proof clone was not edited, and no second sandbox was created.

### Ordered teardown

Teardown recorded `$0` spend, copied artifacts, ran harvest, revoked the runtime key, destroyed the VM, shredded the runtime-key file, closed the run record, and passed authoritative key-list absence. The target VM and fleet were absent afterward.

The proof clone's exact tracked state remained clean with no diff. It and its ignored host config were then disposed.

## Evidence

Detailed evidence record:

`docs/evidence/B3-005_FRESH_CLONE_PROOF.md`

Windows equivalence record:

`docs/evidence/B3-005_WINDOWS_NATIVE_EQUIVALENCE.md`

Raw retained text evidence and manifests:

`docs/evidence/b3-005/`

Closed run record:

`docs/evidence/b3-005/closed-run-record.json`

## Non-goals

- Merge the contribution branch.
- Advance canonical `main`.
- Create, move, or rewrite a final B3 freeze tag.
- Self-approve Windows-native equivalence.
- Repair the pre-existing setup model-probe gate.
- Purchase credits or enable a metered path.
- Execute an ADW or create guest commits.
- Commit a runtime SQLite database.
- Copy a host authentication home into a guest.
- Change sandbox provider, model roster, or ADW behavior.

## Acceptance

The detailed proof record contains the authoritative dimension-by-dimension table. In summary:

- fresh clone/bootstrap/front doors/persistent boundary: PASS except equivalence review seam;
- Windows-native equivalence: CNO / HOLD;
- exactly one sandbox lifecycle and source custody: PASS;
- Windows sqlite-free observability: PASS;
- contradictory setup roster probe: FAIL / UNRESOLVED;
- ordered teardown and residual-resource controls: PASS;
- proof-clone no-edit and disposal: PASS;
- merge, main advancement, and final B3 freeze: HOLD / NOT PERFORMED.

## Reopened acceptance defect

Independent PR review rejected the first proof as final evidence. Four insufficient-credit roster failures were followed by unconditional Gate C/D/E PASS lines because host acceptance trusted the remote transport result without requiring typed subgate evidence or reconciling the captured diagnostics. The contradiction is a source-level acceptance defect, not merely a known limitation.

The bounded correction adds:

- one typed remote `SSSF_CDE_RESULT` marker;
- explicit `PASS` / `FAIL` / `CNO` states for roster, live cost, and runtime-key evidence;
- host capture of complete remote output and remote exit status;
- deterministic reconciliation in `tools/setup_cde_acceptance.py`;
- regression validation in `docs/validation/check_setup_cde_acceptance.py`;
- Windows host-doctor composition of that validator.

The old insufficient-credit output now classifies `CNO/HOLD`; it cannot reach downstream PASS. A repaired candidate must be published and proved from another newly allocated fresh Windows clone. No proof-clone patch-and-continue is permitted.

## Result

The first proof and its cleanup remain durable diagnostic evidence, but they are not final B3-005 acceptance evidence. B3-005 is reopened pending the required fresh-clone proof of the acceptance correction.

**Result: REOPENED — FRESH REPROOF REQUIRED**
