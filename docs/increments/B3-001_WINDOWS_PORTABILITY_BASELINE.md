# B3-001 — Windows Host Portability Baseline

**Status:** PROVEN
**Starts from:** `sssf-b2-004-ledger-closure`
**Audit date:** 2026-08-14

## Problem

SSSF has been proven on the current Windows host, but several host-specific compatibility requirements were discovered manually during baseline construction.

Those requirements were not represented as one explicit, testable Windows host contract.

Known historical observations included:

- Git Bash tooling requires both `sh` and `cygpath`.
- Windows Command Prompt requires Git's `bin` and `usr\bin` directories to be reachable.
- sandbox lifecycle code previously required CR normalization for Python output consumed by shell code.
- teardown previously required portable `mktemp` usage under Git Bash/MSYS.
- noninteractive sandbox SSH required explicit wildcard host configuration.
- Windows Git emitted LF-to-CRLF working-copy warnings.
- host observability failed when external `sqlite3` was unavailable.
- successful operation depended on tools installed through several different Windows mechanisms.

These requirements must not remain implicit operator knowledge.

## Desired outcome

Capture the actual Windows host prerequisites, current configuration, known compatibility seams, and deterministic follow-up work needed to turn Windows support into an explicit SSSF contract.

B3-001 is an audit and contract-definition increment.

It intentionally does not modify runtime or sandbox behavior.

## Non-goals

- Replace exe.dev.
- Add a local sandbox provider.
- Change sandbox source provenance.
- Change agent rosters.
- Change ADW behavior.
- Perform broad refactoring.
- Silence Git line-ending warnings without defining a repository policy.
- Modify system-wide Windows configuration during the audit.
- Make Herdr a required SSSF dependency.

## Audit environment

The audit was performed from Windows Command Prompt in the canonical SSSF checkout.

Repository state began from:

`sssf-b2-004-ledger-closure`

The working tree contained only this untracked B3-001 audit record during evidence collection.

## Finding 1 — Core host toolchain resolves

Observed executable resolution:

- Git for Windows resolves from both `Git\bin` and `Git\cmd`.
- Bash resolves from Git for Windows.
- `cygpath` resolves from Git for Windows `usr\bin`.
- SSH resolves first to Git for Windows, with Windows OpenSSH also installed.
- `python` currently resolves to Python 3.11 before Python 3.13.
- Bun resolves under `%USERPROFILE%\.bun\bin`.
- uv resolves under `%USERPROFILE%\.local\bin`.
- just resolves under `%USERPROFILE%\.local\bin`.
- GitHub CLI resolves through its WinGet installation.
- external `sqlite3` does not resolve.
- Herdr is installed, but is not required by the current SSSF portability contract.

Observed versions:

- Git: `2.53.0.windows.2`
- Bash: `5.2.37`
- OpenSSH: `10.2p1`
- Python selected by `python`: `3.11.9`
- Bun: `1.3.14`
- uv: `0.12.3`
- just: `1.58.0`
- GitHub CLI: `2.96.0`
- Herdr: `0.7.5-preview.2026-07-21-0f10e1453a7f`

### Disposition

Core host tooling is operational.

The portability contract should not rely on incidental PATH ordering where multiple implementations or versions are installed.

## Finding 2 — PATH is functional but not cleanly reproducible

The current Command Prompt PATH contains the required Git for Windows directories:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

It also contains:

- `%USERPROFILE%\.local\bin`
- `%USERPROFILE%\.bun\bin`

Both `sh` and `cygpath` resolve successfully.

However, `C:\Program Files\Git\bin` and `C:\Program Files\Git\usr\bin` occur repeatedly in the current PATH.

### Disposition

The current environment works, but PATH state is not a suitable reproducibility contract.

A Windows bootstrap should establish the required paths idempotently and avoid accumulating duplicate entries.

## Finding 3 — Repository line endings are not governed

Observed Git configuration:

`core.autocrlf=true`

No explicit values were present for:

- `core.eol`
- `core.safecrlf`

The repository has no `.gitattributes`.

Observed tracked-file state:

- `docs/baseline/PROOF_MATRIX.md`: index LF, working tree LF
- `docs/increments/B2-002_SANDBOX_SOURCE_CONTRACT.md`: index LF, working tree LF
- `just/sandbox/lifecycle/fill.just`: index LF, working tree CRLF
- `just/sandbox/lifecycle/setup.just`: index LF, working tree CRLF

### Disposition

This is an unresolved portability seam.

The repository currently relies on global Git configuration and file history to determine working-tree line endings.

B3 must define a repository-owned line-ending contract, especially for files executed through Bash/MSYS.

Existing defensive CR normalization must not be removed merely because a `.gitattributes` policy is introduced; removal would require separate proof.

## Finding 4 — SSH behavior is currently correct

Effective configuration for `exe.dev` showed:

- `IdentitiesOnly yes`
- `StrictHostKeyChecking accept-new`
- dedicated exe.dev identity selected

Effective configuration for a synthetic `b3-probe.exe.xyz` hostname showed the same behavior.

This proves the wildcard host rule applies to dynamically created sandbox hostnames.

No private key contents were inspected or recorded.

### Disposition

Current SSH behavior satisfies the exe.dev lifecycle requirement.

A future Windows host validator should check effective behavior rather than depend solely on the textual shape of an operator SSH config file.

## Finding 5 — SSH executable selection depends on PATH precedence

Two SSH implementations are installed:

- Git for Windows OpenSSH
- Windows System32 OpenSSH

The current Command Prompt resolves Git for Windows SSH first.

### Disposition

Current behavior is proven, but fresh-host support should make the intended shell/SSH environment explicit enough that success does not depend on accidental executable precedence.

