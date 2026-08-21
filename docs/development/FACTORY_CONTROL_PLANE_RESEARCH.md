# Factory control-plane research

> **Planning status:** `PRESERVE` supporting research only.
>
> **Reviewed repository:** `owainlewis/factory`
>
> **Reviewed commit:** `22d20e62fdc8de809ce69f3bbe1c16a8a8eb7f53`
>
> **Review date:** 2026-08-21
>
> **Authority:** This note does not activate an increment, create a new FUT item, change roadmap sequencing, authorize a dependency, or modify SSSF's accepted control model.

## Executive ruling

Factory is a strong implementation reference for durable software-engineering execution, but it must **not** become an SSSF dependency or a competing control plane.

The useful conclusion is narrower:

> **Factory confirms SSSF's outer-control direction while providing concrete implementation patterns for fencing, reconciliation, capability readiness, fake-backend qualification, crash recovery, and ephemeral execution artifacts. Preserve those patterns as proof and implementation inputs to existing B4/SBX/DSH contracts.**

Factory's current product model is approximately:

```text
Task
  mutable reusable intent
      ↓ snapshot
Run
  immutable invocation
      ↓
Session
  one repository
      ↓
Execution
  durable assignment
      ↓
Attempt
  one leased try
      ↓
Worker
  repository + runtime/process mechanics
```

The operator primarily sees Task, Run and Session. Execution and Attempt remain internal lifecycle records. That separation is useful, but SSSF already has its own stronger identity, qualification and authority model and should not import Factory's product nouns merely because the implementation is sound.

## Review scope

The review covered the current repository tree and the substantive current implementation/design surfaces, including:

- root `ARCHITECTURE.md`;
- `docs/tasks/design.md`;
- `docs/software-factory/vision.md` and the superseded target-architecture record;
- `docs/worker.md`, `docs/local.md`, `docs/remote-workers.md`;
- `docs/cloud-run-agents/design.md` and the Cloud Run experiment directory;
- control-plane Task/Run/Session, routing, claim, lease, event and retry code;
- execution profiles and deterministic fake-cloud backend;
- Worker health/capability registration and repository acquisition;
- Worker attempt lifecycle, supervisor, process-group tests, manifests, reconciliation and cleanup;
- SQLite backup/restore and migration behavior;
- browser Run/Session/Attempt projection;
- CI, release and documentation governance;
- current license and compatibility status.

Generated browser assets were inventoried but are not treated as architectural evidence where authored React/TypeScript source and tests provide the relevant behavior.

## Governing compatibility with SSSF

Factory repeatedly applies principles already accepted by SSSF:

- mutable authoring state is snapshotted before execution;
- code owns durable sequencing and lifecycle state;
- active work has explicit identity and bounded authority;
- retries are descendants of prior history rather than overwrites;
- ambiguity is retained rather than rounded into cleanup success;
- runtime/provider choices are separated from the durable execution lifecycle;
- fake-provider qualification precedes privileged external infrastructure;
- event/result surfaces are bounded;
- recovery re-observes reality instead of assuming pre-crash intent still holds.

This is corroborative research, not a reason to create parallel SSSF abstractions where existing contracts already own the concern.

---

# 1. Attempt authority and stale-executor fencing

Factory gives each active Attempt a random lease token. The control plane stores the digest rather than the token. Active lifecycle mutations require the matching, unexpired authority. Claim request IDs and terminal completion are independently idempotent.

The durable principle for SSSF is:

> **Any executor that can remain alive after execution authority transfers must be mechanically fenced from further mutation.**

This is most relevant when SSSF has concurrent or out-of-process execution owners: Docker sandboxes, remote executors, DSH cells, long-running workers or future elastic backends.

A suitable SSSF shape may be conceptually:

```text
outer_attempt_id
      +
short-lived execution authority
      ↓
trusted owner stores/verifies binding
      ↓
every live mutation requires
  identity + authority + validity
      ↓
CODE accepts or rejects
```

Do not introduce leases into a purely single-process path merely for conceptual symmetry. The requirement activates where stale concurrent executors are physically possible.

### Proof implications

Pressure tests should include:

- old executor continues after replacement;
- duplicate dispatch after an ambiguous response;
- cancellation races with terminal completion;
- authority expires before process start;
- authority expires while descendants remain alive;
- stale event/result publication after authority loss.

Late or stale evidence may remain inspectable, but it must not regain authority to establish success.

---

