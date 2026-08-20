# Windows Installation Runbook

This runbook describes the supported Windows Command Prompt path after B3-004.

## Repository

Clone the operator-owned canonical repository:

```bat
E:
mkdir SSSF
cd /d E:\SSSF
git clone https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git .
git status
```

## Strict LF gate

Before bootstrap or execution, run the one authoritative line-ending validator:

```bat
python docs/validation/check_line_endings.py --require-worktree-lf
```

The validator always requires the watched execution-sensitive files to report
`i/lf w/lf`, even if `--require-worktree-lf` is omitted. The explicit command
above is the supported Windows invocation and is also what the host doctor
runs.

A red result is terminal. The validator reports positive contract violations as
`observed-bad` and unavailable evidence as `could-not-observe`; neither is a
pass. It does not rewrite the working tree.

If the only defect is stale CRLF materialization, preserve local work first and
require `git status --short` to be empty. Then explicitly re-materialize only
the watched files from the unchanged index:

```bat
git checkout-index --force -- .gitattributes justfile just/sandbox/lifecycle/fill.just just/sandbox/lifecycle/setup.just sandbox_mount/guest/provision.sh sandbox_mount/host/run_record.py docs/baseline/PROOF_MATRIX.md
python docs/validation/check_line_endings.py --require-worktree-lf
```

`git checkout-index` does not modify the index. The clean-tree precondition
makes this a content-preserving line-ending repair rather than an overwrite of
developer work. Bootstrap performs validation only and never runs this
remediation automatically.

## Bootstrap and host doctor

Run:

```bat
bin\sssf-windows.cmd
```

The bootstrap invokes the host doctor, which invokes the exact strict LF
command above and does not print the session-ready message when that check is
non-passing.

## FirstMate double-click front door

After the tracked launcher is installed in the canonical checkout, double-click
this shortcut target or run it from any Command Prompt directory:

```bat
E:\SSSF\bin\sssf-firstmate.cmd
```

The front door always validates and enters `E:\SSSF` through WSL before handing
off to FirstMate's existing `fm-launch.sh` primary path. It prints only the
project, canonical repository, root, and handoff identity without printing
credentials, auth-home paths, `head=`, or `branch=`. FirstMate remains
responsible for harness selection, project registration, supervision,
admission, and work decisions.

Use `--print-menu` to validate the root/configuration and render FirstMate's
menu without creating a session. `--detach` is reserved for bounded host
validation; it selects the installed Claude entry and returns after the
FirstMate primary starts. Unknown arguments refuse visibly.

The front door does not run `just local cc`, schedule work, mutate Docker/SBX
state, or activate Wayfinder or DSH. If WSL, the canonical checkout, the
canonical origin, the FirstMate launcher/admission/session-start scripts, or the
registered `sssf` project is missing, it refuses with a repair instruction.
