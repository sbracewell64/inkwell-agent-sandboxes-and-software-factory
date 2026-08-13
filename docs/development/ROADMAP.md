# Post-Baseline Roadmap

The order below deliberately separates concerns.

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

## B5 — Sandbox provider contract

Goal:

Extract the semantic contract currently supplied by exe.dev before replacing it.

Define provider-neutral operations:

- create
- fill/source
- execute
- readiness
- port exposure
- artifact/Git extraction
- state inspection
- destroy

Acceptance:

contract tests run against the exe.dev reference adapter.

## B6 — Free/local sandbox implementation

Implement the selected local/free provider only after B5.

Acceptance must preserve:

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
