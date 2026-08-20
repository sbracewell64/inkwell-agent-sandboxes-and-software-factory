# ADR-0006 — SSSF-owned provider-neutral sandbox contract

**Status:** Accepted for SBX-1 contract/fake scope
**Date:** 2026-08-16

## Context

The historical exe.dev lifecycle is useful semantic evidence but is not a
portable provider contract. It uses shell prose, provider-specific custody,
unbounded/suppressed artifact paths, and control-plane errors that can look like
absence. Docker mechanics are deferred to SBX-2 and must not be guessed in the
contract increment.

SSSF also already owns a bounded subprocess supervisor and the sole offline
evidence-manifest serializer/validator. A new provider must not create a second
process owner, evidence store, trace store, lifecycle recovery engine, or
acceptance authority.

## Decision

Adopt `sandbox-provider/v1` as the minimum provider-neutral seam, implemented by
`adws/adw_modules/sandbox_provider.py` and documented once in
`docs/reference/SANDBOX_PROVIDER.md`.

1. `SandboxSpec` is immutable and binds run/operation identity, exact
   repository+commit+tree source identity, profile/template/toolchain and
   cognition/instruction identities, finite resource bounds, effect/network/
   filesystem/exposure policies, secret references only, workspace mode, and
   evidence root.
2. `CommandSpec` is argv-based, absolute-cwd, allowlisted-environment,
   explicit-stdin, monotonic-timeout and bounded-stream authority. Its
   projection is consumed by the existing SSSF subprocess owner. It is not an
   `AgentBackend` contract.
3. Provider operations are explicit, operation-keyed, bounded fact operations
   for create, inspect, typed exec, source/input copy, artifact collection, Git
   export, process/quiescence inspection, stop, one-use-authorized destroy,
   and reconciliation. Facts are observed-good, observed-bad, or
   could-not-observe and never contain acceptance/promotion authority.
4. SSSF owns durable lifecycle operation records, applicability, sequencing,
   budgets, retries/recovery, aggregate fold, acceptance/promotion, and
   destroy authorization. CNO records retain `unknown`; they never become
   `absent`.
5. Artifact/Git obligations are declared before export, are bounded and
   identity/digest/ancestry checked, use the existing evidence-manifest owner,
   and precede irreversible destruction. Reconciliation distinguishes present,
   absent, duplicate, residual, and could-not-observe.
6. The aggregate fold is FAIL over observed contradictions, otherwise CNO over
   required incomplete/wrong-identity/unverified observations, and PASS only
   for complete applicable required good observations. Work, cleanup, and
   evidence components remain separate.
7. Docker-specific capability decisions use a typed deferred/refused fact until
   SBX-2 binds a truthful mechanism.

The in-process `FakeSandboxProvider` and watched-red validator prove this
semantic contract without an external provider call. They are not a production
provider and do not establish Docker qualification.

## Consequences

- SBX-2 can map Docker mechanisms to an existing semantic seam rather than
  making Docker the workflow owner.
- Ambiguous creation, inspection failure, process/workload leaks, bounded
  export failures, and residual cleanup remain recoverable CNO/non-clean facts.
- The current B4-002 governance/exact-head acceptance limitation remains
  explicit. SBX-1 reuses executable subprocess semantics but does not call that
  candidate final-head evidence accepted.
- A changed mechanism may require a new typed capability/refusal or an
  explicit successor contract; it cannot silently weaken the public facts.
