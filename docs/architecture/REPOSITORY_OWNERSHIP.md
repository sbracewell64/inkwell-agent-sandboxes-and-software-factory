# Repository Ownership and Sandbox Source Custody

This is the current, authoritative record of who owns the SSSF source and where a sandbox run gets the code it executes.

It is normative and it describes present behavior. Executable code outranks it: the recipes and the run-record schema below are the authority, and this document exists to state what they do without a reader having to reconstruct it. `docs/validation/check_source_custody_authority.py` refuses to let the two drift apart.

## Authority pointers

- `just/sandbox/lifecycle/fill.just` — FILL, the only clone authority.
- `just/sandbox/lifecycle/setup.just` — SETUP Gate A, the independent provenance recheck.
- `just/sandbox/manage/harvest.just` — the harvest namespace that brings a run's commits home.
- `sandbox_mount/host/run_record.py` — the durable run-record schema that carries provenance across phases and past teardown.
- `docs/increments/B2-002_SANDBOX_SOURCE_CONTRACT.md` — the increment that established and proved this contract.
- `docs/evidence/B2-002_SOURCE_PROOF_RUN_RECORD.json` — the tracked run record from that live proof.
- `docs/evidence/B2-002_SOURCE_PROOF.md` — the proof narrative.
- `docs/validation/check_source_custody_authority.py` — the deterministic control that keeps this document true.

## Sandbox source custody

FILL resolves the sandbox source from the host checkout itself. It reads `git remote get-url origin`, so the repository a sandbox clones is whatever the canonical `origin` remote of the host checkout is, and the recipe names no repository of its own.

Three properties follow, and each is enforced rather than assumed:

- **Public clone only.** FILL is credential-free. It refuses any origin that is not a public `https://github.com/` URL, so an SSH or credential-bearing host remote is never forwarded into a disposable VM.
- **Exact pin.** Every run executes an exact 40-character committed revision. An explicit committed SHA is accepted; with no argument the source revision is the host checkout's current `HEAD`.
- **Clean host tree.** Uncommitted host files cannot cross a public Git clone, so the default path refuses to run while the host working tree is dirty rather than silently mounting an older committed tree than the engineer is looking at.

Inside the VM the clone is checked out at that revision and the run branch `sbx/<run-id>` is created at it. FILL then gates the actual guest `HEAD` against the intended revision and fails the phase, leaving the VM up, if they differ. Only after that gate does it write provenance to the run record: `source_repo`, `source_sha`, and the actual guest `commit_sha`.

SETUP does not trust that record. Gate A independently re-reads the guest's own `origin`, its `HEAD`, and its working-tree state, and fails unless they match the recorded provenance exactly and the tree is clean.

HARVEST reads the same run branch and writes it home under `refs/sandbox/<run-id>`, which is why exactly one run's commits come back and nothing else does.

## Contract table

Every row below is a claim this document makes about the code, the file that owns it, and the operative token a reader will find by opening that file. `docs/validation/check_source_custody_authority.py` rejects duplicate rows and verifies recipe rows with bounded structural recognizers after removing comments and unreachable literal-false blocks. A row outside that accepted syntax is reported unchecked by name and prevents a satisfied verdict.

