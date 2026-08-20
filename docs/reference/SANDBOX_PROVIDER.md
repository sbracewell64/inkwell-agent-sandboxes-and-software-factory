# SBX-1 SandboxProvider contract

**Contract:** `sandbox-provider/v1`
**Implementation owner:** `adws/adw_modules/sandbox_provider.py`
**Increment:** `SBX-1` from canonical base `bee9296a4c94b1dc3da6991acd1755a91fa681eb`
**Landed implementation:** PR #18 head `d38b9b4c4718389104ad5ffbd1ad05e70cb82db9` landed as tree-identical `b902cdcecd65c8ba03031875297d31e990f12c11`
**Planning authority:** `origin/planning/future-sssf` at `54ef67c3849b24b1eaa6e10d2ed0e49a09464a70`
**SBX-0 handoff:** [`SBX-0_SEMANTICS_INVENTORY.json`](SBX-0_SEMANTICS_INVENTORY.json), source digest `2d16bee3db4c46062b460dfbd6752339e85228a3b6f2c5002313a4f06dc663b3`

This is the provider-neutral environment-mechanics seam. It is not a Docker
adapter and it does not claim a live provider capability. The deterministic
validator is `docs/validation/check_sandbox_provider.py`; its fake has zero
external provider calls. The SBX-0 inventory is a source-bound handoff only.
SBX-1 is a **landed implementation**. SBX-1 is not activated, not accepted,
not certified, and not real-provider-proven; it does not unlock SBX-2.

## Ownership boundary

`AgentBackend != SandboxProvider`.

- **SSSF code** owns lifecycle sequencing, applicability, operation/attempt
  budgets, retries, cancellation propagation, recovery choices, durable
  operation records, aggregate folding, acceptance/promotion, and issuing the
  one-use authorization for irreversible destruction.
- **SandboxProvider** owns bounded environment operations and returns observed
  facts. It never returns acceptance authority, makes a recovery decision,
  retries autonomously, promotes/pushes Git, or owns a second lifecycle/trace
  database.
- **AgentBackend** remains the bounded reasoning-execution contract. It is not
  a provider identity, provider resource, or sandbox lifecycle owner.
- The typed `CommandSpec.supervisor_projection` points at the existing
  SSSF-owned `adws/adw_modules/subprocess_supervisor.py`. Docker must not add a
  second subprocess supervisor. The B4-002 exact-head governance/acceptance
  status remains CNO in the baseline ledger; this increment reuses its
  executable process-custody semantics without manufacturing final-head
  acceptance evidence.

## Requested identity

`SandboxSpec` is frozen and content-addressed. It binds:

- `run_id` and the create `operation_id`;
- HTTPS source repository, full requested commit SHA, and full requested tree
  SHA (`SourceIdentity`);
- profile, immutable template, toolchain, workspace mode, and cognition /
  instruction policy identities;
- positive CPU, memory, PID, disk, wall-time, and bounded network resource
  ceilings (`ResourceBounds`);
- filesystem, network, effect, and exposure policy identities;
- secret **references** only; secret values cannot be represented in the spec;
- an absolute evidence root.

`SandboxIdentity` separates the requested spec digest from the provider's
resource identity. Resource lookup and replay bind the complete run, spec, and
provider-local resource identity, so a local identifier collision across runs
cannot satisfy or mutate either subject. A stale, wrong, or unavailable
provider identity is not silently changed into `ABSENT`.

## Typed command projection

`CommandSpec` is shell-free authority. It requires:

- nonempty `argv`, normalized absolute guest `cwd`, and execution/attempt /
  cancellation identities;
- environment references plus an explicit allowlist;
- closed/empty/referenced stdin policy;
- a positive **monotonic** timeout;
- independent bounded stdout/stderr retention;
- expected exit codes or a structured terminal-parser identity.

The provider may add transport facts, but host/provider-client process custody
comes from the existing supervisor. In-sandbox workload and resource quiescence
are separate provider observations. A clean terminal result requires the host
custody plus both in-sandbox domains.

## Operation surface and fact rules

`SandboxProvider` exposes only bounded, idempotency-keyed operations:

```text
create(spec, operation)
inspect(identity, operation)
exec(identity, command, operation)
copy_in(identity, explicit_source_or_input)
collect_artifacts(identity, artifact_spec)
export_git(identity, git_export_spec)
inspect_processes(identity, operation)
wait_quiescent(identity, operation)
stop(identity, operation)
destroy(identity, operation, one_use_authorization)
reconcile(identity, operation)
```

`OperationKey` carries run, operation, attempt, operation kind, and an explicit
idempotency key. Every result is a closed three-valued fact:

- `observed-good` — the bounded fact was positively observed;
- `observed-bad` — a contradiction or prohibited state was positively
  observed;
- `could-not-observe` — the fact was unavailable, interrupted, ambiguous,
  overflowed, or cleanup was not verifiable.

Facts retain reason, timestamp, prior/observed lifecycle state, resource
identity, and evidence references. Provider facts do not have an `accepted`
field. `CapabilityFact` provides an explicit `deferred-to-sbx-2` or `refused`
disposition where Docker mechanics would otherwise invite an untruthful guess.

## Lifecycle records and states

SSSF's durable vocabulary is `LifecycleState`: requested, creating, present,
source-staged, ready, running, stopping, stopped, exporting, quiescent,
destroying, absent, duplicate, residual, and unknown. `unknown` is the state
paired with CNO; it is not absence.

