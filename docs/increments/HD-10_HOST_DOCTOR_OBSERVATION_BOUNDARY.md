# HD-10 — Host Doctor Observation Boundary

**Status:** IMPLEMENTED, AWAITING REVIEW
**Starts from:** `c192693ec1f09156fd2ce8d1a9e6ce8470e9bd96`

## Problem

HD-09 closed the observation boundary inside `docs/validation/check_obs_query.py`
and gave `tools/ci_gate.py` a channel for a validator to report its own failure
to observe. The adjacency scan it opened — inspect every sibling owner that
spawns child tools from inside a Python wrapper — leaves one instance open:
`tools/windows_host.py`, the B3-003 Windows host doctor.

Its `run()` wrapper called `subprocess.run` with no guard, so a host without
`just` produced no result at all. On this repository's own head the doctor
narrowed the same distinction three separate ways in one invocation:

```
FAIL  just compatibility — could not parse ''
FAIL  observability query contract — B3-004 sqlite-free observability: CNO
- could-not-observe: tool unavailable: just (required by the just obs integration path)
Traceback (most recent call last):
  File "tools/windows_host.py", line 710, in doctor
    root_front = run(["just"])
FileNotFoundError: [Errno 2] No such file or directory: 'just'
```

- a version contract fabricated from a tool that never ran (`could not parse ''`),
- a child that had already declared could-not-observe, exit `125`, read back as
  a FAIL the child never earned,
- an uncaught `FileNotFoundError` at the front-door probe, which ended the run
  before the second front door, both `ssh` probes, the optional-tool inventory,
  the sandbox doctor and the terminal verdict were ever reached.

With `git` also absent the crash moved earlier, to `git remote get-url origin`.

## Desired outcome

The host doctor reports a missing child tool as could-not-observe: never a
crash, and never a FAIL. Failure to observe and predicate failure stay distinct,
and reclassifying one as the other never upgrades a property to a pass.

## Non-goals

- No new framework and no second result owner. `tools/ci_gate.py` already owns
  the reserved exit code and the reason-line shape; this increment consumes
  them.
- No change to what any host predicate asserts. The doctor's own installed-tool
  predicate is deliberately unchanged: an absent tool is a genuine answer to
  "is this tool installed on the host", so it stays a FAIL finding.
- No change to `bin/sssf-windows.cmd`, which already propagates any nonzero
  doctor exit.

## Design

`tools/windows_host.py` imports HD-09's landed contract from `tools.ci_gate`:
`COULD_NOT_OBSERVE_EXIT`, `CNO_REASON_PREFIX` and `child_cno_reason`.

- `ChildObservation` is one child spawn's three-valued result. `returncode` is
  `None` exactly when no observation was reached, and `reason` names why.
- `run()` returns one instead of raising. An unspawnable tool and an unreadable
  working directory (`OSError`) are could-not-observe; so is a child that stops
  answering, bounded by `SSSF_CHILD_TIMEOUT_SECONDS` (default 30); so is a child
  that exits `COULD_NOT_OBSERVE_EXIT`. That code is repository-reserved for
  every child the doctor spawns, not only validators; named reasons are carried
  through and a bare reserved exit uses the shared fallback reason. A malformed,
  non-finite or non-positive timeout setting deterministically falls back to 30
  seconds so configuration cannot prevent the doctor from reporting a result.
- `Doctor` gains `cno()` alongside `ok`/`fail`/`warn`/`info`, printing the
  `could-not-observe: <reason>` shape the repository already uses.
- `check_child_probe()` is the single seam every returncode-only probe now runs
  through: unobserved is CNO, nonzero is FAIL, zero is ok.
- `check_tool()` keeps its FAIL for an absent tool and additionally returns the
  reason no version was read. `check_version_contract()` consumes that reason:
  a version that was never read is CNO, while a tool that did answer
  unparseably or below the minimum still FAILs.
- `terminal_disposition()` keeps HD-09's precedence. An observed defect outranks
  a failure to observe, so a doctor that judged anything false still exits `1`
  and prints `FAILED`. A doctor that judged nothing false but left something
  unobserved prints `COULD-NOT-OBSERVE` and exits `COULD_NOT_OBSERVE_EXIT` —
  red, never a pass.

`emit-path` is unchanged. Constructing the bootstrap PATH is an action, not an
observation, and its `RuntimeError` for an unlocatable Git for Windows is an
action failure rather than a narrowed verdict.

## Scope boundary observed and deliberately left alone

`docs/validation/check_ci_contract.py` also references `just`, at its
expected-command tuple. That is a declared constant, not an invocation, and the
validator already proves its own CNO path; it is not an instance of this defect.

The doctor's `os.name != "nt"` row is a directly observed host property with no
child spawn. Running on a non-Windows host is observed-bad for "is this a
Windows host", not a failure to observe it, so that row keeps its FAIL.

## Proof

`tests/test_windows_host_observation_boundary.py` drives the real module and the
real executable:

- an absent child tool returns a result naming the tool, and does not raise;
- a wedged child is a timed-out observation;
- an unreadable working directory is could-not-observe;
- a child that declared `could-not-observe: <reason>` and exited 125 is believed,
  not re-read as a FAIL;
- a bare reserved exit 125 is also could-not-observe with the shared fallback,
  while a present child exiting another nonzero code remains a doctor FAIL;
- invalid, non-finite and non-positive child timeout settings keep the module
  importable and use the 30-second default;
- an absent front-door tool is a CNO row and not a doctor FAIL;
- an absent `ssh` makes the `ssh config` probe CNO;
- an absent tool stays a doctor finding — `FAIL <tool> — not found on PATH`;
- a version that was never read is CNO and never `could not parse ''`;
- **the boundary cannot mask a genuine failure**: a front-door tool that is
  present and exits nonzero is still FAIL, an unparseable version from a tool
  that did run is still FAIL, and a version below the minimum is still FAIL;
- **non-vacuity**: with the tool present the doctor really executes it — the
  stub records that it ran — and the probe reports `ok`; a version at the
  minimum passes;
- an observed defect outranks a failure to observe, and a could-not-observe
  doctor never exits 0;
- end to end, with every child tool absent, the real `tools/windows_host.py
  doctor` returns a full three-valued report with no traceback and both front
  doors marked CNO.

Each half was watched red before it was believed. Reverting the `OSError` guard
reds 5 cases; recording CNO as a doctor FAIL reds 4; letting a CNO doctor exit 0
reds 1; parsing a version that was never read reds 1; reading a child's declared
CNO as a verdict reds 1.

Offline gate at this head: all ten `ci/checks.json` rows keep the statuses they
had before this change (8 `observed-good`, 2 `could-not-observe` because this
host has no `just`), conclusion still `could-not-observe` and still red. The
host doctor on the same host moves three rows off a manufactured verdict —
`just compatibility`, `python compatibility` and `observability query contract`
become CNO — and now reaches its own terminal verdict instead of crashing.