# 2. Real-process supervision pressure tests

Factory's Worker supervisor is a separate subprocess that anchors ownership of the runtime process group. The associated tests exercise real OS processes rather than only mocked state transitions.

The strongest reusable test pattern is to prove that the execution owner tears down the whole owned descendant set when any of the following occurs:

- explicit cancellation;
- execution timeout;
- parent process loss;
- control-channel loss;
- lease/authority loss;
- invalid input before start.

SSSF already requires the accepted B4 process owner to remain the single subprocess/sequencing owner used by Docker and DSH. Factory therefore supplies a **pressure-test reference**, not a second supervisor design.

### Recommended application

As B4/SBX-5/DSH-0B become active, include negative controls equivalent to:

```text
cancel before child launch
cancel after child launch
parent disappears
control transport disappears
authority expires before start
authority expires during work
timeout while descendants exist
executor restarts after partial preparation
replacement executor observes same durable attempt
```

Terminal proof should establish zero surviving owned descendants where the platform can observe that fact; inability to prove quiescence remains CNO/non-PASS under applicable policy.

---

# 3. Durable execution presence and fail-closed reconciliation

Factory persists Worker-side Attempt manifests and reconciles them after restart against both local and control-plane observations. Its checks include Attempt, Worker, repository, branch/worktree, process and process-group identity. Cleanup is refused when filesystem and Git registration disagree or when process identity is unreconciled.

The useful SSSF principle is:

> **Recovery is a new observation pass over durable identity and provider/process reality, not a replay of remembered intent.**

SSSF should adapt this into existing run/attempt/provider evidence rather than create a new Factory-style Worker manifest namespace.

A compact owner-emitted record may need facts equivalent to:

```yaml
execution_presence:
  outer_attempt_id: ...
  provider_resource_id: ...
  source:
    repository: ...
    commit: ...
    tree: ...
  workspace_identity: ...
  process_owner_identity: ...
  process_identity: ...
  lifecycle_generation: ...
  artifact_refs: ...
  harvest_state: ...
  quiescence_state: ...
```

On restart:

```text
durable SSSF state
+
provider observation
+
process observation
+
source/workspace identity
        ↓
CODE reconciliation
        ↓
continue | harvest | retain | destroy | fail/CNO
```

Never infer cleanup eligibility from existence alone.

### Destructive-action rule

Factory also records cleanup intent before destruction and revalidates identity immediately before removal. Preserve the principle:

> **Irreversible cleanup requires durable intent plus fresh identity proof; uncertainty retains the resource/evidence.**

This belongs primarily in SBX-5 and any later disposable-executor recovery path.

---

# 4. Construct, verify, then atomically publish

Factory's managed-repository cache clones into a temporary private directory, validates repository identity/origin and path properties, and only then installs the cache entry under its stable identity. Interrupted temporary clone state is cleaned under Worker ownership on restart.

SSSF's Source Broker remains intentionally stronger: workers must receive credential-free disposable source at exact repository + commit + tree identity, not an authenticated host checkout.

The reusable implementation law is therefore independent of Factory's `gh` mechanism:

> **Build outside the trusted namespace, verify complete identity and invariants, then publish atomically.**

Candidate uses include:

- Source Broker clone/cache publication;
- generated execution environments;
- restored local state;
- generated authoritative projections;
- recovered artifacts.

This law complements rather than changes existing source-custody authority.

---

# 5. Immutable admission snapshots and generation conflicts

Factory separates mutable Task configuration from immutable Run input. Task updates use expected-generation conflicts; admission freezes the exact prompt, repositories, runtime, timeout, concurrency, generation, schedule context and execution profile used by the Run.

SSSF already uses exact source, protocol, increment and execution identities. Preserve two implementation reminders:

1. **mutable configuration must be snapshotted before work begins;**
2. **stale mutation of mutable configuration should conflict rather than silently overwrite newer state.**

For retries, Factory's strongest execution-profile behavior is that an old Run reuses its frozen profile version even if the operator has since changed the current profile. A new Run may use the new version.

SSSF equivalent:

> **Retry is continuation of an admitted generation, not implicit adoption of current configuration. Material source/runtime/policy change creates a new generation.**

---

# 6. Event identity is distinct from retry/backoff timing

Factory's scheduler keeps the original scheduled occurrence identity separate from its admission retry cursor. A due occurrence freezes a pending snapshot and due instant; transient admission backoff cannot silently turn that occurrence into a later one.

General law:

