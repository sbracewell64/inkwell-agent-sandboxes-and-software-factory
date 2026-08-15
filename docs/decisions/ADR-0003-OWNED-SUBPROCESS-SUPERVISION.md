# ADR-0003 — SSSF-Owned Subprocess Supervision

**Status:** Accepted for B4-002 candidate
**Date:** 2026-08-17

## Context

The Pi interface directly owned a `Popen` read loop. It closed stdin, but did
not bound wall time, output, retries, or process-tree cleanup, and treated a
shell-zero provider error as success. Ambient Pi settings could also enable
sessions, resources, project trust, model fallback, and native retries outside
SSSF accounting.

## Decision

SSSF has one provider-neutral subprocess supervisor in
`adws/adw_modules/subprocess_supervisor.py`. It accepts only an argv array, an
absolute cwd, and environment names explicitly allowlisted by its caller. It
closes stdin and owns monotonic timeout/cancellation, byte bounds, attempt
budget, reap, Unix process-group termination, bounded TERM-to-KILL escalation,
tracked descendant cleanup, identity-aware verification, typed evidence, and
three-valued failure reasons.

Linux execution uses a dedicated spawned custodian per attempt. Only that
helper becomes a child subreaper, launches the provider process, and repeatedly
rescans adopted children through cleanup, so coordinator threads and their
unrelated children remain outside its custody. Missing terminal IPC or an
unverified empty custody set is could-not-observe.
The custodian also owns an independent monotonic cleanup watchdog and duplex
cleanup-request/acknowledgement protocol. Coordinator startup, callback, pipe,
or deadline failures cannot terminate the subreaper; without an observable
empty-tree acknowledgement they return cleanup-unverified with custodian
identity while the helper retains custody and completes bounded cleanup.

`adws/adw_modules/pi_json_adapter.py` is the strict Pi JSON/print projection.
It requires an exact provider/model, explicit thinking and tool allowlist, and
passes flags that disable sessions, extensions, skills, prompt templates,
context files, and project approval. It creates an isolated, credential-free
Pi settings directory with agent/provider retries and compaction disabled.
Raw bounded stdout is fsynced before JSON parsing or event callbacks. A
structured provider error remains failure regardless of process exit status.
Event callback exceptions disable further delivery and return typed
observation-delivery CNO while retaining the separately classified provider
outcome, raw digest, process result, and cleanup evidence.
Observable native retry events are counted and charged to the same budget; a
retry despite the disabled policy fails.

No model catalog or credential store is consulted. Provider authentication or
subscription transport is not established by this increment.

## Windows decision

The candidate does not claim that `CREATE_NEW_PROCESS_GROUP` is equivalent to
a Unix process group. Until an atomic, proven Windows Job Object assign/kill/
verify path exists, Windows native launch returns typed
`could-not-observe`/`windows-job-object-unavailable` before spawning. Windows
CI still executes the strict static/parser controls and the refusal fixture.

## Consequences

- Existing Pi configurations that request extensions now refuse rather than
  silently weakening the strict adapter.
- Existing same-session continuation is not available through this adapter;
  each invocation is one bounded, no-session attempt.
- Context-window catalog lookup is unavailable and reports zero through the
  legacy `PiResult` compatibility object.
- Linux can execute the full deterministic process fixtures. Windows remains
  an honest execution CNO, not a portability pass.
- Host no-tools/read-only transport and accounting adapters remain separate
  increments.
