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
  a result.

GitHub success is projected only when discovery is nonempty, all discovered
checks execute, and every result is `observed-good`. The calibrated negative
controls live in `docs/validation/check_ci_contract.py`.

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

`docs/validation/check_derived_source_provenance.py` is the preventive gate for
any future assessment-derived source. It reports two results that must never be
collapsed: the exit code carries the CONTRACT state, and a separate printed line
carries a four-valued POPULATION verdict with precedence
`FAIL > CANNOT_OBSERVE > NOT_APPLICABLE > PASS`. Its calibration builds a
throwaway assessment input from pinned Git object identities, bundles it, and
drives a throwaway destination through three states so the empty, unrecorded,
and honest cases are each reachable. Those fixtures are calibration-only and are
not an import path.

Read a green result here precisely. It means the gate is installed and
red-capable. It does not mean any derived source is certified, because no
derived source exists; the population is `NOT_APPLICABLE`, which is a
could-not-observe result. See `docs/reference/DERIVED_SOURCE_PROVENANCE.md`.

`docs/validation/check_repository_ownership.py` is intentionally not in this
offline gate because it queries GitHub and the canonical remote. Repository and
sandbox source invariants that do not need the network remain enumerated.

## Anti-pattern

Do not add an LLM judge for a claim code can settle exactly.