> **Business/event identity must not be derived from retry timing.**

This is most applicable to FirstMate/control-plane watches, scheduled maintenance and future event-driven intake. The originating event/occurrence remains stable while retry timing is operational state.

No new scheduler abstraction is required in SSSF merely to adopt this law.

---

# 7. Backend, runtime and model/profile stay orthogonal

Factory independently models:

```text
execution backend
agent runtime
provider + model
```

Its proposed Cloud Run path can therefore change compute placement without redefining the Task/Run lifecycle or agent runtime.

SSSF already has the stronger intended split:

```text
SandboxProvider
≠
AgentBackend
≠
model/profile
```

Factory is confirming evidence that this separation should survive implementation pressure during Docker and DSH work.

### Non-decision

Do not introduce Factory's execution-profile type or synthetic-Worker abstraction as an SSSF public concept unless an independently justified active increment requires an equivalent. Existing SSSF contracts own the concern.

---

# 8. Deterministic fake before privileged/expensive provider

Factory implemented versioned execution profiles plus a deterministic fake-cloud backend before implementing real Cloud Run dispatch. The fake exercises the same ordinary Run/Session/Execution/Attempt lifecycle and tests frozen generation, health/disable behavior, retry and request replay.

This strongly corroborates existing SBX-1 direction: provider-neutral contract and deterministic fake before real Docker/provider attachment.

### Conformance-test inputs for SBX-1/SBX-2

Preserve tests equivalent to:

```text
same request identity + same input
  → same execution / idempotent replay

same request identity + materially changed input
  → conflict

provider disabled/unhealthy
  → no new dispatch

provider generation changes after admission
  → admitted work remains unchanged

retry
  → admitted provider/profile generation

new run
  → newly eligible generation

fake and real implementation
  → same provider-neutral lifecycle contract
```

Factory does not change SBX-1 planning state and does not prove SSSF's contract; it provides a useful external reference for what the conformance suite should prevent.

---

# 9. Capability readiness is multidimensional

Factory does not treat "binary exists" as equivalent to runtime readiness. Worker capabilities can be `ready`, `missing`, `unauthenticated` or `unhealthy`; source access is separately probed. Codex weekly usage is observed independently from runtime existence/authentication.

SSSF should preserve a similarly explicit distinction where provider/runtime admission depends on several independent facts.

A future exact schema may differ, but the semantic dimensions resemble:

```text
implementation = AVAILABLE | MISSING
binding/authentication = READY | UNAVAILABLE | CNO
provider_health = READY | DEGRADED | UNAVAILABLE | CNO
quota/capacity = OBSERVED(...) | CNO
capability = PRESENT | ABSENT | CNO
runtime/profile identity = MATCH | MISMATCH | CNO
```

CODE then decides whether the particular assignment is admissible.

Do not collapse those facts into one generic `healthy=true` claim when different remediation/authority consequences follow from each failure class.

Factory also generation-binds Worker registration so a stale registration response cannot re-authorize an obsolete capability snapshot. Preserve that stale-state principle where SSSF later registers long-lived executors.

---

# 10. Start fencing for ambiguous external dispatch

Factory's proposed Cloud Run design addresses a classic failure: an external Run call may succeed while the caller loses the response, causing a retry that starts a duplicate execution.

Its proposed solution gives both dispatches the same durable Attempt identity but requires an independent conditional start fence before either may launch the agent. Only one can win; duplicates exit without doing engineering work.

SSSF principle:

> **Ambiguous external dispatch must not be solved by assuming the first call failed. Duplicate physical executors may exist, but only one may acquire execution authority.**

This is not currently a reason to add a remote backend. Preserve it for any future out-of-process/elastic executor and for DSH seams where duplicate process/container startup can occur after transport ambiguity.

---

# 11. Revoke authority before best-effort infrastructure cancellation

Factory's proposed cloud path records/revokes control-plane authority first, then asks Cloud Run to cancel the external execution and reconciles until the provider reaches a terminal state. A result published after the cancellation decision can remain evidence but cannot convert the Attempt to success.

SSSF should preserve this separation:

```text
CODE revokes execution authority
        ↓
executor can no longer establish accepted success
        ↓
best-effort provider/process teardown
        ↓
reconcile physical reality until quiescent/CNO
```

Therefore:

> **Failure of an external cancellation API must not imply that the executor remains logically authorized.**

This belongs in SBX-5 and any future remote/elastic execution adapter.

---

