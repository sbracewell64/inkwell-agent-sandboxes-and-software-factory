# B4-002 — Owned Executor Supervisor and Strict Pi Adapter

**Status:** CORRECTED CANDIDATE; FRESH EXACT-HEAD REVIEW AND CI REQUIRED
**Starts from:** `a984f6cf0a89503d3db8855ccd820b83e9ee60a1`
**Reviewed implementation:** `2291725cf0782b40ce01a17d29b6415a51b130de`
**Proof workflow run:** `31911734134`
**Supervisory ruling:** Browser Sol `5304605032`
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
- a shared native-attempt budget claimed only after cancellation is observed,
  plus a recheck immediately before the custodian starts;
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
- typed observation-delivery CNO that preserves the primary provider outcome
  and cleanup evidence when a post-capture callback fails;
- typed evidence reservation/persistence CNO for every filesystem stage, with
  no parsing, callback, durable-digest claim, or partial-target reuse;
- strict malformed/missing/duplicate terminal-event handling;
- shell-zero structured-error precedence;
- observable native-retry accounting against the common budget;
- requested/resolved target and effort, terminal stop/error, source-classed
  usage/cost, timeout/cancel, process/cleanup, attempts and evidence digests.
- immutable per-`message_end` resolved-target evidence with event/message
  identity, rejecting the first incomplete or drifting tuple so later matching
  output cannot cure earlier fallback evidence.
- structured provider errors remain the primary verdict while any incomplete
  or drifting target tuples remain attached as secondary typed observations.

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
8. escaped, immediate-parent-exit, and TERM-handler late-fork descendants that
   must be killed and verified absent;
9. stdout and event overflow;
10. live and late cancellation races, a cancellation already set before
    invocation, and a cancellation arriving during pre-launch setup;
11. custodian startup/IPC, spawn callback, event callback, and evidence-storage
    failures with typed CNO and retained primary evidence where observable;
12. explicit unsupported-Windows Job Object refusal;
13. fully qualified target, explicit effort, exact tool policy, strict Pi argv
    controls, and immutable requested-versus-resolved target enforcement.

The check is the seventh repository-owned offline CI manifest entry. Linux runs
all process fixtures. Windows runs the nonempty static/parser/refusal proof and
reports runtime execution as CNO; it does not skip into a false pass.

## Exact reviewed pull-request proof

Browser Sol ruling `5304605032` rechecked canonical `main` at
`a984f6cf0a89503d3db8855ccd820b83e9ee60a1` and PR 7 as open, non-draft,
unmerged, and clean at exact reviewed head
`2291725cf0782b40ce01a17d29b6415a51b130de`. Workflow run `31911734134`
completed the required nonempty Linux and Windows checks successfully on that
exact head.

The Linux result projects the full provider-free process fixtures. The green
Windows result proves that the static/parser controls execute and unsupported
provider execution fails closed with the required typed refusal. It does
**not** prove Windows provider execution or descendant containment:
`WINDOWS_PROVIDER_EXECUTION` remains `CNO/REFUSED` until a proven Job Object
path lands.

Subsequent executable corrections make this ruling provenance only. The current
candidate requires fresh exact-candidate review and fresh nonempty Linux and
Windows checks before landing; neither acceptance nor checks may be inferred
from ruling `5304605032` or run `31911734134`.

## Pre-launch cancellation correction

Review of head `64fbd0e3be7383e7cd5294eba6923d686d012c51` found that
`supervise()` claimed the attempt budget and started the custodian before it
observed cancellation at all, so a cancellation already set at entry still
spent budget and still launched a provider. The correction observes
cancellation before `budget.claim()` and rechecks it immediately before the
custodian starts, returning typed `cancelled-before-launch` /
`could-not-observe` with `cancelled` set.

Accounting stays explicit rather than convenient:

- observed before any claim: no attempt number, no budget use, no custodian or
  provider identity, and no spawn, exit, or event callback;
- observed after a claim: the claim is already spent and stays spent, and the
  result reports that attempt number. Spent work is never refunded to make
  accounting look cheaper.

Both branches are proven by fixtures that were first watched red against the
unfixed head. The pre-set control failed there for the intended reason: it
consumed one attempt, produced a provider process, produced a custodian, and
invoked both spawn and exit callbacks. Platform and contract refusals keep
precedence over the cancellation check because they are pure and name a more
specific defect, and neither claims an attempt.

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
- Cancellation observed after the custodian starts remains governed by the
  existing duplex cleanup protocol: the provider may already be live, so that
  case still spends its attempt and is typed `cancelled` with verified cleanup
  rather than refused. This correction narrows the pre-launch window only; it
  does not claim the post-launch window never launches a provider.
- No credential transport is part of this increment, so it does not by itself
  authorize a live provider call.
- Raw callbacks occur after bounded output is durably retained, not live during
  process execution.

## Acceptance state

Local focused fixtures and the full provider-free project gate passed for the
reviewed implementation. Browser Sol ruling `5304605032` accepted workflow run
`31911734134` as nonempty exact-head Linux and Windows proof for
`2291725cf0782b40ce01a17d29b6415a51b130de`, while preserving Windows provider
execution as `CNO/REFUSED`.

That ruling is stale for landing after executable corrections. The corrected
candidate remains CNO until fresh exact-candidate review and fresh nonempty
Linux and Windows checks complete successfully on its own exact head. An
absent, pending, mismatched, skipped, cancelled, neutral, timed-out, or failing
review or check is not PASS and does not authorize landing.
