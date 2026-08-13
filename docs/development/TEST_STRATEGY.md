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

## Anti-pattern

Do not add an LLM judge for a claim code can settle exactly.
