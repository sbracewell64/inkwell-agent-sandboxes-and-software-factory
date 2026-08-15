# B3-003 — Windows Bootstrap and Host Doctor

**Status:** PROVEN
**Starts from:** `sssf-b3-002-line-ending-contract`
**Accepted candidate:** `d5c53e871b32902ee76cd082a944afa4cdfc218d`
**Proof date:** 2026-08-14

## Problem

B3-001 established that the current Windows host was operational only after several manually assembled environment conditions were present.

B3-003 probing then established two concrete Windows front-door failures.

On the Windows host:

`where zsh`

reported no executable.

Before B3-003:

`just`

failed because the root justfile required `zsh`.

`just local`

failed for the same reason.

At the same time:

`just sbx manage doctor`

passed because its doctor recipe has an explicit Bash shebang and therefore bypasses the root linewise-shell setting.

## Persistent PATH finding

The persistent Windows environment did not contain the two Git Bash paths required by the existing SSSF shell workflows.

The persistent machine PATH contained:

`C:\Program Files\Git\cmd`

but not:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

The working Command Prompt used during earlier SSSF development contained those two paths repeatedly because they had been prepended manually.

The working session was therefore functional but not reproducible from persistent Windows state.

## Executable-selection finding

Multiple implementations or versions are simultaneously installed.

Observed examples:

- Git resolves from both `Git\bin` and `Git\cmd` after bootstrap.
- SSH exists as both Git for Windows OpenSSH and Windows OpenSSH.
- `python` resolves to Python 3.11.
- `python3` resolves to Python 3.13 through WindowsApps.
- zsh is absent.

SSSF must not depend on accidental PATH ordering when multiple implementations coexist.

## Desired outcome

Provide a repository-owned Windows front door that:

1. works from Command Prompt;
2. does not require zsh;
3. constructs a deterministic session PATH;
4. removes duplicate PATH entries;
5. puts Git Bash and Git SSH in deterministic positions;
6. validates required host tooling;
7. validates Python compatibility;
8. validates just compatibility;
9. validates effective exe.dev SSH behavior without exposing secrets;
10. validates the B3-002 line-ending contract;
11. validates the root `just` and `just local` front doors;
12. optionally composes the existing sandbox doctor;
13. leaves external sqlite3 non-fatal until B3-004;
14. does not modify persistent HKCU or HKLM environment state.

## Shell contract

Unix preserves the existing interactive-zsh behavior.

Windows uses:

`cmd.exe /d /c`

for linewise recipes in:

- the root justfile;
- `just/local.just`.

Recipes with explicit shebangs continue to bypass the linewise-shell setting.

The first Windows implementation retained `set positional-arguments` in the root and local modules.

That caused nested listing recipes to receive `default` as an unwanted positional argument, producing:

`justfile does not contain submodule default`

and:

`justfile does not contain submodule local default`

The root and local modules do not require positional arguments themselves, so that setting was removed from those two modules.

The ADW module retains its own independent positional-argument contract.

After correction:

`just`

listed the root namespaces successfully.

`just local`

listed:

- `cc`
- `default`
- `pi`

successfully.

`where zsh`

continued to report no executable.

Therefore zsh is no longer a Windows front-door dependency.

The `ipi` local recipe remains Unix-only because the current contract defines it as a zsh function rather than a Windows executable.

## Bootstrap contract

The Windows bootstrap entrypoint is:

`bin\sssf-windows.cmd`

It:

1. resolves the repository root from its own location;
2. requires an already-installed Python command;
3. asks deterministic Python code to construct the session PATH;
4. deduplicates PATH entries case-insensitively;
5. prepends the discovered Git for Windows `bin` and `usr\bin`;
6. ensures `.local\bin` and `.bun\bin` are present when those directories exist;
7. changes only the current Command Prompt environment;
8. exports `SSSF_ROOT` for that session;
9. runs the host doctor;
10. reports the session ready only if required checks pass.

## Host-doctor contract

`tools/windows_host.py doctor`

requires:

