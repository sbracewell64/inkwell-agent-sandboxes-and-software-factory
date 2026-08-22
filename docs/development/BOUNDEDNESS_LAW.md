# Boundedness Law

> **Authority:** Captain-directed cross-cutting SSSF requirement.
>
> **Status:** DECIDED as an architectural law. The initial repository-wide audit and the continuous enforcement mechanism landed with `BOUND-1`; see `docs/increments/BOUND-1_BOUNDEDNESS_AUDIT_AND_ENFORCEMENT.md` for what that increment does and does not establish. BOUND-1 is a landed implementation, not an accepted, certified, or SBX-2-unlocking one.
>
> **Owners in this repository:** the registry is `docs/reference/BOUNDEDNESS_REGISTRY.json`; the validator is `docs/validation/check_boundedness.py`; source ownership is declared with `BOUNDEDNESS-OWNER` markers and shared enforcement mechanisms with `BOUNDEDNESS-POLICY` markers.
>
> **Scope:** SSSF, SandboxProvider implementations, AgentBackend implementations, FirstMate-facing execution surfaces owned by SSSF, DSH ExecutionCells and admitted DSH plugins/capabilities, validators, evidence stores, retained artifacts, and future remote/elastic executors.
>
> **Non-effect:** This record does not activate an increment, change the Docker → baseline → Wayfinder → DSH sequence, or itself establish that current code satisfies the law.

## Governing law

> **Every list, queue, log, retry chain, event stream, child-agent set and retained-artifact surface needs an explicit bound or an explicit reason it is safely unbounded.**

Generalized form:

> **Every state surface whose cardinality, byte size, depth, duration, concurrency, retention, or resource consumption can grow as work, time, input, retries, descendants, or observations accumulate must have a declared growth contract.**

A growth contract is one of:

1. **EXPLICIT_BOUND** — CODE enforces a finite limit;
2. **DERIVED_BOUND** — a finite limit is mechanically implied by another authoritative bound and the derivation is recorded;
3. **SAFE_UNBOUNDED** — no finite local limit is imposed, but a specific invariant and proof explain why unbounded growth is safe in the intended operating domain.

`SAFE_UNBOUNDED` is exceptional. "We do not expect it to get large", "the operator can clean it up", "the model should stop", or "storage is cheap" are not sufficient justifications.

Missing classification is non-compliant. Missing evidence is not implicit safety.

## Why this is a CODE law

Unbounded growth is a deterministic systems property, not a semantic judgment problem. Once a surface and its operating contract are known, CODE owns:

- the limit or derived limit;
- admission/backpressure;
- overflow behavior;
- retry/depth ceilings;
- retention/eviction;
- cleanup;
- observability of utilization and overflow;
- validation that the declared contract remains present.

Agents may recommend a suitable bound when workload semantics are uncertain. They do not own enforcement and cannot enlarge a bound merely by deciding more work would be useful.

## Initial repository-wide audit

A dedicated bounded increment must inventory the current accepted implementation before this law can be claimed PROVEN.

The audit must inspect at least:

- in-memory and durable lists/collections that grow with work;
- queues, pending-work sets, mailboxes, inboxes and scheduler backlogs;
- stdout/stderr capture and other command-output buffers;
- logs, traces, event histories, telemetry streams and evidence journals;
- API pagination/list accumulation and caches;
- retry chains, repair/refinement loops and retry histories;
- process, job, worker and sandbox concurrency sets;
- DSH children/subagents, delegation depth and parallel fan-out;
- model context/history projections where SSSF owns the budget;
- artifacts, patches, bundles, archives, screenshots and evidence retained on disk;
- repository/worktree/sandbox caches and cleanup queues;
- scheduled occurrences and failed-delivery/reconciliation queues;
- any future remote/elastic dispatch records or recovery artifacts;
- any other state whose size can increase monotonically with input, time or repeated work.

The audit must distinguish **surface discovery** from **bound verification**. Finding a limit in code is not sufficient until the owner, enforcement point, overflow behavior and proof are identified.

## Machine-readable boundedness registry

The audit must produce one authoritative, repository-contained, machine-readable registry. Recommended identity:

`docs/reference/BOUNDEDNESS_REGISTRY.json`

The exact schema may be refined in the implementing increment, but every entry must bind at least:

```text
surface_id
owner
source_refs
surface_kind
resource_dimensions
classification = EXPLICIT_BOUND | DERIVED_BOUND | SAFE_UNBOUNDED
limit/value or derivation
policy_identity
admission_or_backpressure
on_limit_behavior
retention_or_cleanup
observability
verification_refs
status = observed-good | observed-bad | could-not-observe
```

`resource_dimensions` may include count, bytes, depth, duration, concurrency, retained age, disk footprint, token/context size, or another explicit unit.

For `SAFE_UNBOUNDED`, the registry must additionally contain:

```text
safety_invariant
why_no_finite_local_bound_is_required
failure_consequence
falsification_test_or_review
reviewer/authority
```

If those fields cannot be made concrete, the surface must be bounded.

## Continuous enforcement after the audit

The audit is not a one-time spreadsheet. Its main deliverable is a continuing enforcement mechanism.

### 1. Canonical validator

Land one deterministic validator, recommended identity:

`docs/validation/check_boundedness.py`

It must fail when, at minimum:

- a registered surface has no classification;
- an explicit bound is absent, malformed, zero/negative where invalid, or no longer connected to its owner;
- a derived bound loses its authoritative parent or derivation;
- a `SAFE_UNBOUNDED` entry lacks its invariant/proof fields;
- a source ownership marker refers to no registry entry;
- a registry entry points to missing/renamed owner source without an explicit retirement;
- duplicate surface IDs or competing owners exist;
- a bound changes without the boundedness delta being declared by the increment;
- an overflow/limit path has no specified deterministic behavior;
- a surface required by a qualified stage is CNO where PASS policy requires observation.

