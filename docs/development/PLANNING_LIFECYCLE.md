# Future Planning Lifecycle

<!-- canonical transition contract owner: v1 -->

**Canonical transition contract owner:** this document is the only owner of the
SSSF planning state machine. `docs/development/PLANNING_STATE.json` records
current states and transition evidence; it does not redefine this contract.
The candidate register, roadmap, ADRs, manifest, and increment record point
here and must not publish a competing graph.

## Contract boundary

Planning records preserve engineering intent. They are not executable
workflow state, runtime authority, landing authority, acceptance,
certification, or a PRE_CERTIFICATION exit.

The lifecycle distinguishes planning from proof:

> **PRESERVE does not mean approved. APPROVED does not mean sequenced.
> SEQUENCED does not mean active. ACTIVE does not mean proven. PROVEN means
> accepted proof, not merely a planning assertion.**

Every state is one of the following closed values:

- `EXPLORE`
- `PRESERVE`
- `CANDIDATE`
- `DECIDED`
- `SEQUENCED`
- `ACTIVE`
- `PROVEN`
- `DEFERRED`
- `REJECTED`
- `SUPERSEDED`

`DEFERRED`, `REJECTED`, and `SUPERSEDED` are side exits. `DEFERRED` is
re-enterable; `REJECTED` and `SUPERSEDED` are terminal. `PROVEN` is terminal
for the item/version that it proves, although a later item/version may
supersede it.

### Terminal state rules

`PROVEN`, `REJECTED`, and `SUPERSEDED` are terminal states for their recorded
item/version. Only `PROVEN -> SUPERSEDED` is legal after a proof state, and a
successor is a new item/version.

## Legal transition contract

The following table is closed. A transition not listed here is illegal,
including an unknown state, an omitted intermediate state, or an edge inferred
from a commit subject. The durable state record must list each edge as a
`from`/`to` record with durable evidence references.

| From | Legal `from -> to` edges | Rule |
|---|---|---|
| `EXPLORE` | `EXPLORE -> PRESERVE`; `EXPLORE -> CANDIDATE`; `EXPLORE -> DEFERRED`; `EXPLORE -> REJECTED`; `EXPLORE -> SUPERSEDED` | Conversation may be retained, evaluated directly, deferred, rejected, or replaced. |
| `PRESERVE` | `PRESERVE -> EXPLORE`; `PRESERVE -> CANDIDATE`; `PRESERVE -> DEFERRED`; `PRESERVE -> REJECTED`; `PRESERVE -> SUPERSEDED` | A preserved reference may return to exploration or enter evaluation. |
| `CANDIDATE` | `CANDIDATE -> PRESERVE`; `CANDIDATE -> DECIDED`; `CANDIDATE -> DEFERRED`; `CANDIDATE -> REJECTED`; `CANDIDATE -> SUPERSEDED` | Evaluation either remains a reference, resolves design, or exits. |
| `DECIDED` | `DECIDED -> CANDIDATE`; `DECIDED -> SEQUENCED`; `DECIDED -> DEFERRED`; `DECIDED -> REJECTED`; `DECIDED -> SUPERSEDED` | A decision may be reopened, sequenced, or explicitly exited. |
| `SEQUENCED` | `SEQUENCED -> DECIDED`; `SEQUENCED -> ACTIVE`; `SEQUENCED -> DEFERRED`; `SEQUENCED -> REJECTED`; `SEQUENCED -> SUPERSEDED` | Sequencing adds dependency position. Only this edge may enter `ACTIVE`. |
| `ACTIVE` | `ACTIVE -> SEQUENCED`; `ACTIVE -> PROVEN`; `ACTIVE -> REJECTED`; `ACTIVE -> SUPERSEDED` | Work may be deactivated or exited; `PROVEN` requires the proof contract below. |
| `PROVEN` | `PROVEN -> SUPERSEDED` | `PROVEN` is terminal for this item/version; a successor is a new governed item/version. |
| `DEFERRED` | `DEFERRED -> EXPLORE`; `DEFERRED -> PRESERVE`; `DEFERRED -> CANDIDATE`; `DEFERRED -> DECIDED`; `DEFERRED -> SEQUENCED` | Re-entry must name and return to the exact recorded `return_to` state. It cannot jump to `ACTIVE` or `PROVEN`. |
| `REJECTED` | no outgoing edge | Terminal. Reconsideration requires a new candidate identity and record. |
| `SUPERSEDED` | no outgoing edge | Terminal. The successor is a new item/version, not re-entry into this record. |