- Windows;
- a Git checkout;
- discoverable Git for Windows;
- unique PATH entries;
- Git `bin` and `usr\bin` in PATH;
- Git;
- Bash/sh;
- cygpath;
- Git SSH as the selected SSH implementation;
- Python;
- python3;
- Bun;
- uv;
- just;
- GitHub CLI;
- Python 3.11 or newer;
- just 1.56 or newer;
- canonical `origin`;
- passing the authoritative strict B3-002 invocation,
  `python docs/validation/check_line_endings.py --require-worktree-lf`;
- working root `just`;
- working `just local`;
- effective `exe.dev` SSH policy;
- effective `*.exe.xyz` wildcard SSH policy.

It treats these as informational or non-fatal:

- zsh on Windows;
- external sqlite3 until B3-004;
- Claude;
- Pi;
- Herdr.

## Sandbox composition

The host doctor accepts:

`--sandbox`

When requested, it additionally runs:

`just sbx manage doctor`

This composes the existing sandbox-specific checks rather than duplicating them.

## Pre-candidate bootstrap proof

The bootstrap was first run against the deliberately duplicated working-session PATH.

The host doctor passed all required checks.

After bootstrap:

- Git `bin` count = 1
- Git `usr\bin` count = 1
- every PATH entry was unique
- Git resolved from `C:\Program Files\Git\bin`
- Bash resolved from `C:\Program Files\Git\bin`
- cygpath resolved from `C:\Program Files\Git\usr\bin`
- SSH resolved first from `C:\Program Files\Git\usr\bin`

The bootstrap was then run a second time with:

`--sandbox`

The composed sandbox doctor passed.

The PATH after the second bootstrap was byte-for-byte identical to the PATH after the first bootstrap.

Observed result:

`PASS: bootstrap PATH idempotent`

## Persistent-state boundary proof

After bootstrap, the persistent HKCU PATH remained unchanged.

The persistent HKLM PATH also remained unchanged.

HKLM continued to contain:

`C:\Program Files\Git\cmd`

and did not gain persistent:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

B3-003 therefore changes the current Command Prompt session only.

It does not write:

- `HKCU\Environment\Path`
- machine PATH
- Git global configuration
- SSH private keys
- permanent shell aliases

## Candidate commit

The exact implementation candidate is:

`d5c53e871b32902ee76cd082a944afa4cdfc218d`

The candidate contains:

- `bin/sssf-windows.cmd`
- `tools/windows_host.py`
- Windows/Unix shell selection in `justfile`
- Windows/Unix shell selection in `just/local.just`
- this increment record

Before commit:

`git diff --cached --check`

passed.

After commit:

`git show --check --oneline HEAD`

passed.

The candidate was pushed to:

`increment/b3-003-windows-bootstrap-host-doctor`

Local and remote branch SHAs both resolved to:

`d5c53e871b32902ee76cd082a944afa4cdfc218d`

## Fresh Command Prompt exact-candidate proof

A genuinely new Windows Command Prompt was opened from persistent Windows state rather than from the already-bootstrapped SSSF session.

Before bootstrap:

`git rev-parse HEAD`

reported:

`d5c53e871b32902ee76cd082a944afa4cdfc218d`

The working tree was clean.

The new Command Prompt PATH contained neither:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

Before bootstrap:

`where sh`

reported no executable.

`where cygpath`

reported no executable.

`where ssh`

resolved only:

`C:\Windows\System32\OpenSSH\ssh.exe`

`where zsh`

reported no executable.

Despite zsh being absent and Git Bash not yet being on PATH:

`just`

worked.

`just local`

worked.

This independently proved the new Windows-native just front doors.

## Exact committed bootstrap reconstruction proof

From that same fresh Command Prompt:

`bin\sssf-windows.cmd --sandbox`

was run against candidate:

`d5c53e871b32902ee76cd082a944afa4cdfc218d`

The host doctor passed.

The composed sandbox doctor reported:

`sbx doctor: OK`

The bootstrap reported:

`SSSF Windows host doctor: OK`

and:

`SSSF Windows session ready.`

After bootstrap:

- Git `bin` count = 1
- Git `usr\bin` count = 1
- all PATH entries were unique

Executable resolution then showed:

- `sh` from `C:\Program Files\Git\bin`
- `cygpath` from `C:\Program Files\Git\usr\bin`
- SSH first from `C:\Program Files\Git\usr\bin`
- Windows OpenSSH still installed as the secondary SSH implementation

zsh remained absent.

The working tree remained clean.

This proves that the committed repository bootstrap reconstructs the required SSSF Windows session from persistent host state rather than relying on prior manual PATH edits.

## Line-ending boundary

B3-002 established:

`* text=auto eol=lf`

B3-003 does not weaken that policy.

The B3-002 line-ending validator passed after the Windows shell and bootstrap changes.

HD-01 later corrected the doctor integration to invoke the already-documented
strict form exactly:

`python docs/validation/check_line_endings.py --require-worktree-lf`

The default validator is also strict, so no alternate non-worktree mode can
mask CRLF. Doctor/bootstrap output names the exact command. Failure or
could-not-observe evidence is terminal, and neither validator nor bootstrap
rewrites a developer working tree; remediation remains an explicit operator
action documented in `docs/operations/INSTALL_WINDOWS.md`.

The `.cmd` bootstrap executed successfully under the repository LF policy.

No CRLF exception was required.

## Known remaining portability gap

External sqlite3 remains absent.

The host doctor reports that condition as:

`WARN`

rather than failure.

B3-004 owns removal of the external sqlite3 dependency from Windows host observability.

The final fresh-clone/mount/teardown integration proof remains B3-005 scope.

## Non-goals

- Install missing host software automatically.
- Modify persistent Windows PATH.
- Install zsh on Windows.
- Fix external sqlite3 observability.
- Change sandbox source provenance.
- Change ADW behavior.
- Replace exe.dev.
- Change model rosters.
- Make Claude, Pi, or Herdr mandatory Windows portability dependencies.

## Acceptance

1. `just` runs successfully on Windows with no zsh installed.
2. `just local` runs successfully on Windows with no zsh installed.
3. Unix retains the existing interactive-zsh shell contract.
4. `ipi` is not offered as a Windows local recipe.
5. The Windows bootstrap removes duplicate PATH entries.
6. Re-running the bootstrap produces the same effective PATH.
7. Git Bash `sh` resolves from the Git installation.
8. `cygpath` resolves from Git `usr\bin`.
9. SSH resolves to Git for Windows rather than Windows OpenSSH after bootstrap.
10. Python and python3 both satisfy the declared compatibility floor.
11. just satisfies the declared compatibility floor.
12. Bun, uv, just, GitHub CLI, and Git resolve.
13. Effective SSH policy for `exe.dev` and a synthetic `*.exe.xyz` host passes.
14. The strict B3-002 invocation `python docs/validation/check_line_endings.py --require-worktree-lf` passes.
15. External sqlite3 absence is non-fatal and remains assigned to B3-004.
16. `--sandbox` composes and passes the existing sandbox doctor.
17. Persistent user and machine PATH values remain unchanged.
18. `git diff --check` passes.
19. Python source compiles.
20. B3-002 remains frozen at `8df2a9bc535bc8f5be50742053dc6ebf520c54ee`.
21. A fresh Command Prompt begins without Git Bash paths and successfully reconstructs them using the committed bootstrap.
22. The exact committed and remotely published candidate is the one used for the fresh Command Prompt proof.

All B3-003 acceptance criteria are satisfied.

## Result

B3-003 establishes a repository-owned Windows bootstrap and host-doctor contract.

Windows SSSF no longer requires manual Git PATH prepending or a local zsh installation merely to use the root and local front doors.

A fresh Command Prompt beginning from persistent Windows PATH successfully reconstructed the required Git Bash, cygpath, Git SSH, toolchain, line-ending, repository, and sandbox prerequisites using the exact committed candidate.

Persistent Windows PATH state was not modified.

External sqlite3 remains the next explicit Windows portability defect.

**Result: PASS**