Output must be machine-readable PASS / FAIL / CNO with FAIL > CNO > PASS precedence.

### 2. Bidirectional source ↔ registry coverage

The implementing increment must choose the smallest robust mechanism for linking real code owners to registry entries. Prefer stable near-owner declarations/markers or typed policy identities over a second runtime framework.

The validator must check both directions:

```text
source declaration → exactly one registry entry
registry entry     → existing declared source owner
```

A registry that can silently omit a new growing surface is not sufficient.

Static discovery heuristics may additionally scan changed code for likely growth surfaces (queue construction, append/extend accumulation, retry loops, event writers, child spawning, retained artifact writes, caches). Such heuristics are an omission detector, not the source of truth; false positives may be waived only by an explicit, reviewable not-applicable record.

### 3. Increment-protocol boundedness delta

Every implementation increment must state one of:

```text
boundedness_delta:
  added: [...surface_ids]
  changed: [...surface_ids]
  retired: [...surface_ids]
```

or:

```text
boundedness_delta: none
boundedness_reason: <why the diff cannot create/change a growing surface>
```

An increment touching a registered growth owner without declaring the corresponding delta is incomplete.

### 4. Watched-red controls

The boundedness validator must include non-vacuous watched-red mutations proving it detects at least:

- removal of a limit;
- bound changed upward without declared delta;
- orphaned registry entry;
- source marker without registry entry;
- duplicate owner/surface identity;
- missing overflow behavior;
- retry ceiling removed;
- child/delegation depth or fan-out ceiling removed;
- retention/eviction disabled;
- invalid `SAFE_UNBOUNDED` justification;
- CNO narrowed to PASS.

A generic whole-document digest failure does not count as proof of these individual properties.

### 5. Runtime proof where the surface is dynamic

Where practical, each dynamic bound should expose enough facts to prove enforcement, such as:

- current/high-water utilization;
- configured/effective limit;
- rejected/deferred/dropped/evicted count;
- overflow reason;
- cleanup/retention outcome.

Qualification should exercise the boundary at `limit - 1`, `limit`, and `limit + 1` or the closest meaningful equivalents. The `+1` case must demonstrate the intended deterministic behavior rather than uncontrolled growth.

### 6. CI and acceptance

Once implemented and qualified, the canonical CI contract must run the boundedness validator. Required CI is not satisfied by a documentation-only check if executable source/registry linkage can be observed.

No increment may claim acceptance if its required boundedness controls are FAIL or CNO under a PASS-required policy.

### 7. Periodic complete re-audit

Continuous checks protect known and declared owners, but architecture changes can reveal new categories. Therefore perform a complete boundedness re-audit at least at these natural boundaries:

- before Docker commissioning / SBX-8 freeze;
- before DSH child/subagent parallelism is admitted at DSH-3;
- before richer plugin/capability admission at DSH-5;
- before governed self-evolution at DSH-8;
- whenever an architecture change introduces a new scheduler, executor, durable store, cache, remote transport, or autonomous descendant class.

The re-audit updates the same registry; it does not create another boundedness database.

## Required overflow semantics

A bound is incomplete without behavior at the boundary. Each surface must choose and prove one or more explicit outcomes appropriate to its role:

```text
REJECT
BACKPRESSURE
BLOCK/WAIT_WITH_TIMEOUT
DEFER
EVICT_OLDEST
EVICT_POLICY
TRUNCATE_WITH_EXPLICIT_STATUS
SPILL_TO_BOUNDED_EXTERNAL_STORE
CANCEL
FAIL
COULD_NOT_OBSERVE
```

Silent truncation, silent eviction, silent retry cessation, silent child dropping, and silent artifact deletion are forbidden when the dropped state can affect engineering meaning or proof.

## Interaction with evidence preservation

Evidence discipline does not imply infinite retention.

If historical evidence must remain immutable, bound the *retained set* through an explicit retention/archive policy rather than mutating accepted evidence in place. Immutable proof tags and artifacts required by accepted policy remain preserved according to their own retention owner; the boundedness registry records that owner and any intentionally permanent retention reason.

Where permanent retention is truly required, it may be `SAFE_UNBOUNDED` only if the operating assumption, storage growth consequence, archive strategy and falsification/oversight path are explicit.

## DSH-specific requirements

Before DSH-3, the registry/validator must mechanically cover at least:

- maximum child count per parent;
- maximum delegation depth;
- maximum simultaneously active children;
- aggregate child token/time/cost/tool budgets;
- retry/refinement counts;
- pending/background child result retention;
- inter-agent message/mailbox queues if admitted;
- active model context/projection budget where SSSF owns it;
- tool/MCP catalog/schema exposure budget where applicable.

DSH's ability to spawn another unit never implies authority to enlarge these bounds.

## Audit exit criteria

The initial boundedness audit is complete only when:

1. every discovered growth surface has one stable ID and owner;
2. every entry is `EXPLICIT_BOUND`, `DERIVED_BOUND`, or justified `SAFE_UNBOUNDED`;
3. enforcement and overflow behavior are identified;
4. required dynamic boundaries are tested;
5. the registry validator and watched-red controls are non-vacuous;
6. source↔registry coverage is bidirectional;
7. the canonical CI contract runs the validator;
8. the increment protocol requires a boundedness delta;
9. remaining CNOs are explicit and cannot be interpreted as PASS;
10. assignment-distinct review confirms the audit did not merely document obvious surfaces while missing material growth owners.

## Governing shorthand

Use this review question whenever a new execution feature is proposed:

> **What grows, who owns the bound, what happens at +1, and how will CI know if that protection disappears?**
