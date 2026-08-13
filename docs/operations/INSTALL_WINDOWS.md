# Windows Installation Runbook

This runbook records the Windows Command Prompt path that produced the proven baseline.

## Repository

```bat
E:
mkdir SSSF
cd /d E:\SSSF
git clone https://github.com/disler/inkwell-agent-sandboxes-and-software-factory.git .
git status
```

## Host tools

Required and proven:

- Git for Windows
- Bun
- uv
- just

Installed locations in the proof environment included:

- Bun: `%USERPROFILE%\.bun\bin\bun.exe`
- uv: `%USERPROFILE%\.local\bin\uv.exe`
- just: `%USERPROFILE%\.local\bin\just.exe`
- Git Bash: `C:\Program Files\Git\bin\sh.exe`
- cygpath: `C:\Program Files\Git\usr\bin\cygpath.exe`

## Command Prompt PATH requirement

A new Command Prompt may require:

```bat
set "PATH=C:\Program Files\Git\bin;C:\Program Files\Git\usr\bin;%PATH%"
```

Without `usr\bin`, `just` may fail with:

`could not find cygpath executable`

## Environment

Copy:

```bat
copy .env.sample .env
notepad .env
```

Two distinct OpenRouter fields are used:

- `OPENROUTER_PROVISIONING_KEY` — management/provisioning key, host only
- `OPENROUTER_API_KEY` — local inference key

Never commit `.env`.

## exe.dev SSH

A dedicated Ed25519 identity was used.

SSH config pattern:

```text
Host exe.dev *.exe.xyz
    IdentitiesOnly yes
    IdentityFile ~/.ssh/id_ed25519_exe
    StrictHostKeyChecking accept-new
```

The wildcard is important because SSSF probes newly created `<run-id>.exe.xyz` hosts non-interactively.

## Inkwell dependencies

```bat
cd /d E:\SSSF\apps\inkwell
bun install
cd /d E:\SSSF
```

## Preflight

```bat
just sbx manage doctor
```

Required result:

`sbx doctor: OK`

## Payload test

```bat
just inkwell test
```

Baseline:

- 30 pass
- 0 fail

## Required local source portability patches

See `baseline/BASELINE.md` and `baseline/FREEZE_PROCEDURE.md`.

Do not hide these as machine quirks; they are part of the current local platform contract until removed by a tested portability increment.
