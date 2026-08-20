# SBX-1 — SandboxProvider contract and deterministic fake

**Status:** LANDED IMPLEMENTATION; provider-free deterministic controls observed-good; lifecycle promotions CNO/unmet
**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`
**Historical PR head:** `d38b9b4c4718389104ad5ffbd1ad05e70cb82db9`, tree `fd2a37619f9c9b258a676a643d691182cb444851`
**Landed as:** `b902cdcecd65c8ba03031875297d31e990f12c11`, the same tree as the historical PR head
**Reconciliation base:** `aa0dcc5e66a41284cdb2f28ca4c235bec7c623d6`
**Planning ref:** `origin/planning/future-sssf` at `54ef67c3849b24b1eaa6e10d2ed0e49a09464a70`
**SBX-0 handoff:** [`../reference/SBX-0_SEMANTICS_INVENTORY.json`](../reference/SBX-0_SEMANTICS_INVENTORY.json), source content SHA `2d16bee3db4c46062b460dfbd6752339e85228a3b6f2c5002313a4f06dc663b3`
**Mutable source input:** `data/sssf-sbx-0/report.md` (evidence only; not durable authority)

## Intent and non-goals

Define the smallest provider-neutral `SandboxProvider` contract handed off by
Browser Sol control issue 6 and the continuing SSSF commission. The increment
proves the semantics with a deterministic in-process fake and watched-red
controls; it does not implement Docker or call any live provider. The SBX-0
publication is an inspectable handoff input only and does not activate or accept
this increment.

Explicit non-goals are Docker mechanism binding (SBX-2), exe.dev parity,
Wayfinder/DSH, model execution, network/credential transport, live source
brokerage, or irreversible environment mutation.

## Landed lineage and evidence disposition

PR #18 and landed main `b902cdce` are immutable historical/adverse provenance;
this forward reconciliation does not rewrite their landing history. The PR head
and squash commit have the same tree, so the implementation bytes are positively
bound as landed. The scope of every other observation remains local to its
evidence:

| Axis | Observation | Durable disposition |
|---|---|---|
| Provider-neutral implementation bytes landed | observed-good | PR #18 head `d38b9b4c` and `b902cdce` both name tree `fd2a3761` |
| Deterministic fake-contract controls | observed-good | Provider-free validator and focused tests establish the typed contract properties listed below with `provider-calls: 0` |
| Exact-head Linux/Windows CI | observed-good | Establishes execution of the provider-free tree only; it is not supported Windows-host or provider custody proof |
| Assignment-distinct semantic review applicable to the PR #18 landing | could-not-observe | No readable, head-bound durable evidence was found; no review is inferred from the implementation review-fix chain |
| Applicable RulingEnvelope for the PR #18 landing | could-not-observe | `SOL-FM-SSSF-SBX1-POSTMERGE-20260820-1203` governs this reopened forward reconciliation only and cannot approve the historical landing |
| One-use LandingAuthorization for the PR #18 landing | could-not-observe | Unmet; the runtime destroy capability is unrelated and is not landing authority |
| Post-merge exact-main proof for the PR #18 landing | could-not-observe | No such historical proof was observed; later tree comparison does not backfill fresh-at-use proof |
| Supported Windows-host/provider execution | could-not-observe | Green Windows CI ran the provider-free fake, not Docker/provider custody |
| Real provider or Docker custody | could-not-observe | No provider call or environment mutation occurred |
| Activation, acceptance, certification, or SBX-2 unlock | could-not-observe | Unmet; no promotion is inferred from landed bytes or fake controls |

SBX-1 is a **landed implementation**. SBX-1 is not activated, not accepted,
not certified, and not real-provider-proven; it does not unlock SBX-2.

## Code and ownership

- `adws/adw_modules/sandbox_provider.py` owns the public typed contract, closed
  facts, immutable spec/command identities, SSSF lifecycle record interface,
  destroy authorization gate, aggregate fold, typed deferred capability, and
  deterministic fake.
- `adws/adw_modules/subprocess_supervisor.py` remains the process owner. The
  contract exposes `CommandSpec.supervisor_projection`; no second supervisor
  was added.
- `tools/evidence_manifest.py` remains the sole evidence-manifest
  serializer/validator. Artifact facts carry bounded inventories and a manifest
  reference rather than defining a duplicate manifest format.
- Existing SSSF trace/observability owners remain authoritative for durable
  runtime persistence. The in-memory lifecycle store exists only as a test
  double for the append/CAS interface.
- `docs/validation/check_sandbox_provider.py` and
  `tests/test_sandbox_provider.py` exercise the fake without external calls.

## Proven semantic rules

`SandboxSpec` binds exact repository, commit, and tree identities plus immutable
profile/template/toolchain/workspace/policy/resource/secret-reference/evidence
identities. `CommandSpec` binds argv, normalized absolute guest cwd,
allowlisted environment references, explicit stdin, monotonic timeout, bounded
streams, expected exits or parser identity, and execution/attempt/cancellation
identities.

Every provider operation is keyed by `OperationKey` and returns an explicit
observed-good, observed-bad, or could-not-observe fact. Provider facts do not
return acceptance, recovery, retry, push, promotion, or a second state store.
Host/provider-client custody and sandbox workload/resource quiescence are
separate fact domains.

SSSF lifecycle records preserve requested/provider/source/attempt/evidence
identities, prior/observed state, timestamps, reason, and destroy authority.
CNO uses `LifecycleState.UNKNOWN`; it cannot become absence. Artifact and Git
obligations are applicability-bound, bounded, digest/identity checked, and
export-before-destroy. Git export exposes `PromotionAuthority.NONE` only.

`fold_aggregate` is nonempty and deterministic: observed bad first, then
required CNO/incomplete/wrong-identity/unverified cleanup, then PASS only when
all applicable required observations are good. Work, cleanup, and evidence
summaries remain separately inspectable under aggregate CNO.

## Deterministic proof

Run:

```text
python3 docs/validation/check_sandbox_provider.py
PYTHONPATH=.:adws pytest -q tests/test_sandbox_provider.py
```

The observed-good positive case is limited to immutable repo+commit+tree
`SandboxSpec` identity; typed `CommandSpec` projection to the existing
supervisor; operation-keyed three-valued facts; separate host-client, workload,
and resource quiescence; bounded manifest-backed artifact and Git export with
`PromotionAuthority.NONE`; authenticated one-use destroy/reconciliation fake
controls; and FAIL-over-CNO-over-PASS aggregate precedence. It reports
`provider-calls: 0`.

The validator also positively manufactures ambiguous create and same-key
duplicate prevention; stale/wrong identity; timeout, cancellation, overflow,
provider-client cleanup CNO, workload leak; missing/tampered/overflowed
artifacts; wrong Git ancestry; partial stop; unauthorized destroy; destroy
acknowledgement with residual resources; unreachable inspection;
already-absent idempotency; duplicate reconciliation; interruption at every
provider lifecycle boundary plus SSSF-owned secret-retirement CNO; and
PASS/FAIL/CNO precedence including cleanup CNO. It checks typed state,
identities, bounds, digests, quiescence, and residual lists rather than matching
failure text.

The contract validator is added to the repository's non-vacuous offline CI
manifest. Live Docker/exe.dev/provider/model/network/credential/browser calls
are not part of the proof.

## Known limitations and handoff

- Docker client/API/container/image/workspace/secret/network mechanics remain
  an explicit `deferred-to-sbx-2` capability, not an invented implementation.
- Runtime integration of exported facts with HD-08 acceptance remains a later
  increment; the contract points at the existing manifest owner.
- The baseline's B4-002 exact-head governance acceptance is still CNO. This
  increment cites and projects onto its executable subprocess semantics without
  representing that governance CNO as accepted final-head evidence.
- Historical PR #18 assignment-distinct review, applicable RulingEnvelope,
  LandingAuthorization, and post-merge exact-main proof remain CNO/unmet; this
  reconciliation supplies none of them retroactively.
- A real provider must prove its own process/environment custody and
  authoritative residual reconciliation against this contract before any
  Docker acceptance claim.
