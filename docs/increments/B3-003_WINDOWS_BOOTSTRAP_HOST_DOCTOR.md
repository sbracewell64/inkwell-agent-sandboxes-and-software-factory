# B3-003 — Windows Bootstrap and Host Doctor

**Status:** IN_PROGRESS
**Starts from:** `sssf-b3-002-line-ending-contract`

## Problem

B3-001 established that the current Windows host was operational only after several manually assembled environment conditions were present.

B3-003 probing then established two concrete Windows front-door failures.

On the Windows host:

`where zsh`

reported no executable.

As a result:

`just`

failed because the root justfile required `zsh`.

`just local`

failed for the same reason.

At the same time:

`just sbx manage doctor`

passed.

That difference existed because the sandbox doctor recipe has an explicit Bash shebang and therefore bypasses the root linewise-shell setting.

## PATH finding

The persistent Windows environment does not contain the two Git Bash paths required by SSSF.

The persistent user PATH contains the user-installed Python, Bun, uv/just, GitHub CLI, and other tools.

The persistent machine PATH contains:

`C:\Program Files\Git\cmd`

but not:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

The pre-B3-003 interactive Command Prompt contained those Git paths repeatedly because they had been prepended manually during earlier SSSF work.

Therefore the working session was functional but not reproducible.

## Executable-selection finding

Multiple implementations or versions are simultaneously installed.

Observed examples:

- Git resolves from both `Git\bin` and `Git\cmd`.
- SSH resolves from Git for Windows and Windows OpenSSH.
- `python` resolves first to Python 3.11.
- `python3` resolves through WindowsApps to Python 3.13.
- zsh is absent.

SSSF must not depend on accidental PATH ordering when several acceptable or incompatible executables coexist.

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

The first Windows implementation retained `set positional-arguments` in those files.

That caused the nested listing recipes to receive `default` as an unwanted positional argument, producing:

`justfile does not contain submodule default`

and:

`justfile does not contain submodule local default`

The root and local modules do not require positional arguments themselves, so that setting was removed from those two modules.

The ADW module retains its own independent positional-argument contract.

After that correction:

`just`

listed all six root namespaces successfully.

`just local`

listed:

- `cc`
- `default`
- `pi`

successfully.

`where zsh`

continued to report no executable.

Therefore zsh is no longer a Windows front-door dependency.

Recipes with explicit shebangs continue to bypass the linewise-shell setting.

The `ipi` local recipe remains Unix-only because the existing contract defines it as a zsh function rather than a Windows executable.

## Bootstrap contract

The Windows bootstrap entrypoint is:

`bin\sssf-windows.cmd`

It:

1. resolves the repository root from its own location;
2. requires an already-installed compatible Python;
3. asks deterministic Python code to construct the session PATH;
4. deduplicates PATH entries case-insensitively;
5. prepends the discovered Git for Windows `bin` and `usr\bin`;
6. ensures `.local\bin` and `.bun\bin` are available when present;
7. changes only the current Command Prompt environment;
8. exports `SSSF_ROOT` for that session;
9. runs the host doctor;
10. reports the session ready only if required checks pass.

## First bootstrap proof

The bootstrap was run against the deliberately duplicated working-session PATH.

The host doctor reported:

- Windows host: PASS
- repository checkout: PASS
- Git for Windows root: PASS
- PATH uniqueness: PASS
- Git `bin` present: PASS
- Git `usr\bin` present: PASS
- Git: PASS
- Bash/sh: PASS
- cygpath: PASS
- Git SSH: PASS
- Python: PASS
- python3: PASS
- Bun: PASS
- uv: PASS
- just: PASS
- GitHub CLI: PASS
- Git Bash selection: PASS
- cygpath selection: PASS
- SSH selection: PASS
- Python compatibility: PASS
- python3 compatibility: PASS
- just compatibility: PASS
- canonical origin: PASS
- B3-002 line-ending contract: PASS
- root `just` front door: PASS
- `just local` front door: PASS
- effective `exe.dev` SSH config: PASS
- effective synthetic `*.exe.xyz` SSH config: PASS

External sqlite3 was reported as a non-fatal warning.

zsh was reported absent and non-required on Windows.

The host doctor result was:

`SSSF Windows host doctor: OK`

The bootstrap then reported:

`SSSF Windows session ready.`

## PATH normalization proof

After bootstrap:

- Git `bin` count = 1
- Git `usr\bin` count = 1
- all PATH entries were unique

The effective executable order was:

- Git from `C:\Program Files\Git\bin`
- Bash from `C:\Program Files\Git\bin`
- cygpath from `C:\Program Files\Git\usr\bin`
- SSH from `C:\Program Files\Git\usr\bin`

Windows OpenSSH remained installed but no longer won resolution precedence.

## Idempotence proof

The PATH after the first successful bootstrap was captured.

The bootstrap was then run a second time with:

`--sandbox`

The second host doctor again passed.

The composed sandbox doctor reported:

`sbx doctor: OK`

The PATH after the second bootstrap was byte-for-byte identical to the PATH after the first bootstrap.

Observed result:

`PASS: bootstrap PATH idempotent`

## Persistent-state proof

The post-bootstrap HKCU PATH was re-read from the Windows registry.

It remained the previously observed persistent user PATH and was not rewritten by B3-003.

The post-bootstrap HKLM PATH is independently re-checked before the B3-003 candidate commit.

B3-003 does not intentionally write:

- `HKCU\Environment\Path`
- machine PATH
- Git global configuration
- SSH private keys
- permanent shell aliases

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
- passing B3-002 line-ending validator;
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

This retains the existing sandbox-specific checks rather than duplicating them.

The composed sandbox doctor passed during the B3-003 bootstrap proof.

## Line-ending boundary

B3-002 established:

`* text=auto eol=lf`

B3-003 does not weaken that policy.

The B3-002 line-ending validator passed after the Windows shell and bootstrap changes.

The new `.cmd` bootstrap remains governed by the repository LF policy because actual Windows execution succeeded with that representation.

No CRLF exception was required.

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
11. just satisfies the compatibility floor required by the conditional shell settings.
12. Bun, uv, just, GitHub CLI, and Git resolve.
13. Effective SSH policy for `exe.dev` and a synthetic `*.exe.xyz` host passes.
14. The B3-002 line-ending validator passes.
15. External sqlite3 absence is non-fatal and remains assigned to B3-004.
16. `--sandbox` composes and passes the existing sandbox doctor on the proven host.
17. Persistent user and machine PATH values are unchanged.
18. `git diff --check` passes.
19. Python source compiles.
20. B3-002 remains frozen at `8df2a9bc535bc8f5be50742053dc6ebf520c54ee`.

## Evidence

Pre-candidate Windows execution proof: PASS.

Candidate commit and exact-candidate Windows proof: pending.

## Result

Pending exact candidate proof.