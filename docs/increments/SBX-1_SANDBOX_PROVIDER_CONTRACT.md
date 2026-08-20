# SBX-1 — SandboxProvider contract and deterministic fake

**Status:** implementation candidate; provider-free deterministic proof
**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`
**Planning ref:** `origin/planning/future-sssf` at `54ef67c3849b24b1eaa6e10d2ed0e49a09464a70`
**SBX-0 input:** `/home/shane/kun-agent-workspace/data/sssf-sbx-0/report.md`

## Intent and non-goals

Define the smallest provider-neutral `SandboxProvider` contract authorized by
Browser Sol control issue 6 and the continuing SSSF commission. The increment
proves the semantics with a deterministic in-process fake and watched-red
controls; it does not implement Docker or call any live provider.

Explicit non-goals are Docker mechanism binding (SBX-2), exe.dev parity,
Wayfinder/DSH, model execution, network/credential transport, live source
brokerage, or irreversible environment mutation.

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

The validator positively manufactures complete success; ambiguous create and
same-key duplicate prevention; stale/wrong identity; timeout, cancellation,
overflow, provider-client cleanup CNO, workload leak; missing/tampered/
overflowed artifacts; wrong Git ancestry; partial stop; unauthorized destroy;
destroy acknowledgement with residual resources; unreachable inspection;
already-absent idempotency; duplicate reconciliation; interruption at every
provider lifecycle boundary plus SSSF-owned secret-retirement CNO; and
PASS/FAIL/CNO precedence including cleanup CNO. It reports
`provider-calls: 0` and checks typed state, identities, bounds, digests,
quiescence, and residual lists rather than matching failure text.

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
- A real provider must prove its own process/environment custody and
  authoritative residual reconciliation against this contract before any
  Docker acceptance claim.
