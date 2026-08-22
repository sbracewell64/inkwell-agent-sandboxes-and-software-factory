# B2-002 — Sandbox Source Contract

**Status:** PROVEN
**Starts from:** `sssf-b2-001-canonical-repository`

## Problem

The host had an operator-owned canonical repository after B2-001, but sandbox FILL still hard-coded Disler's upstream repository.

That allowed the host SSSF to evolve while a newly created sandbox could silently execute different source.

## Desired outcome

Every sandbox run records and proves both:

- the repository it cloned;
- the exact commit it executed.

The default source is the host checkout's canonical `origin` and exact committed `HEAD`.

## Source contract

- `source_repo` — public repository URL resolved from the host checkout's `origin`.
- `source_sha` — exact 40-character committed source revision selected by the host.
- `commit_sha` — actual guest HEAD after clone, checkout, and FILL gate.
- Default FILL requires a clean host working tree.
- Default FILL selects exact host `HEAD`.
- Explicit committed SHA selection remains supported.
- FILL accepts only public `https://github.com/...` source repositories.
- Accepted FILL requires actual guest HEAD to equal `source_sha`.
- SETUP independently verifies guest `origin`, guest HEAD, recorded provenance, and clean working-tree state.

## Durable state

The closed sandbox run-record schema now includes:

- `source_repo`
- `source_sha`
- `commit_sha`

This keeps source provenance available across the separate sandbox lifecycle processes and after teardown.

## Non-goals

- Replace exe.dev.
- Add another sandbox provider.
- Change ADW behavior.
- Change model rosters.
- Add a general sandbox-provider abstraction.
- Change canonical repository ownership established by B2-001.

## Implementation

B2-002 changed:

- `sandbox_mount/host/run_record.py`
- `just/sandbox/lifecycle/fill.just`
- `just/sandbox/lifecycle/setup.just`
- sandbox-orchestrator references and durable lifecycle documentation
- deterministic source-contract validation

FILL no longer contains Disler's repository as clone authority.

SETUP Gate A now verifies source repository identity in addition to commit and working-tree integrity.

## Static acceptance evidence

`python docs/validation/check_sandbox_source_contract.py`

Result:

`B2-002 sandbox source contract: PASS`

Repository ownership validator:

`B2-001 repository ownership: PASS`

Agent bootstrap validator:

`B1 agent bootstrap: PASS`

`python -m py_compile sandbox_mount/host/run_record.py`

Result: PASS.

`git diff --check`

Candidate implementation gate before live proof: PASS with no whitespace errors.

During final documentation closure, `git diff --check` detected trailing whitespace on the `**Status:** PROVEN` line. The B2-002 closure was nevertheless committed and published. B2-003 records and corrects that documentation-hygiene deviation without moving or rewriting the immutable B2-002 tag.

## Live proof

Candidate runtime commit:

`0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`

Proof sandbox:

`b2-002-source-proof-20260813-f9681a`

FILL was invoked without an explicit SHA.

It automatically selected:

- `source_repo` = `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`
- `source_sha` = `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`

FILL gated actual guest HEAD against that exact SHA and passed.

The durable run record stored:

- `source_repo` = canonical operator-owned repository
- `source_sha` = `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`
- `commit_sha` = `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df`

Independent guest inspection verified the same origin and HEAD with a clean working tree.

SETUP Gate A independently verified:

- recorded repository == guest origin;
- recorded source SHA == guest HEAD;
- guest working tree clean.

Gate A passed.

## Cleanup proof

Teardown:

`just sbx lifecycle teardown b2-002-source-proof-20260813-f9681a --no-harvest`

Result:

- spend recorded;
- runtime key revoked;
- VM destroyed;
- key file shredded;
- record closed;
- key-absence gate passed.

After teardown:

`ssh exe.dev ls`

reported no VMs.

Closed run record:

`docs/evidence/B2-002_SOURCE_PROOF_RUN_RECORD.json`

Detailed proof narrative:

`docs/evidence/B2-002_SOURCE_PROOF.md`

## Known unrelated observation

The existing stock-roster SETUP gate still reports C/D/E PASS after individual model probes print insufficient-credit failures.

That defect predates B2-002 and remains explicitly unresolved. It does not affect the independently proven source-provenance assertions.

## Result

B2-002 is proven.

A fresh sandbox now derives its default source from the canonical host repository and exact committed host HEAD, persists that provenance, gates the guest checkout against it, independently re-verifies it during SETUP, and retains the provenance after teardown.

The host and sandbox can no longer silently disagree about which SSSF source revision a run executed.

## Boundedness delta

```text
boundedness_delta: none
boundedness_reason: this increment predates the boundedness registry. Its
  growth surfaces, where it created any, were inventoried and bound
  retrospectively by BOUND-1 against the post-increment source rather than
  claimed here after the fact. See
  docs/reference/BOUNDEDNESS_REGISTRY.json and
  docs/development/BOUNDEDNESS_LAW.md.
```
