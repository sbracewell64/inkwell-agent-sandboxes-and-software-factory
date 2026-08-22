# Future SSSF Candidate Register

This is the durable register for future architecture and research items. It
records current item state; the closed transition contract is owned only by
[`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md), and the current state/evidence
record is [`PLANNING_STATE.json`](PLANNING_STATE.json).

The register does not create tasks or runtime authority. `ACTIVE` is an
engineering authorization/intake state, not `PROVEN` or runtime authority.

authoritative planning source: planning/future-sssf; commit: d75103fb7ef8dd4ca40f62d40fc7479369bbdf0b; tree: e29628eb5754a032dce989166f287b82d5c877dc; generation: planning/future-sssf@d75103fb7ef8dd4ca40f62d40fc7479369bbdf0b:e29628eb5754a032dce989166f287b82d5c877dc

## Register

| ID | Item | State | Decision / sequence | Notes |
|---|---|---|---|---|
| FUT-001 | Bounded autonomous DSH execution cells | SEQUENCED | [`ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md`](../decisions/ADR-0007-SSSF-OUTER-AUTHORITY-DSH-INNER-AUTONOMY.md); long-range roadmap | SSSF owns outer authority; DSH may exercise bounded inner autonomy. This item is not active. |
| FUT-002 | Awesome DSH Plugin catalog as future research/reuse source | PRESERVE | none | Catalog inclusion is not trust or production eligibility. |
| FUT-003 | FirstMate planning-transition awareness | ACTIVE | [`ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`](../decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md); `FP-001` + `FM-FP-001` | Authoritative planning authorization is ACTIVE, not PROVEN; production landing/enablement remains separately held. |
| FUT-004 | LLM-as-a-Verifier as post-DSH research source | PRESERVE | `FUT-004_LLM_AS_VERIFIER_REFERENCE.md` | State-only projection; detail remains outside this bounded planning repair. |
| FUT-005 | Verifier-guided DSH progress and refinement | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | State-only projection; no implementation or production evaluation authority. |
| FUT-006 | Best-of-N DSH candidate selection | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | State-only projection; no implementation or production evaluation authority. |
| FUT-007 | Typed criteria decomposition for inner semantic evaluation | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | State-only projection; no implementation or production evaluation authority. |
| FUT-008 | Hierarchical probabilistic-verifier evidence and cost telemetry | CANDIDATE | `VERIFIER_DSH_RESEARCH.md`; unsequenced | State-only projection; verifier output remains advisory. |
| FUT-009 | SSSF architecture-unit contract and generated governance views | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | State-only projection; no governance runtime is authorized. |
| FUT-010 | Compact SSSF architectural laws | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | State-only projection; no competing constitution or runtime is authorized. |
| FUT-011 | Instruction-artifact governance | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | State-only projection; no instruction router or runtime is authorized. |
| FUT-012 | Deterministic derived documentation | CANDIDATE | `AE_GOVERNANCE_RESEARCH.md`; unsequenced | State-only projection; no generated governance runtime is authorized. |
| FUT-013 | Agent engineering skill repositories as research sources | PRESERVE | `AGENT_ENGINEERING_SKILLS_RESEARCH.md` | State-only projection; no competing skill router is authorized. |

## Projection boundary

This register is a current-authority state projection, not a complete research
corpus. Its machine-readable scope is in `PLANNING_STATE.json`: all FUT-001
through FUT-013 states are included, while detailed research prose for the
preserved/candidate items is explicitly out of scope. The projection cannot
answer SBX-2 readiness, activation, implementation, landing, acceptance,
certification, or live enablement. BOUND-1 is separately projected as
`SEQUENCED` and must complete and qualify before SBX-2 can leave `HELD`.

## FUT-001 — Bounded autonomous DSH execution cells

### Status

`SEQUENCED`

This item is **not active**. It remains a long-range planning direction and
has no DSH implementation authorization.

### Confirmed architectural direction

```text
SSSF deterministic work graph
        -> bounded autonomous DSH execution cell
        -> deterministic SSSF verification / acceptance
```

SSSF retains outer authority over execution-domain identity, objective and
role, source/workspace custody, eligible models/backends, resource/time/token/
cost ceilings, external-effect policy, maker/checker independence, retries,
deterministic verification, acceptance, commit/promotion, and terminal state.

DSH may eventually qualify substantial inner autonomy inside one externally
bounded execution cell, including multi-turn reasoning, bounded refinement,
subagents, inner workflows, and adaptive orchestration. Internal autonomy
cannot commit, promote, alter the SSSF graph, or own acceptance.

### Cordis boundary

SSSF does not import or expose Cordis as its architecture. Cordis remains an
internal DSH implementation dependency, and any future DSH boundary must stay
provider-neutral to SSSF.

### Prerequisites

Before production DSH adoption, the existing SSSF execution/isolation
foundations, qualified backend contracts, source custody, lifecycle/evidence,
hard termination, quiescence, and deterministic acceptance must be proven
independently. This record does not authorize those implementations.

## FUT-002 — Awesome DSH Plugin catalog

### Status

`PRESERVE`

The catalog is a future research/reference source, not an allowlist,
marketplace, or production trust decision. A later candidate must inspect any
source directly, pin exact identities, and pass the applicable deterministic,
security, isolation, lifecycle, and semantic gates.

## FUT-003 — FirstMate planning-transition awareness

### Status

`ACTIVE`, not `PROVEN`

The architectural decision and bounded increment authorization are recorded
by the authoritative planning generation. The durable state record is bound to
that exact source identity; an older internally valid snapshot cannot demote
this state.

The architectural decision is recorded in
[`ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md`](../decisions/ADR-0005-FIRSTMATE-PLANNING-TRANSITION-AWARENESS.md).
The durable state record is [`PLANNING_STATE.json`](PLANNING_STATE.json), which
records the legal `SEQUENCED` to `ACTIVE` edge and binds it to the exact
planning source/generation above. `FP-001` and `FM-FP-001` are active-not-proven
bounded increments named by that authoritative source. Their active planning
state does not establish accepted implementation, landing, certification,
live enablement, or `PROVEN`.

### Problem and decision

FirstMate may eventually need deterministic awareness of deliberate SSSF
planning promotions without inferring work from prose or arbitrary document
diffs. The intended future design is a typed, source-bound planning signal
consumed through existing authenticated admission machinery, not a semantic
reread of planning documents and not a second polling daemon.

This planning repair does **not** add a feed, watcher, FirstMate custom check,
producer, consumer, task, or runtime path. It records the bounded design only.

### Authority boundary

Browser Sol/Captain-controlled planning records own promotion through
`SEQUENCED` and `ACTIVE`. A future implementation would still require ordinary
FirstMate admission, exact source validation, and the existing SSSF acceptance
boundary.
No planning record creates a task, grants execution authority, authorizes
landing, exits PRE_CERTIFICATION, accepts or certifies work, enables a live
source, or means `PROVEN`.

`ACTIVE` would be engineering authorization and intake eligibility only. It
would never be task creation, execution authority, landing authority,
PRE_CERTIFICATION exit, acceptance, certification, live enablement, or proof.
`PROVEN` would remain downstream proof state under the canonical lifecycle
contract.

### Required future admission inputs

The exact implementation-binding requirements for later admission are owned by
[`PLANNING_LIFECYCLE.md`](PLANNING_LIFECYCLE.md). The current
planning-authority binding is not an accepted implementation binding and does
not bypass those requirements.

The authoritative `ACTIVE` planning state does not create a task or permit
execution, landing, acceptance, certification, live enablement, or proof. No
SSSF producer, FirstMate consumer, watcher, credential, sandbox, provider, ADW,
Docker, Wayfinder, DSH behavior, or live enablement is part of this record.