## Finding 6 — Multiple Python versions are installed

The host contains at least:

- Python 3.11
- Python 3.13
- WindowsApps Python resolution entry

The bare `python` command currently selects Python 3.11.9.

### Disposition

Current SSSF operation succeeds with that ordering.

A Windows bootstrap or validator should establish the actual Python compatibility requirement rather than merely assume whichever `python.exe` appears first is acceptable.

## Finding 7 — External sqlite3 is absent

`where sqlite3` returned no executable.

This agrees with the existing unresolved host-observability finding.

### Disposition

Host observability must either:

1. declare and install an external `sqlite3` dependency; or
2. preferably use Python's standard-library SQLite support or another already-owned implementation.

The second option is preferred because it reduces host prerequisites.

This remains unproven until implemented and tested.

## Finding 8 — Existing Windows lifecycle compatibility fixes remain relevant

Prior proven increments established Windows compatibility for:

- CR normalization of lifecycle metadata consumed by shell code;
- MSYS-compatible temporary-file creation during teardown;
- wildcard SSH behavior needed by generated exe.dev hostnames.

B3-001 does not remove or alter those protections.

### Disposition

Later B3 work should add deterministic regression checks around these behaviors rather than treating the historical fixes as temporary local patches.

## Finding 9 — Current sandbox doctor passes

Observed:

`just sbx manage doctor`

Result:

`sbx doctor: OK`

The doctor verified:

- exe.dev SSH reachability;
- provisioning-key presence;
- run-record helper;
- provisioner;
- model-rate configuration;
- ADW layer resolution.

### Disposition

The existing sandbox doctor proves the current sandbox prerequisites it knows about.

It does not constitute a complete Windows host portability validator because external `sqlite3` is absent while doctor still passes, and it does not encode all of the PATH, line-ending, executable-selection, and fresh-host requirements discovered by this audit.

## Finding 10 — Current audit introduced no runtime changes

Observed after evidence collection:

`git diff --check`

Result: PASS.

Observed working tree:

`?? docs/increments/B3-001_WINDOWS_PORTABILITY_BASELINE.md`

No runtime, lifecycle, sandbox, application, agent, or configuration implementation file changed during the audit.

## Windows host contract derived from the audit

A supported Windows SSSF host must eventually provide deterministic answers for:

1. required executable presence;
2. executable selection when multiple implementations exist;
3. required PATH entries;
4. Git/Bash/MSYS interoperability;
5. repository-owned line endings;
6. exe.dev SSH behavior;
7. Python compatibility;
8. sandbox lifecycle portability;
9. host observability;
10. fresh-clone bootstrap and recovery.

## Follow-up increments

### B3-002 — Repository line-ending contract

Define and test repository-owned line-ending behavior.

Expected scope:

- add an appropriate `.gitattributes`;
- force execution-sensitive shell/Just files to deterministic line endings;
- preserve source semantics;
- validate index and working-tree behavior on Windows;
- retain defensive lifecycle normalization unless separately proven unnecessary;
- eliminate accidental LF/CRLF churn.

Acceptance should include deterministic `git ls-files --eol` expectations for execution-sensitive files.

### B3-003 — Windows bootstrap and host-doctor contract

Turn the currently successful but manually assembled host environment into deterministic bootstrap and validation behavior.

Expected scope:

- required tool discovery;
- Git Bash `sh` and `cygpath`;
- PATH construction;
- duplicate-path avoidance;
- Python compatibility;
- SSH executable/environment selection;
- effective exe.dev wildcard SSH behavior;
- Bun, uv, just, GitHub CLI, and required Git tooling;
- clear distinction between required and optional tools.

The bootstrap must be idempotent.

Herdr should remain optional unless a later architecture increment explicitly makes it part of SSSF.

### B3-004 — sqlite-free Windows host observability

Remove the unnecessary external `sqlite3` executable dependency if feasible.

Preferred implementation:

use Python standard-library SQLite support behind the host observability interface.

Acceptance must prove the host observability commands work on this Windows host while `where sqlite3` still reports no external executable.

### B3-005 — Fresh Windows clone proof

Perform the final B3 integration proof only after B3-002 through B3-004 are accepted.

Required proof path:

`fresh Windows clone -> bootstrap -> doctor -> mount -> teardown`

The proof must require no manual source editing and no transient operator-only compatibility commands.

It must also prove:

- source provenance remains intact;
- lifecycle cleanup succeeds;
- no runtime key remains;
- no VM remains;
- host observability is usable;
- repository line-ending state remains compliant.

## Acceptance

1. Current Windows tool resolution was captured.
2. Required PATH dependencies were identified.
3. Git line-ending configuration and representative file states were captured.
4. SSH behavioral requirements were established without recording secrets.
5. Existing lifecycle portability fixes were identified.
6. Host external `sqlite3` availability was established as absent.
7. `just sbx manage doctor` passed from the current Windows environment.
8. Findings were classified into explicit follow-up increments rather than fixed opportunistically.
9. B3-001 changed documentation only.
10. `git diff --check` passed.
11. Documentation remained valid UTF-8.

All B3-001 acceptance criteria are satisfied.

## Result

B3-001 establishes the Windows portability baseline.

The current host is operational, but its successful state is not yet fully reproducible from repository-owned configuration.

The four remaining B3 implementation/proof increments are:

- B3-002 — repository line-ending contract;
- B3-003 — Windows bootstrap and host-doctor contract;
- B3-004 — sqlite-free Windows host observability;
- B3-005 — fresh Windows clone end-to-end proof.

B3-001 made no runtime or lifecycle changes.

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