# 12. Ephemeral completion must be reconstructible; final manifest last

A disposable Factory cloud Job cannot leave a retained worktree. The proposed design therefore uploads bounded outputs, Git state, patch/bundle/recovery artifacts and checksums, then writes a final manifest last. The trusted control plane independently reconstructs a clean checkout at the frozen source and verifies the artifact before treating transport success as execution success.

The durable SSSF principle is:

> **For disposable execution, completion evidence must describe a reconstructible terminal state, and the trusted side must independently reconstruct or validate that state before acceptance.**

A future SSSF terminal artifact for an ephemeral executor should bind at least the relevant equivalents of:

- outer attempt/execution identity;
- exact repository + commit + tree;
- canonical input/protocol digest;
- sandbox/image/runtime/profile identities;
- artifact byte lengths and digests;
- Git/status/result evidence;
- executor identity where policy requires it.

The completeness manifest is published **after** required artifacts. Presence of a partial artifact set is not success.

Although Docker can remain alive long enough for direct harvest, this pattern is still useful as a negative control and becomes especially important for any future remote/elastic provider.

---

# 13. Monotonic deadlines across remote authority seams

Factory's proposed Cloud Run design avoids extending a frozen timeout merely because authority/time responses arrive slowly. It records local monotonic time before requesting the trusted deadline and anchors returned remaining time to that earlier point, so communication delay consumes rather than enlarges the work budget.

Preserve the law:

> **Transport latency may consume a fixed execution budget but must not silently extend it.**

This should inform any B4/DSH/remote-executor seam that translates a trusted durable deadline into process-local timers.

---

# 14. Crash-safe recovery publication

Factory's SQLite backup/restore path follows a high-quality generic state-publication pattern:

```text
observe source identity
→ stage privately
→ transform/snapshot
→ validate
→ sync durable bytes
→ re-check source/preconditions
→ atomically publish without replacement
```

Restore similarly stages migrations/validation before publication and rejects changed or ambiguous source state.

SSSF does not need SQLite because Factory uses SQLite. Preserve only the generic systems law for future mutable durable state, restored evidence indexes, generated authoritative projections or similar artifacts.

---

# 15. Bounded observability and retention

Factory explicitly bounds Worker capacity, event batches, individual event size, total Attempt event bytes, results, errors, repository caches and paginated history.

This is important as SSSF approaches DSH child/subagent execution.

Preserve the audit question:

> **Every queue, list, event stream, retry chain, child set, retained artifact class and result channel should have an explicit bound or a demonstrated reason it is safely unbounded.**

This should become a qualification concern by DSH-3 and later autonomous stages, not a new standalone architecture layer.

---

# 16. Documentation state and mechanically checkable provenance

Factory keeps current implementation, active design and superseded design records visibly separate. That is compatible with SSSF's own planning-state discipline.

The review also observed a useful negative control: current Factory `ARCHITECTURE.md` still identifies an older verification basis while current `main` has moved materially beyond that commit.

The SSSF implication is:

> **Where documentation provenance can be mechanically derived or checked, do not depend indefinitely on manually maintained "verified against commit X" prose.**

This is supporting evidence for FUT-012-style generated/validated derived documentation, not a promotion of FUT-012 by this note.

---

# 17. Mechanically enforce architectural boundaries where possible

Factory includes CI checks for package/import boundaries rather than relying only on architectural prose.

SSSF should apply the same governing idea when implementation structure permits it:

> **Architecture that can be checked should be CODE.**

Potential future examples, subject to actual package/module structure:

```text
outer SSSF control code
must not depend on Cordis implementation packages

DSH adapter
may implement ExecutionCell contracts
but must not import landing/promotion authority

SandboxProvider adapters
must not own verification/acceptance packages
```

Do not create artificial package boundaries merely to satisfy this research note. Add checks only where the boundary is real and violation is mechanically meaningful.

---

# 18. Explicit non-adoptions and weaker Factory semantics

Factory is intentionally a trusted-host execution system. Its Worker can run coding agents using host filesystem, network and credentials. A Git worktree isolates Git state but is explicitly not a hostile-code sandbox.

SSSF must **reject** that trust model.

Required SSSF direction remains:

```text
canonical host checkout + control-plane credentials
            no worker access
                    ↓
credential-free exact Source Broker clone
                    ↓
Docker containment/security boundary
                    ↓
bounded admitted runtime capabilities/effects
```

Other explicit non-adoptions:

