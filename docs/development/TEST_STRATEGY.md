# Test and Verification Strategy

## Verification hierarchy

Prefer executable evidence.

### Level A — deterministic code

Examples:

- unit tests,
- integration tests,
- exit codes,
- JSON schema validation,
- file existence/non-empty gates,
- Git status/SHA checks,
- HTTP status,
- process liveness.

### Level B — invariant reconciliation

Examples:

- run record vs live VM,
- key hash vs OpenRouter key list,
- expected base SHA vs guest HEAD,
- declared artifact vs filesystem.

### Level C — semantic review

Use an independent agent/model only when the claim is inherently semantic.

Examples:

- does the implementation satisfy ambiguous product intent?
- is an architecture choice coherent?

## Baseline examples

- planner claim about artifacts: Level A filesystem gate
- test suite: Level A deterministic command
- VM liveness: Level B control plane + SSH
- free model role suitability: representative agent fixture plus deterministic gates

## GitHub projection

The ordinary pull-request and `main` push gate is `.github/workflows/ci.yml`.
It runs the repository-owned manifest on Linux and Windows without provider,
credential, or sandbox access. `tools/ci_gate.py` retains one of three statuses
for every attempted check:

- `observed-good` — the check executed and returned success;
- `observed-bad` — the check executed and returned failure;
- `could-not-observe` — discovery, tooling, timeout, or cancellation prevented
  a result, or the check itself reported that it could not observe.

GitHub success is projected only when discovery is nonempty, all discovered
checks execute, and every result is `observed-good`. The calibrated negative
controls live in `docs/validation/check_ci_contract.py`.

A validator is the owner of the distinction between *its predicate is false*
and *it could not run its predicate*. When a required child tool is absent or
unspawnable, stops answering, or the host lacks a primitive the check needs, the
validator exits `tools/ci_gate.py`'s reserved `COULD_NOT_OBSERVE_EXIT` (125) and
prints one `- could-not-observe: <reason>` line per reason, naming the tool. The
gate runner records that row as `could-not-observe` with those reasons, never as
`observed-bad`. Every other nonzero exit stays `observed-bad`: an observed defect
outranks a failure to observe, so a validator that judged anything reports FAIL
even when part of its evidence was unavailable. `could-not-observe` is a real
result and never a pass — the gate still exits red on it.

`tools/windows_host.py` owns the same boundary outside the gate. The host doctor
prints `CNO` rows beside `ok`/`FAIL`, exits `COULD_NOT_OBSERVE_EXIT` when it
judged nothing false but left something unobserved, and exits 1 whenever it did
judge something false. Its installed-tool predicate is deliberately untouched —
an absent tool answers "is this tool installed" and stays a FAIL finding — while
every predicate derived from a child that never ran is could-not-observe:
version contracts, both `just` front doors, the `ssh config` probes, the
canonical-origin probe, and any child that declared its own observation failure.
`tests/test_windows_host_observation_boundary.py` holds those controls, with the
non-vacuity half proving a present tool is really executed and a
present-but-failing tool is still FAIL.

The B4-002 provider-free process contract is
`docs/validation/check_executor_supervisor.py`. Its deterministic fake Pi child
covers successful typed evidence plus watched-red stdin inheritance,
structured shell-zero errors, protocol corruption, hidden retry, timeout,
ignored TERM, escaped descendants, output bounds, cancellation races
(live, late, already set before invocation, and arriving during pre-launch
setup), fixed-allowlist and sensitive-name environment refusals before launch,
and unsupported Windows cleanup. The environment controls include a
credential-style name outside the fragment vocabulary so the proof does not
depend on enumerating every secret word. Linux executes process behavior;
Windows executes static/parser controls and proves typed refusal before launch
rather than turning missing Job Object containment into a pass.

`docs/validation/check_production_extension_path.py` guards the shipped
extension-bearing ADW path. It refuses to pass unless a shipped roster declares
a nonempty `harness_engineering` agent, then drives each one through the real
`agent_pi` launch path against a local recording stub and asserts every
configured extension is forwarded as `-e`. It exists because a strict-adapter
rewrite once rejected those extensions and the rest of the gate did not notice.

`tests/test_protected_evaluator_surface.py` proves the frozen evaluator
surface: a maker or optimizer is refused the acceptance machinery that grades
it, a legitimate evaluator change is an explicit roster revision that starts a
new generation and reports evidence bound to the old one as no longer current,
and a file outside the declared property scope stays ordinary work. It carries
its own negative controls, because two of its claims are properties to
*preserve*: over-freezing the declaration turns the property-scope assertion
red, and reversing the session-runtime-first precedence turns the reportability
assertion red. An undeclared, unresolvable or unreadable surface is
`could-not-observe`, never an intact evaluator, and failed Git snapshot
enumeration refuses enforcement instead of representing an observed-clean tree.
The snapshot pins its armed commit and tree. In-phase commits remain ordinary
work, while committed and uncommitted deltas are both compared with that pin;
an unavailable pin is a named refusal rather than an implicit new baseline.

`docs/validation/check_repository_ownership.py` is intentionally not in this
offline gate because it queries GitHub and the canonical remote. Repository and
sandbox source invariants that do not need the network remain enumerated.

## Anti-pattern

Do not add an LLM judge for a claim code can settle exactly.