`LifecycleOperationRecord` preserves, for every append/CAS operation:

- requested sandbox, provider resource, source, run, operation, and attempt
  identities;
- prior and observed lifecycle state;
- requested/observed timestamps and closed observation reason;
- evidence references; and
- any SSSF-issued destroy authorization.

`LifecycleRecordStore` is an SSSF persistence interface. The in-memory store is
only a deterministic test double; production storage must bind the existing
SSSF state/observability owners rather than introduce a provider lifecycle DB or
trace store.

## Evidence, artifacts, and Git

Applicability is declared by SSSF before an operation. `ArtifactSpec` therefore
contains exact paths, required/applicable status, producer/purpose/manifest
identity, and positive file/count/byte bounds. `ArtifactExportFacts` returns a
path-sorted, duplicate-free inventory with byte lengths, SHA-256 digests,
producer/run/operation/attempt identities, completeness, overflow, missing and
tamper facts. `ArtifactSpec` binds the manifest path, artifact root, and
`tools/evidence_manifest.py` validation context; its observed result and
validated inventory are required before the export obligation can pass.

The provider does not create a second evidence serializer or validator. Runtime
SSSF integration must use the sole `tools/evidence_manifest.py` serializer and
validator. Missing/unreadable required artifacts are CNO; a positive digest
contradiction is observed-bad; overflow is CNO. An empty inventory is never a
pass for an applicable required obligation.

`GitExportSpec` binds the exact source base commit/tree and export identity.
`GitExportFacts` returns base, tip, tree, bundle size/digest, and positive
ancestry verification. The result carries `PromotionAuthority.NONE`; there is
no provider push or promotion operation. Base/tip/tree/ancestry mismatch is a
contradiction, not a successful harvest.

The SSSF-side `issue_destroy_authorization` function cannot mint a token until
all applicable required artifact/Git obligations are observed-good, complete,
identity-bound, and ancestry-verified (and secret retirement is observed when
secret references exist). Authorization validates the exact sandbox spec
digest, source-bound artifact and Git specifications, requested Git export
reference, source base commit/tree, evidence-manifest candidate Git tip, and an
identity-bound `SecretRetirementFacts` inventory covering
every requested secret reference. Therefore export and evidence obligations precede
irreversible destroy. A provider acknowledgement is not clean terminal state:
SSSF must reconcile authoritative absence afterward.

## Reconciliation and destruction

`ReconciliationFacts.status` distinguishes:

- `present` — the uniquely identified resource is observed;
- `absent` — empty authoritative result, observed-good only;
- `duplicate` — more than one resource claims the identity, observed-bad;
- `residual` — residue remains after cleanup, observed-bad; and
- `could-not-observe` — inspection/reconciliation was unavailable, CNO.

Inspection failure can never produce `absent`. Already-absent destroy and
reconciliation are idempotent only where authoritative observation binds the
exact run, sandbox/resource, and destroy operation identities and proves absence.
Destroy requires an opaque SSSF-issued `DestroyAuthorization`. The SSSF-only
`DestroyAuthorizationIssuer` owns signing material and records the authenticated
value in `DestroyAuthorizationStateStore`; signing material is never serialized.
The provider receives only `DestroyAuthorizationVerifier`, which can verify and
atomically compare-and-swap an issued capability through `reserved` and
`completed` states but cannot mint or record one. A reservation remains
identity-bound and retryable after authoritative reconciliation when failure
precedes the side effect; completion is recorded only after destruction or
authoritative absence. Observed residual resources and cleanup CNO retain the
same identity-bound reservation for reconciliation and retry; neither completes
the capability until cleanup establishes absence. Production binds that state seam to the durable SSSF owner; the
in-memory implementation is only the deterministic fake. Fabricated capabilities
are rejected, while issued provenance and completion status remain valid across
serialization and supervisor restart. Residual or ambiguous state is preserved
for later reconciliation.

## Aggregate fold

`fold_aggregate` is non-vacuous and deterministic. It folds separately named
work, cleanup, and evidence observations and preserves those component results
when the aggregate is non-PASS:

1. any applicable observed-bad contradiction wins;
2. otherwise a required CNO, missing result, wrong identity, incomplete
   collection, or unverified cleanup yields CNO; and
3. PASS requires every applicable required observation to be observed-good.

Thus successful work plus cleanup CNO remains aggregate CNO while retaining a
positive work observation. A zero-observation fold is CNO.

## Deterministic fake coverage

`FakeSandboxProvider` positively manufactures and validates controls for:

- complete success, create-response ambiguity, and same-key retry without a
  duplicate resource;
- stale/wrong identity and unreachable inspection;
- typed execution timeout, cancellation, output overflow, provider-client
  cleanup CNO, and in-sandbox workload leak;
- missing, tampered, and overflowed artifacts;
- wrong Git ancestry, partial stop, unauthorized destroy, acknowledged destroy
  with residual resources, duplicate resources, and already-absent idempotency;
- interruption before each provider lifecycle boundary plus SSSF-owned secret
  retirement CNO; and
- PASS/FAIL/CNO precedence, including cleanup CNO.

The controls assert typed states, identities, bounds, digests, residual lists,
quiescence domains, and aggregate component preservation. They do not infer a
pass from a failure string and make no Docker, exe.dev, provider, model,
network, credential, browser, or irreversible environment call.
