# Post-Baseline Roadmap

The order below deliberately separates concerns.

authoritative planning source: planning/future-sssf; commit: 5f83760a6d71bb798b9f652f21267fad4b743f16; tree: 6e33db5ae5f7d43bf3a7f8c351d888c599d1997d; generation: planning/future-sssf@5f83760a6d71bb798b9f652f21267fad4b743f16:6e33db5ae5f7d43bf3a7f8c351d888c599d1997d

## Authoritative Docker-first commissioning order

```text
Docker SBX-2..8
-> Docker-backed ordinary PR
-> immutable post-Docker/pre-DSH baseline
-> existing Wayfinder
-> DSH-0A
-> DSH-0B
-> DSH-1...
```

## Current SBX lifecycle status

- SBX-0's sole durable provider-neutral handoff landed at `aa0dcc5e`; it does
  not establish SBX-0 exit or any promotion.
- SBX-1 is a **landed implementation** of the provider-neutral contract and
  deterministic fake controls. SBX-1 is not activated. SBX-1 is not accepted.
  SBX-1 is not certified. SBX-1 is not real-provider-proven. SBX-1 does not
  unlock SBX-2.
- SBX-2 is held. Docker mechanism selection, real-provider custody, and
  Windows/WSL feasibility require their own authorization and evidence; none
  is inferred from SBX-1's provider-free CI.

Planning-state semantics and legal edges are owned only by
[`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). The durable current-state and
transition evidence record is [`PLANNING_STATE.json`](PLANNING_STATE.json).
A roadmap row records dependency position; it does not create a task, grant
runtime authority, or replace the lifecycle contract.

## B1 — Baseline archive + documentation discovery

Goal:

Complete the B0 freeze and make `docs/README.md` a first-class agent entrypoint.

Acceptance:

- B0 harvested/teardown complete,
- immutable tag exists,
- fresh agents are pointed to the docs index,
- no execution behavior changes merely to add documentation discovery.

## B2 — Canonical repository ownership

Goal:

Ensure new sandboxes execute the SSSF source you are actually evolving.

Scope:

- create/use a remote repository you control,
- preserve upstream as a reference remote,
- make the FILL clone URL configurable instead of hard-coded,
- pin proof runs to exact commits.

Acceptance:

fresh sandbox clones the owned source and gate proves guest HEAD equals the requested commit.

## B3 — Windows host portability

Goal:

Turn the ad-hoc Windows compatibility overlay into supported, tested behavior.

Scope:

- CRLF normalization,
- portable temp-file creation,
- SSH first-host behavior,
- persistent PATH/bootstrap,
- host observability without external `sqlite3` if feasible.

Acceptance:

fresh Windows clone -> doctor -> mount -> teardown without manual source editing.

## B4 — Durable local/free agent roster

Goal:

Add an explicit locally maintained roster without changing upstream/default staffing.

Acceptance:

- planner qualification,
- builder qualification,
- typed-output retry,
- permission enforcement,
- deterministic test+commit fixture,
- documented last-verified date/model IDs.

## B5 / SBX-1 — Sandbox provider contract

The provider-neutral contract and deterministic fake implementation have landed.
That landed scope defines create/source, typed execution, readiness facts,
bounded artifact/Git extraction, state inspection, stop, authorized destroy,
reconciliation, and three-valued folding. Historical exe.dev parity is not an
acceptance prerequisite and was not observed by this increment.

This status is implementation-only. Activation, acceptance, certification,
real-provider proof, supported Windows-host proof, and SBX-2 promotion remain
CNO or unmet.

## B6 / SBX-2+ — Free/local sandbox implementation (held)

**Planning state: `HELD`.**

A selected local/free provider may be implemented only after a separately
bounded SBX-2 mechanism/feasibility increment is authorized. SBX-1 is not that
authorization or unlock.

Eventual acceptance must preserve:

- host isolation,
- disposable/reproducible state,
- guest toolchain,
- no host provisioning credential in guest,
- application + observability access,
- Git harvest,
- explicit destruction,
- crash recovery.

## B7 — Observability and unattended execution

Goal:

make trace/status inspection reliable from the Windows host and suitable for supervisory automation.

## B8 — Broader ADW/agent qualification

Qualify scout/reviewer/documenter and additional ADWs with explicit fixtures.

## FUT-003 — FirstMate planning-transition awareness

**Planning state: `ACTIVE`, not `PROVEN`.**

The architectural decision is
[`ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`](../decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md),
and the durable state/evidence record is
[`PLANNING_STATE.json`](PLANNING_STATE.json). The legal lifecycle contract is
owned by [`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md).

The authoritative planning source marks `FP-001` and `FM-FP-001` as
active-not-proven bounded increments. This is engineering authorization and
intake eligibility only; it is not task creation, execution, landing,
acceptance, certification, live enablement, or `PROVEN`. The durable state
record is bound to the authoritative planning generation above, not to an
older snapshot.

FUT-003 remains planning-only in this increment. No FirstMate watcher,
producer, or consumer implementation is added. No feed, task, runtime
behavior, credential, sandbox, provider, ADW, Docker, Wayfinder, or DSH
behavior is added. A later ACTIVE
record would be intake eligibility only and would still require ordinary
admission, exact source validation, review, acceptance, and current
PRE_CERTIFICATION constraints. It would never be task creation, execution
authority, landing authority, a PRE_CERTIFICATION exit, acceptance,
certification, live enablement, or `PROVEN`.

## Long-range sequenced direction — FUT-001

**Planning state: `SEQUENCED`, not `ACTIVE`.**

The governing decision is
[`ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`](../decisions/ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md).
SSSF retains outer graph, source custody, budgets, external-effect policy,
deterministic verification, acceptance, promotion, landing, and terminal-state
authority. DSH may be considered only as a future bounded inner execution cell
with attributable evidence, forceable termination, and no outer authority.

Production DSH adoption remains downstream of the existing execution/isolation,
backend, source-custody, lifecycle/evidence, hard-termination, quiescence, and
acceptance proofs. No DSH or Cordis implementation is authorized by this
roadmap row.

## Rule

Do not begin the local-sandbox replacement by editing exe.dev commands everywhere. First make source ownership explicit, then define the provider contract, then swap the implementation.