There is **no atomic `DECIDED -> ACTIVE` edge**. A durable `SEQUENCED`
record is required before an `ACTIVE` transition. History is preserved; a
commit message, tag movement, or rewritten parent chain cannot manufacture a
missing state record.

### Side exits, re-entry, and terminality

- `DEFERRED` is a side exit from a resumable state. The transition entering
  `DEFERRED` must retain that source as `return_to`, and a current deferred
  record must retain the same value as `return_state`; the only legal return
  edge is `DEFERRED -> return_to`. An outgoing transition cannot choose or
  replace the retained return state.
- `REJECTED` is terminal. It cannot be reopened by editing its state or by a
  later implementation branch.
- `SUPERSEDED` is terminal. A replacement records a new item/version and does
  not mutate this record.
- `PROVEN` is terminal for the exact item/version. It means implementation,
  deterministic proof, retained evidence, required documentation, and
  immutable accepted source identity agree. `PROVEN` is a proof claim bounded
  by the proof matrix; it is never inferred from `ACTIVE`, local tests, a
  roadmap row, or an ADR.
- A transition history must be contiguous: each next `from` equals the
  previous `to`, and every edge is present in the table. Unknown, illegal, or
  skipped transitions fail closed.

## State meanings

### `EXPLORE`

Conversation, comparison, or incomplete research. No durable implementation
obligation exists.

### `PRESERVE`

A future reference or idea source is retained without approval or an
implementation slot.

### `CANDIDATE`

A plausible future primitive is recorded for formal evaluation.

### `DECIDED`

The architectural question is resolved. The decision is design intent, not an
implementation slot.

### `SEQUENCED`

The decided work has an explicit dependency position in `ROADMAP.md`, linked
ADR/candidate records, and a durable state record. `SEQUENCED` is not active,
does not create a task, and does not authorize execution.

### `ACTIVE`

`ACTIVE` is engineering authorization only. `ACTIVE` is intake eligibility
only. `ACTIVE` is never task creation. `ACTIVE` is never execution authority.
`ACTIVE` is never landing authority. `ACTIVE` is never PRE_CERTIFICATION exit.
`ACTIVE` is never acceptance. `ACTIVE` is never certification. `ACTIVE` is
never live enablement. `ACTIVE` is never `PROVEN`.

An `ACTIVE` record is honest only when every bounded increment has all of these
exact identities in the durable record:

- named increment ID;
- exact branch name;
- exact PR URL/identity;
- exact source commit SHA;
- exact source tree SHA; and
- authoritative repository-document references.

The record must also remain subject to ordinary admission, exact-source
validation, review, acceptance, and existing repository gates. If any required
identity does not yet exist, the canonical state is `SEQUENCED` and the
`ACTIVE` transition is deferred. No partial, guessed, or placeholder `ACTIVE`
record is valid.

### `PROVEN`

`PROVEN` is proof state only. It is reached only after the accepted
implementation, deterministic proof, retained evidence, required
 documentation, and immutable source identity agree. It does not grant a new
runtime authority; runtime behavior remains owned by executable code and its
acceptance gates.

The durable `proven_proof` record must set `accepted_implementation` to true;
retain nonempty, existing `acceptance_evidence_refs`,
`implementation_evidence_refs`, `proof_evidence_refs`, and
`documentation_evidence_refs`; and bind the accepted source with exact
40-character `source_commit` and `source_tree` identities. A `proven_proof`
claim is valid only after a legal transition reaches `PROVEN`; it remains
required historical proof if the legal `PROVEN -> SUPERSEDED` edge follows.
An item that never reached `PROVEN` may not carry the claim.

## Durable records and ownership

`PLANNING_STATE.json` is the durable current-state and transition-evidence
record. It is not a notification feed, execution queue, runtime database, or
replacement for the candidate/ADR/roadmap documents. Git history remains
immutable predecessor evidence; commit subjects are not state records.

- `FUTURE_CANDIDATES.md` records item state and design context.
- `ROADMAP.md` records dependency position and current lifecycle holds.
- ADRs record architectural decisions and boundaries.
- `INCREMENT_PROTOCOL.md` governs any later bounded implementation.
- `docs/validation/check_planning_foundation.py` is the sole deterministic
  validation owner for this planning foundation.

No planning record, ADR, manifest entry, roadmap row, or validation result is
runtime authority. The current implementation remains limited to planning
records and offline validation; it does not add a FirstMate watcher, producer,
consumer, feed, runtime, sandbox, provider, credential, ADW, Docker, Wayfinder,
or DSH behavior.
