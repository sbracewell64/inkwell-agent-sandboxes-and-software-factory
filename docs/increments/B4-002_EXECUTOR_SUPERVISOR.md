# B4-002 — Owned Executor Supervisor and Strict Pi Adapter

**Status:** CANDIDATE — LOCAL PROVIDER-FREE PROOF COMPLETE; EXACT-HEAD CI CNO
**Starts from:** `a984f6cf0a89503d3db8855ccd820b83e9ee60a1`
**Decision:** `docs/decisions/ADR-0003-OWNED-SUBPROCESS-SUPERVISION.md`

## Problem

SSSF did not own a complete terminal contract for provider CLI processes.
Direct Pi launch could hang, overrun evidence, leak descendants, hide native
retries, or return shell zero with a structured provider error. Ambient Pi
resources and fuzzy model resolution could also alter the requested execution.

## Desired outcome

Provide one provider-neutral subprocess owner and one strict Pi JSON/print
adapter whose launch, budget, evidence, cleanup, and terminal semantics are
bounded and deterministic without calling a provider.

## Implementation

`adws/adw_modules/subprocess_supervisor.py` owns:

- shell-free argv-array launch with absolute cwd and exact environment-name
  allowlists;
- closed stdin;
- monotonic wall timeout and cancellation;
- bounded stdout/stderr bytes;
- a shared native-attempt budget;
- a new Unix process group, TERM grace, KILL escalation, child reap, Linux
  descendant identity tracking, escaped-descendant cleanup, and bounded
  group/descendant absence verification;
- typed terminal state, process identity, cleanup evidence and SHA-256 digests;
- `observed-good`, `observed-bad`, and `could-not-observe` failure semantics.

`adws/adw_modules/pi_json_adapter.py` adds:

- exact, fully qualified provider/model and explicit effort;
- JSON print mode, exact built-in tool allowlist, and no fallback;
- explicit no-session, no-extension, no-skill, no-prompt-template,
  no-context-file and no-approval flags;
- isolated credential-free settings disabling native retries, provider retries,
  compaction, project trust, packages, and telemetry/update startup work;
- durable bounded raw events before parsing;
- strict malformed/missing/duplicate terminal-event handling;
- shell-zero structured-error precedence;
- observable native-retry accounting against the common budget;
- requested/resolved target and effort, terminal stop/error, source-classed
  usage/cost, timeout/cancel, process/cleanup, attempts and evidence digests.

The legacy `agent_pi.run` now delegates native execution to this adapter. It no
longer reads Pi's user model catalog or launches a separate list-models process.

## Deterministic proof

`docs/validation/check_executor_supervisor.py` and
`docs/validation/fixtures/fake_pi_child.py` make no provider/model call. They
cover:

1. success and typed usage/cost evidence;
2. shell-zero structured provider error;
3. malformed, missing and duplicate terminal events;
4. an inherited-stdin watched-red control plus the closed-stdin parent-tail
   marker regression;
5. observable hidden retry and common-budget charging;
6. monotonic timeout;
7. ignored TERM and KILL escalation;
8. an escaped descendant that must be killed and verified absent;
9. stdout and event overflow;
10. live and late cancellation races;
11. explicit unsupported-Windows Job Object refusal;
12. fully qualified target, explicit effort, exact tool policy, and strict Pi
    argv controls.

The check is the seventh repository-owned offline CI manifest entry. Linux runs
all process fixtures. Windows runs the nonempty static/parser/refusal proof and
reports runtime execution as CNO; it does not skip into a false pass.

## Refusal conditions

Launch refuses, without a child, for invalid argv/cwd/environment bounds,
exhausted attempt budget, non-allowlisted or credential/auth-home/cookie/token
environment names, unsupported platform cleanup, bare/fuzzy model targets, implicit or invalid thinking,
implicit/duplicate/unknown tools, extensions, or incompatible event bounds.
Pi runtime failure is typed when output or event bounds are exceeded, terminal
JSON is malformed/non-unique/missing, retry evidence does not reconcile, a
native retry violates policy, process exit is nonzero, cancellation/timeout
wins, descendants outlive the parent, or cleanup cannot be verified.

## Boundaries and non-goals

This increment reads, copies, mounts, logs, and places in argv no credential,
auth home, cookie, or token. Its environment helper copies only process
mechanics such as PATH/locale/temp names. It does not change guest/sandbox or
provider lifecycle, browser/GitHub/billing state, B3 acceptance, PR 1,
OpenRouter roster/accounting, DSH, migration, expansion, or unrelated
increments. A subscription CLI is not treated as B3-equivalent. Host
no-tools/read-only transport and accounting adapters remain separate.

## Residual limitations

- Windows child execution is CNO until a proven Job Object path lands.
- Linux launch delegates child-subreaper custody to a dedicated spawned helper
  so descendants remain discoverable after their original parent exits without
  capturing coordinator-thread children; launch refuses as CNO if custody or
  bounded terminal IPC cannot be verified.
- Coordinator failure requests cleanup over duplex IPC and waits for an
  empty-tree acknowledgement; missing acknowledgement is cleanup-unverified
  with custodian identity, and the coordinator never kills the subreaper.
- No credential transport is part of this increment, so it does not by itself
  authorize a live provider call.
- Raw callbacks occur after bounded output is durably retained, not live during
  process execution.

## Acceptance state

Local focused fixtures and the full provider-free project gate must pass.
Acceptance additionally requires nonempty Linux and Windows checks on the exact
PR head. Until those checks exist and match, this increment remains CNO and
must not land.
