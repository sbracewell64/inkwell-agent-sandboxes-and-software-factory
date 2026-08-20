# Post-Baseline Roadmap

The order below deliberately separates concerns.

## Current SBX lifecycle status

- SBX-0's sole durable provider-neutral handoff landed at `aa0dcc5e`; it does
  not establish SBX-0 exit or any promotion.
- SBX-1 is a **landed implementation** of the provider-neutral contract and
  deterministic fake controls. SBX-1 is not activated, not accepted, not
  certified, and not real-provider-proven; it does not unlock SBX-2.
- SBX-2 is held. Docker mechanism selection, real-provider custody, and
  Windows/WSL feasibility require their own authorization and evidence; none
  is inferred from SBX-1's provider-free CI.

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

## Rule

Do not begin the local-sandbox replacement by editing exe.dev commands everywhere. First make source ownership explicit, then define the provider contract, then swap the implementation.
