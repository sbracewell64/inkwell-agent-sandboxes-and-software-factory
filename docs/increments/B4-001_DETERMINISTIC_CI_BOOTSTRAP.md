# B4-001 — Non-Vacuous Deterministic CI Bootstrap

**Status:** CANDIDATE — EXACT PULL-REQUEST-HEAD PROOF REQUIRED
**Starts from:** `04e5484a6190f033d25e1626b96a4cca93b7f755`

## Problem

Ordinary canonical pull-request heads currently return an empty GitHub check
set. No checks is could-not-observe, not green. The repository therefore lacks
a deterministic platform projection for its existing offline evidence.

## Desired outcome

Add the smallest repository-owned GitHub workflow that:

- runs on every pull request to `main` and every push to `main`, without path
  filters;
- runs current portable contracts on Linux and Windows;
- calls no model/provider, credential, or sandbox;
- performs no external lifecycle or acceptance operation;
- cannot pass after empty discovery or partial execution;
- retains observed-good, observed-bad, and could-not-observe in project JSON;
- projects GitHub success only for nonempty, wholly observed-good execution.

## Enumerated existing checks

`ci/checks.json` is the deterministic discovery boundary. It enumerates:

1. the CI contract validator and calibrated watched-red controls;
2. the B1 agent-bootstrap validator;
3. the B3-002 strict line-ending validator;
4. the B3-004 SQLite-free observability validator;
5. the B2-002 sandbox-source static validator;
6. the canonical `just inkwell test` application suite.

The B2-001 repository-ownership validator is excluded because it calls the
canonical remote and GitHub CLI. It is not provider-free/offline. No ADW,
model, sandbox, host lifecycle, B3 acceptance, DSH, migration, or expansion
path is invoked.

The B2-002 validator treats the optional trailing `.git` in an HTTPS remote
URL as syntax, not repository identity. This preserves its exact canonical
owner/repository check while allowing the equivalent `origin` URL installed
by `actions/checkout`.

The validators use repository files and disposable local fixtures. The Inkwell
suite uses a temporary SQLite database and loopback server and removes its
files after completion.

## Three-valued gate

`tools/ci_gate.py` writes deterministic JSON with each result classified as:

- `observed-good` when the command executed and succeeded;
- `observed-bad` when the command executed and failed;
- `could-not-observe` when the manifest/tool/result was unavailable or the
  command was cancelled or timed out.

Zero checks, partial execution, and every status other than all
`observed-good` return nonzero. The workflow log contains the full evidence,
so a GitHub success can only follow nonempty deterministic execution.

## Workflow controls

`.github/workflows/ci.yml` has one two-OS matrix job. Every matrix expansion
runs the same six enumerated checks. The contract validator requires:

- exact `pull_request` and `push` triggers targeting `main`;
- no path filter and no `pull_request_target`;
- `contents: read` as the only permission;
- concurrency cancellation;
- a ten-minute job timeout plus per-check timeouts;
- exact Ubuntu and Windows matrix entries;
- checkout without persisted credentials;
- exact Python, Bun, and just versions;
- Bun cache disabled;
- every action pinned to a 40-character commit SHA.

The immutable action objects were observed through the GitHub API at:

- `actions/checkout` v4.2.2 — `11bd71901bbe5b1630ceea73d27597364c9af683`;
- `actions/setup-python` v5.6.0 — `a26af69be951a213d495a4c3e4e4022e16d87065`;
- `oven-sh/setup-bun` v2.0.2 — `735343b667d3e6f658f44d0eca948eb6282f2b76`;
- `extractions/setup-just` v2 — `dd310ad5a97d8e7b41793f8ef055398d51ad4de6`.

No declared fleet verifier exists for action-tag resolution. The API returned
commit objects (observed-good as a direct three-valued observation), and the
workflow pins the returned objects rather than the movable tags.

## Calibrated watched-red controls

`docs/validation/check_ci_contract.py` first validates the live workflow and
manifest, then deliberately proves that the same gate goes red for:

1. zero check discovery;
2. a deliberately failing validator;
3. a missing executable;
4. timeout;
5. cancellation;
6. an empty OS matrix;
7. trigger drift to `pull_request_target`;
8. workflow path drift.

The controls assert observed-bad only for an executed failing validator.
Discovery, dependency, cancellation, and timeout failures remain
could-not-observe. Expected red controls are watched by the validator; they do
not weaken the real gate or create permanently failing GitHub jobs.

## Bootstrap proof rule

Local controls cannot prove that GitHub recognized or ran a newly introduced
workflow. B4-001 remains a candidate until the real workflow completes on its
own exact pull-request head and both jobs report nonempty execution.

If GitHub requires workflow presence on the default branch before it can run,
the exact-head result remains CNO. That bootstrap constraint requires a
bounded Browser Sol/authority decision through canonical landing; it must not
be relabeled green or bypassed with a lower-level merge.

## Non-goals

- Modify PR 1 or canonical `/mnt/e/SSSF`.
- Modify proof clones, credentials, B3 acceptance, DSH, migration, expansion,
  sandboxes, model rosters, or lifecycle behavior.
- Add unrelated hardening or provider-backed review.
- Weaken any existing acceptance gate.

## Acceptance

1. The workflow path and ordinary PR/default-branch triggers pass the contract
   validator.
2. Both Linux and Windows jobs execute at least one enumerated check.
3. All six provider-free checks execute without credentials, providers,
   sandboxes, spend, or external state mutation.
4. Empty or partial execution cannot project success.
5. Project evidence retains all three observation values.
6. Actions and tool versions are immutable/exact, caches and credentials are
   minimized, permissions are read-only, and time/concurrency are bounded.
7. Every watched-red control is observed red with the calibrated status.
8. The exact pull-request head completes the real workflow before B4-001 is
   called PASS.
