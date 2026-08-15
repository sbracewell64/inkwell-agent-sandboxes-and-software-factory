# Windows Installation Runbook

This runbook describes the supported Windows Command Prompt path prepared through B3-005 PRE_CERTIFICATION.

## Repository

Use a newly allocated Windows-native path when proving portability. Do not treat an already-bootstrapped checkout as fresh-environment evidence.

```bat
mkdir E:\SSSF-new
cd /d E:\SSSF-new
git clone https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git .
git status --porcelain=v2 --branch
```

For an accepted increment or proof, select and record the exact branch/tag and 40-character commit before relying on results.

## Native pre-bootstrap controls

A fresh Windows process constructed from persistent user/machine state should not require Git Bash PATH augmentation merely to enter the root Just surfaces.

Record:

```bat
echo %PATH%
where git
where ssh
where sh
where cygpath
where zsh
just
just local
```

Before bootstrap, supported persistent state may expose Git through:

`C:\Program Files\Git\cmd`

The repository bootstrap must not rely on persistent:

- `C:\Program Files\Git\bin`
- `C:\Program Files\Git\usr\bin`

`just` and `just local` must work before those session paths are added. Missing evidence is not a pass.

## Approved host configuration

Create ignored `.env` through the existing approved host configuration mechanism and provide only:

```text
OPENROUTER_PROVISIONING_KEY=<host-only value>
```

Do not print or commit the value. Do not place the host provisioning key or a host-native authentication home in a guest. FILL mints and injects only the bounded disposable runtime key.

The host's existing exe.dev SSH configuration must resolve a dedicated identity, `IdentitiesOnly yes`, and `StrictHostKeyChecking accept-new` for both `exe.dev` and `*.exe.xyz`.

## Bootstrap and doctor

From Command Prompt:

```bat
bin\sssf-windows.cmd --sandbox
```

The command modifies only the current session. It:

- discovers Git for Windows;
- deduplicates PATH;
- prepends Git `bin` and `usr\bin`;
- selects Git Bash `sh`, `cygpath`, and Git OpenSSH;
- validates the Windows toolchain and versions;
- validates canonical repository ownership;
- validates the B3-002 line-ending contract;
- validates B3-004 sqlite-free observability;
- validates root `just` and `just local`;
- composes `just sbx manage doctor` when `--sandbox` is supplied.

Persistent `HKCU\Environment` and `HKLM\...\Environment` PATH values must remain unchanged.

## SQLite-free observability

External `sqlite3` is not a Windows host requirement.

```bat
where sqlite3
python docs\validation\check_obs_query.py --require-no-external-sqlite3
```

The validator uses Python standard-library sqlite3 and read-only database access. A missing database must fail explicitly without being created.

## Sandbox lifecycle

Use a unique run ID and retain every phase's output:

```bat
just sbx lifecycle create <run-id>
just sbx lifecycle fill <run-id>
just sbx lifecycle setup <run-id>
just sbx lifecycle observe <run-id>
```

Before relying on guest results, independently record:

```bat
just sbx run cmd <run-id> "git remote get-url origin && git rev-parse HEAD && git status --porcelain=v2 --branch"
```

Repository, exact SHA, and clean status must agree with the host run record and SETUP Gate A.

SETUP C/D/E acceptance requires one typed result marker reconciled against complete remote output and transport status. A failure diagnostic, missing marker, malformed marker, unavailable model/cost observation, or transport contradiction cannot produce downstream PASS. Unavailable credits classify the gate CNO/HOLD and stop setup; do not purchase credits merely to make a portability proof green.

## Teardown

Teardown is explicit and repository-owned:

```bat
just sbx lifecycle teardown <run-id>
```

Do not manually clean around the lifecycle. Required order is:

`spend -> artifacts -> harvest -> revoke -> destroy -> close -> gate`

Retain evidence of:

- artifact custody before revocation/destruction;
- harvest result;
- runtime-key revocation;
- runtime-key file removal;
- VM absence;
- closed run record;
- no residual runtime-key material.

A failed or unavailable control is CNO, never PASS.

## B3-005 PRE_CERTIFICATION note

B3-005's first sandbox exposed a contradictory setup acceptance defect and was rejected as final evidence. A repaired candidate was then proved from a new fresh clone and sandbox: unavailable credits correctly stopped SETUP as CNO/HOLD with no downstream PASS, and teardown completed cleanly. Browser Sol passed the automated Windows-native method only for proving environment freshness at exact reviewed head `63bc5792e0db4d6fb152a947648e161ae47f1b14`; it does not prove GUI/Explorer/session equivalence. Roster, typed final C/D/E marker, OBSERVE/end-to-end, and no-CI remain CNO/HOLD, while merge/main/tag/freeze remain held. Do not use the PRE_CERTIFICATION record to merge, advance canonical `main`, or establish a final B3 freeze tag.

Detailed evidence:

- `docs/increments/B3-005_FRESH_WINDOWS_CLONE_PROOF.md`
- `docs/evidence/B3-005_FRESH_CLONE_PROOF.md`
- `docs/evidence/B3-005_ACCEPTANCE_CORRECTION_REPROOF.md`
- `docs/evidence/B3-005_WINDOWS_NATIVE_EQUIVALENCE.md`
- `docs/evidence/B3-005_BROWSER_SOL_RULING.md`