| Factory mechanism/direction | SSSF disposition |
| --- | --- |
| Factory control plane/product | Reject as dependency; would duplicate FirstMate/SSSF authority |
| Factory Task/Run database as SSSF truth | Reject |
| Worktree as security isolation | Reject |
| Ambient Worker credentials | Reject |
| Direct host `gh` as general effect-authority model | Reject |
| Trusted-host permission bypass | Reject |
| Process exit as engineering acceptance | Reject |
| Warning-only duplicate effects as final retry policy | Insufficient |
| Persistent retry resolving a newer default-branch commit | Reject by default |
| Cloud Run as new SSSF roadmap target | No authorization / no need |
| Factory React operations UI | Do not add from this research |
| Factory's no-DAG product posture | Not applicable; SSSF deliberately owns a deterministic outer graph |
| Future Temporal-style orchestration substrate | Do not import; SSSF code remains workflow authority |

## Retry/source negative control

Factory documents that its persistent Worker may resolve the repository base at Attempt preparation, so a retry can see newer default-branch state.

SSSF's default must remain stronger:

> **Retry does not imply rebase. Source movement requires an explicit new execution generation or admitted policy transition.**

## External-effect negative control

Factory explicitly warns that an agent retry may repeat external effects. That honesty is useful, but SSSF should continue toward stronger CODE-owned applicability and effect identity where possible:

```text
effect class
+
effect authority
+
effect/idempotency identity where available
+
observed receipt/state
+
retry applicability
```

A warning alone is not sufficient for unattended engineering when deterministic effect safety can be established.

---

# 19. Mapping to existing SSSF work

No new FUT item is required. Apply these findings only through existing owners when they become active and relevant.

| Existing SSSF owner/stage | Factory-derived implementation/proof input |
| --- | --- |
| B4 process owner | Real-process cancel/timeout/parent-loss/authority-loss/descendant pressure tests |
| SBX-1 | Fake/real provider lifecycle equivalence; idempotency and frozen-generation tests |
| SBX-2 | Preserve backend/runtime/model orthogonality; explicit readiness facts |
| SBX-5 | Attempt fencing, durable execution-presence reconciliation, retain-on-ambiguity |
| SBX-5 | Revoke logical authority before best-effort physical teardown |
| SBX-5/SBX-6 | Ordered/idempotent bounded events where such events are part of the accepted owner |
| SBX-6 | Multidimensional capability/readiness state and stale-registration protection where needed |
| SBX-8 | Reconstructible terminal artifacts/independent trusted-side verification as a negative control |
| DSH-0B | Parent loss, authority loss, timeout and descendant-quiescence pressure suite |
| DSH-3+ | Hard bounds on children/events/results/concurrency and retention |
| Future remote/elastic executor | Start fence, short-lived authority, monotonic deadline, manifest-last artifact completion |
| FUT-009/FUT-010 opportunity | Mechanically enforce real architecture boundaries when implementation structure supports it |
| FUT-012 opportunity | Generate/check mechanically derivable documentation provenance |
| FirstMate/watch scheduling | Keep event/occurrence identity separate from retry/backoff timing |

An unlock/opportunity in this table is not activation, promotion or acceptance.

---

# 20. Source identity and revisit rule

This research is pinned to:

```text
repository: owainlewis/factory
commit: 22d20e62fdc8de809ce69f3bbe1c16a8a8eb7f53
```

Factory was in developer preview at review time and explicitly warned of compatibility-breaking changes. Its current implementation, terminology and future cloud design may therefore change substantially.

Revisit the upstream repository when one of these becomes true:

- SSSF is implementing SBX-5 reconciliation/fencing and needs a fresh comparison;
- a remote/elastic executor is seriously proposed;
- DSH reaches stages where long-running/out-of-process worker authority makes stale-executor fencing material;
- a new Factory design materially strengthens ephemeral artifact verification, distributed leases, capability admission or crash recovery.

Do not treat later Factory evolution as automatically authoritative for SSSF. Re-review exact source and preserve only new principles that survive SSSF's own authority, security and simplicity requirements.

## Final research disposition

**PRESERVE.**

Factory is valuable as an external implementation reference because it treats stale state, crash ambiguity, retries, identity, cleanup and provider boundaries as first-class systems problems. SSSF should mine those mechanisms where they tighten existing contracts, while retaining its stronger Docker security boundary, source custody, verification/review/landing authority, exact-head proof and deterministic outer workflow ownership.