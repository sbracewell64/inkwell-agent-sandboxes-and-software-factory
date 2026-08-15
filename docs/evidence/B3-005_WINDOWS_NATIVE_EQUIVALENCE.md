# B3-005 Windows-Native Environment Equivalence Evidence

**Gate:** `REQUIRED_REVIEW_BEFORE_PASS`
**Current classification:** `CNO / HOLD — Browser Sol review pending`
**Successful proof candidate:** `efd84ab02fee4cb4c8e1e116616e039ba84a0546`
**Proof clone:** `E:\SSSF-B3-005-PROOF-20260815-154222`
**Evidence:** `docs/evidence/b3-005/bootstrap/`

## Independent process-environment construction

The worker invoked Windows PowerShell only as a transport into Windows. The proof child did not inherit the worker or PowerShell process environment.

`docs/evidence/B3-005_WINDOWS_NATIVE_PROOF.ps1`:

1. opens the current Windows user's process token with `OpenProcessToken`;
2. calls Windows `userenv.dll` `CreateEnvironmentBlock` with that token and `inherit=false`;
3. creates an absolute `C:\WINDOWS\System32\cmd.exe /d /s /c ...` process with `UseShellExecute=false`;
4. clears `ProcessStartInfo.EnvironmentVariables` completely;
5. populates the child environment only from the independently created native user environment block.

This is intended to reproduce the environment Windows constructs for the logged-on user without accepting any WSL worker PATH or prior SSSF bootstrap state. It is proposed as an automatable equivalent to a Start-menu Command Prompt; it is not self-approved.

The exact process-creation record is:

`docs/evidence/b3-005/bootstrap/process-creation.txt`

The exact child environment is:

`docs/evidence/b3-005/bootstrap/native-process-environment.txt`

Credential-shaped persistent values are explicitly redacted from retained output. Their variable name and presence remain visible; no credential value enters tracked evidence.

## Persistent Windows state

Raw registry names, types, and non-secret values were read directly from:

- `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment`
- `HKCU\Environment`

Before:

`docs/evidence/b3-005/bootstrap/persistent-environment-before.txt`

After:

`docs/evidence/b3-005/bootstrap/persistent-environment-after.txt`

After removing only each capture's timestamp line, the files are byte-identical. Persistent HKCU/HKLM PATH did not change.

## Pre-bootstrap negative controls

The native child PATH contained:

`C:\Program Files\Git\cmd`

It did not contain:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

Executable resolution before bootstrap showed:

- `git` -> `C:\Program Files\Git\cmd\git.exe`
- `ssh` -> `C:\Windows\System32\OpenSSH\ssh.exe`
- `sh` -> absent
- `cygpath` -> absent
- `zsh` -> absent

The batch fails if either forbidden Git Bash PATH entry is present or if `sh`, `cygpath`, or `zsh` unexpectedly resolves. The successful output is retained in:

`docs/evidence/b3-005/bootstrap/stdout.txt`

## Fresh clone and front doors

Exact clone command:

```bat
git clone --single-branch --branch increment/b3-005-fresh-windows-clone-proof https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git E:\SSSF-B3-005-PROOF-20260815-154222
```

The fresh clone reported exact HEAD:

`efd84ab02fee4cb4c8e1e116616e039ba84a0546`

Its branch tracked the commissioned remote branch at `+0/-0`; status and diff were clean. Before bootstrap, root `just` and `just local` both listed their command surfaces successfully.

## Bootstrap reconstruction

Only after the pre-bootstrap observations and root front-door checks, the harness copied the existing approved host `OPENROUTER_PROVISIONING_KEY` entry into the proof clone's ignored `.env`. The value was never printed or retained. No auth home was copied.

The child then called:

```bat
bin\sssf-windows.cmd --sandbox
```

The bootstrap introduced one Git `bin` and one Git `usr\bin` session entry. Resolution then selected Git Bash `sh`, `cygpath`, and Git OpenSSH. The complete host doctor, composed sandbox doctor, B3-002 validator, and B3-004 validator passed. External `sqlite3` remained absent, and the explicit B3-004 sqlite-free validator passed.

The proof clone remained tracked-clean with no compatibility edit.

## Failed proof retained, not continued

The first fresh proof at `E:\SSSF-B3-005-PROOF-20260815-154950` exposed a defect in the new proof harness: it requested composed sandbox doctor before staging approved ignored configuration. That proof stopped at exit 54. It was not patched or continued.

The defect was repaired only on the contribution branch in `efd84ab02fee4cb4c8e1e116616e039ba84a0546`. Failed proof evidence is retained under:

`docs/evidence/b3-005/failed-bootstrap/`

The failed clone was then discarded, and the successful proof used the newly allocated `...154222` path.

## Requested ruling

Please rule only on whether the documented `CreateEnvironmentBlock(inherit=false)` plus cleared child environment is equivalent to the commissioned fresh Windows-native Command Prompt condition.

Until that ruling, this dimension remains exactly:

`CNO / HOLD — REQUIRED_REVIEW_BEFORE_PASS`