| Contract element | Code authority | Exact token |
| --- | --- | --- |
| origin-derivation | `just/sandbox/lifecycle/fill.just` | `git remote get-url origin` |
| public-clone-restriction | `just/sandbox/lifecycle/fill.just` | `https://github.com/*)` |
| exact-pin-shape | `just/sandbox/lifecycle/fill.just` | `^[0-9a-f]{40}$` |
| default-pin-is-host-head | `just/sandbox/lifecycle/fill.just` | `PIN="$(git rev-parse HEAD)"` |
| dirty-host-refusal | `just/sandbox/lifecycle/fill.just` | `if [ -n "$(git status --porcelain)" ]; then` |
| guest-run-branch | `just/sandbox/lifecycle/fill.just` | `branch="sbx/$run_id"` |
| fill-head-gate | `just/sandbox/lifecycle/fill.just` | `if [ "$HEAD_SHA" != "$INTENDED" ]; then` |
| persisted-source-repo | `just/sandbox/lifecycle/fill.just` | `source_repo="$REPO"` |
| schema-source-repo | `sandbox_mount/host/run_record.py` | `"source_repo",` |
| persisted-source-sha | `just/sandbox/lifecycle/fill.just` | `source_sha="$PIN"` |
| schema-source-sha | `sandbox_mount/host/run_record.py` | `"source_sha",` |
| persisted-commit-sha | `just/sandbox/lifecycle/fill.just` | `commit_sha="$HEAD_SHA"` |
| schema-commit-sha | `sandbox_mount/host/run_record.py` | `"commit_sha",` |
| setup-origin-recheck | `just/sandbox/lifecycle/setup.just` | `[ "$origin" = "$want_repo" ]` |
| setup-head-recheck | `just/sandbox/lifecycle/setup.just` | `case "$head" in` |
| setup-clean-tree-recheck | `just/sandbox/lifecycle/setup.just` | `if [ -n "$porcelain" ]; then` |
| harvest-run-branch | `just/sandbox/manage/harvest.just` | `BRANCH="sbx/$RUN_ID"` |
| harvest-ref-namespace | `just/sandbox/manage/harvest.just` | `DEST="refs/sandbox/$RUN_ID"` |
| canonical-remote-url | `docs/validation/check_repository_ownership.py` | `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git` |
| upstream-remote-url | `docs/validation/check_repository_ownership.py` | `https://github.com/disler/inkwell-agent-sandboxes-and-software-factory.git` |
| origin-is-canonical | `docs/validation/check_repository_ownership.py` | `run("git", "remote", "get-url", "origin") != CANONICAL` |
| upstream-push-disabled | `docs/validation/check_repository_ownership.py` | `"--push", "upstream"` |

## Proven ownership state — B2-001

Canonical evolving repository:

`https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`

Remote roles:

- `origin` — operator-owned canonical repository; writable.
- `upstream` — Disler's repository; reference-only.
- `main` — latest accepted/proven platform line.
- `increment/*` — bounded development increments.
- `sssf-*` — immutable proven milestones and evidence.

Accepted increments are proved on increment branches, then canonical `main` is fast-forwarded to the exact accepted commit.

## What a fresh sandbox proves — B2-002

B2-002 closed the gap this document previously described as outstanding. A fresh sandbox now:

- clones the canonical repository the host checkout's `origin` names,
- checks out an exact committed revision,
- proves guest `HEAD` equals the requested revision before any provenance is recorded,
- persists `source_repo`, `source_sha`, and `commit_sha` in the durable run record,
- re-proves repository identity, revision, and a clean tree during SETUP,
- harvests its own commits back under a run-scoped ref without ambiguity,
- retains that provenance after teardown.

The live proof ran on `b2-002-source-proof-20260813-f9681a` against host commit `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`, with FILL invoked without an explicit SHA. The closed record is tracked at `docs/evidence/B2-002_SOURCE_PROOF_RUN_RECORD.json`.

## Why this matters

Without explicit source custody, the host can say "current SSSF" while the sandbox executes a different revision, and reproducibility is gone.

The repository and the exact commit are therefore explicit, recorded, and gated inputs to every sandbox run — not defaults a reader has to infer, and not something any lifecycle phase may re-derive on its own. Nothing outside FILL selects the sandbox source, and no environment variable duplicates it.

## Keeping this document true

`docs/validation/check_source_custody_authority.py` reads this document and the code together, offline. It fails when this document attributes a clone to a named repository instead of the `origin` derivation, when a pointer above is dropped, when a cited path cannot be opened, or when a canonical URL or a persisted field name here diverges from the bytes the code actually uses. It reports structural coverage on every path and refuses satisfaction when any recipe row is unchecked.
