# FUT-003 Planning Foundation Repair

**Status:** documentation and offline-validator candidate; not a FUT-003 runtime
implementation and not a `PROVEN` or live-enable claim

- **Starts from:** `991d3a64f1b96a8b9637f97060d692af3518228f`
- **Starting tree:** `7b88546cd1f63e8304325ee35be37893268ae0e0`
- **Immutable predecessor PR #16 head:** `56b4542a38af8e4435da0fa32ac12497aa6f6016`
- **Immutable predecessor tree:** `bf9a745b861242d131452815556edef654994a83`
- **Predecessor declared base:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`
- **Lifecycle owner:** [`PLANNING_LIFECYCLE.md`](../development/PLANNING_LIFECYCLE.md)
- **State record:** [`PLANNING_STATE.json`](../development/PLANNING_STATE.json)
- **Validation owner:** [`check_planning_foundation.py`](../validation/check_planning_foundation.py)

## Intent

Repair the planning/lifecycle foundation carried by stale SSSF PR #16 without
rewriting that immutable predecessor or treating its head as current. The new
successor is based on supplied current main, not on the predecessor's stale
base. Reconcile
ADR-0005, define one closed transition contract, preserve durable sequencing,
keep FUT-001/DSH sequenced and inactive, defer FUT-003 activation until exact
identities exist, allocate unique ADR-0007 for DSH, and preserve current
SBX-0/SBX-1/held-SBX-2 truth.

## Design and ownership

- `PLANNING_LIFECYCLE.md` is the only lifecycle graph/transition owner.
- `PLANNING_STATE.json` is the durable current-state and legal-transition
  evidence record; commit subjects are not state.
- Candidate, roadmap, ADR, manifest, and increment surfaces point to the
  lifecycle owner rather than restating a competing graph.
- `check_planning_foundation.py` is offline, deterministic, side-effect-free,
  and owns the watched-red controls for this foundation.
- `ACTIVE` is engineering authorization/intake eligibility only and remains
  unrecorded for FUT-003 because FP-001/FM-FP-001 lack exact bindings.

## Scope

This increment changes planning documentation, ADR identity allocation,
manifest routing, the durable planning state record, and provider-free
validation/tests. It does not add runtime, ADW, sandbox, provider, credential,
watcher, FirstMate producer/consumer, feed, Docker, Wayfinder, or DSH
behavior.

Current SBX lifecycle status and all existing holds remain authoritative: SBX-1
is a landed implementation but not activated, accepted, certified, or
real-provider-proven, and it does not unlock held SBX-2.

## Deterministic acceptance

Run:

```text
python3 docs/validation/check_planning_foundation.py
PYTHONPATH=.:adws pytest -q tests/test_planning_foundation.py
```

The validator positively checks the canonical lifecycle, all legal edges,
terminal/re-entry rules, durable `SEQUENCED` records, exact ACTIVE identity
shape, ADR inventory, current SBX holds, ownership, and links. In-memory
watched-red defects cover stale ADR status, illegal/unknown/skipped edges,
missing sequencing, unbound/partial ACTIVE identity, ACTIVE authority escape,
duplicate ADR identity, roadmap regression, competing lifecycle owners, and
broken cross-references. It manufactures each defect without writing files.

No passing local control promotes FUT-003 to `ACTIVE` or `PROVEN`; normal
review, acceptance, PRE_CERTIFICATION, and live-enablement authority remain
outside this candidate.
