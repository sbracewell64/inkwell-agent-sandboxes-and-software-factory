# FUT-003 Planning Foundation Repair

**Status:** documentation and offline-validator candidate; not a FUT-003 runtime
implementation and not a `PROVEN` or live-enable claim

authoritative planning source: planning/future-sssf; commit: eab880656b4ef00174ea514cca128f6336632fcf; tree: 5328b8a437d894682f4ac1c5d7ae581694410c43; generation: planning/future-sssf@eab880656b4ef00174ea514cca128f6336632fcf:5328b8a437d894682f4ac1c5d7ae581694410c43

- **Starts from:** `991d3a64f1b96a8b9637f97060d692af3518228f`
- **Starting tree:** `7b88546cd1f63e8304325ee35be37893268ae0e0`
- **Immutable predecessor PR #16 head:** `56b4542a38af8e4435da0fa32ac12497aa6f6016`
- **Immutable predecessor tree:** `bf9a745b861242d131452815556edef654994a83`
- **Predecessor declared base:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`
- **Lifecycle owner:** [`PLANNING_LIFECYCLE.md`](../development/PLANNING_LIFECYCLE.md)
- **State record:** [`PLANNING_STATE.json`](../development/PLANNING_STATE.json)
- **Validation owner:** [`check_planning_foundation.py`](../validation/check_planning_foundation.py)
- **Authoritative planning source:** `planning/future-sssf` at observed commit `eab880656b4ef00174ea514cca128f6336632fcf`, tree `5328b8a437d894682f4ac1c5d7ae581694410c43`, generation `planning/future-sssf@eab880656b4ef00174ea514cca128f6336632fcf:5328b8a437d894682f4ac1c5d7ae581694410c43`

## Intent

Update the existing successor PR #25 in place without rewriting PR #23 or PR
#24 or treating either predecessor head as current. The successor is based on
the supplied contribution target and carries PR #24's eight commits unchanged
before the bounded authority correction. Reconcile
ADR-0005, define one closed transition contract, preserve durable sequencing,
keep FUT-001/DSH sequenced and inactive, reconcile FUT-003 to the
authoritative ACTIVE-but-not-PROVEN generation, allocate unique ADR-0007 for
DSH, and preserve current
SBX-0/SBX-1/held-SBX-2 truth.

## Preserved pre-correction red evidence

Before this correction, PR #24 exact head `05d3addf8c9120e0824400041fa7235410a7ec4b`
was directly reproduced as follows:

- `python3 -m pytest -q tests/test_planning_foundation.py -k 'windows_symlink_privilege'`
  selected zero tests, deselected 18, and returned 5.
- A synthetic `Path.symlink_to` WinError 1314 caused the canonical validator to
  print `observed-good` and return 0 while listing symlink properties as
  could-not-observe. An unrelated `OSError`/WinError 9999 produced the same
  result, proving capability laundering.
- The PR #24 validator returned `observed-good` for its internally consistent
  FUT-003 `SEQUENCED` snapshot while authoritative
  `planning/future-sssf@5f83760a6d71bb798b9f652f21267fad4b743f16:6e33db5ae5f7d43bf3a7f8c351d888c599d1997d`
  recorded FUT-003 `ACTIVE`. The stale snapshot had no source-generation
  binding, so the newer authority could be demoted without detection.

These observations remain adverse evidence for PR #24; they are not rewritten
or treated as a pass after the correction.

## Closed-set register admission — ruling g1+g2 on control 10

The generation rebind to `eab880656b4ef00174ea514cca128f6336632fcf` /
`5328b8a437d894682f4ac1c5d7ae581694410c43` is complete across every state-bearing
surface, the manifest, `PLANNING_STATE.json`, the CI authority fetch, and the
CI-contract validator.

The observed authority declares four identities that the earlier governed universe
omitted. Ruling g1 authorized exact closed-set admission of `FUT-014`, `FUT-015`, and
`FUT-016`; ruling g2 additionally authorized extending the closed lifecycle projection
by exactly `WAYFINDER-0` = `SEQUENCED`. Both are recorded here:

| Identity | Authority declaration | Projected state |
|---|---|---|
| `FUT-014` | Poker School Phase A Wayfinder product-commissioning POC | `SEQUENCED` |
| `FUT-015` | Agent Lightning gated sandbox optimization POC | `SEQUENCED` |
| `FUT-016` | Deterministic control-band maintenance loop | `CANDIDATE` |
| `WAYFINDER-0` | Configure the Captain's existing Wayfinder transport | `SEQUENCED` |

This repairs closed-set correspondence with the exact ruled generation; it does not
loosen the closed-set invariant. A validator cannot establish applicability to
`eab8806` while refusing an identity that generation lawfully contains. None of the
four is `ACTIVE`: admission records planning position only and creates no task,
execution, landing, acceptance, certification, commissioning, or live enablement.
`WAYFINDER-0` in particular is not configured, commissioned, executed, or proven, and
no Docker/Wayfinder/DSH prerequisite semantics change.

Per ruling g2 the negative closure controls are preserved and extended. The watched-red
set now proves, causally, that each of these is non-PASS: `WAYFINDER-0` omitted from the
authority roadmap (`authority-omitted-wayfinder-0`); `WAYFINDER-0` duplicated
(`authority-duplicate-wayfinder-0-heading`); `WAYFINDER-0` promoted off `SEQUENCED`
(`authority-wayfinder-0-state-change`); and an ungoverned lifecycle identity injected
into the authority roadmap (`authority-ungoverned-lifecycle-identity`). The pre-existing
stale-generation, missing, duplicate, and conflicting-identity controls are unchanged and
still fire. Each new control was verified by neutering its mutation to a no-op and
observing the validator report `watched-red controls did not go red: <control>`, so none
of them can pass vacuously.

## Design and ownership

- `PLANNING_LIFECYCLE.md` is the only lifecycle graph/transition owner.
- `PLANNING_STATE.json` is the durable current-state and legal-transition
  evidence record; commit subjects are not state.
- Candidate, roadmap, ADR, manifest, and increment surfaces point to the
  lifecycle owner rather than restating a competing graph.
- `check_planning_foundation.py` is deterministic and side-effect-free; it
  observes a pre-fetched current-authority Git ref read-only and owns the
  watched-red controls for this foundation.
- `ACTIVE` is engineering authorization/intake eligibility only. The
  authoritative planning binding records FUT-003 as ACTIVE, not PROVEN, without
  granting task, execution, landing, acceptance, certification, or live-enable
  authority.

## Scope

This increment changes planning documentation, ADR identity allocation,
manifest routing, the durable planning state record, and provider-free
validation/tests. It does not add runtime, ADW, sandbox, provider, credential,
watcher, FirstMate producer/consumer, feed, Docker, Wayfinder, or DSH
behavior.

Current SBX lifecycle status and all existing holds remain authoritative: SBX-1
is a landed implementation but not activated, accepted, certified, or
real-provider-proven, and it does not unlock held SBX-2.

## Current-authority projection scope

`PLANNING_STATE.json` contains the machine-readable
`sssf.planning-authority-projection.v1` projection observed from the fetched
`refs/remotes/origin/planning/future-sssf` ref. It projects all current FUT-001
through FUT-016 states, with FUT-014 as `SEQUENCED`, FUT-015 as `SEQUENCED`,
and FUT-016 as `CANDIDATE`; the complete governed LAUNCH-1, SBX-0, SBX-1,
SBX-2, SBX-3, SBX-4, SBX-5, SBX-6, SBX-7, SBX-8, WAYFINDER-0 as `SEQUENCED`, WAYFINDER-1,
DSH-0A, DSH-0B, DSH-1, DSH-2, DSH-3, DSH-4, DSH-5, DSH-6, DSH-7, and DSH-8
roadmap identities, and BOUND-1 as `SEQUENCED`. None of the newly admitted
identities is `ACTIVE`. The BOUND-1 predecessor rule is derived from the immutable
authority bytes: it must complete and qualify before SBX-2 activation, and SBX-2
can leave `HELD` only after that qualification.

The projection is deliberately bounded. It answers only future-item state,
named lifecycle state, and the BOUND-1 predecessor order. It cannot answer
SBX-2 readiness or activation, implementation, landing, acceptance,
certification, or live enablement; every such query is CNO/non-PASS. The
validator observes the current authority ref/tree and rejects candidate-authored
stale-generation self-consistency, omitted FUT items, omitted or demoted
LAUNCH/SBX/Wayfinder/DSH identities, duplicate or conflicting authority
headings/states, and omitted BOUND-1 predecessor bytes.

The validator control refusing stale projection prose belongs in the g2 requalification because a passing validator over a false projection is the masked-applicability defect this repair series exists to remove.

## Known limitation and follow-on

`check_planning_foundation.py` currently accepts only the pre-fetched shared
tracking ref `refs/remotes/origin/planning/future-sssf` as its authority input.
A later bounded increment should add an explicit authority input argument—an
exact commit or an explicit `GIT_DIR`—so qualification never requires a lane or
CI job to write that shared tracking ref. This follow-on is not implemented by
this increment.

## Deterministic acceptance

Run:

```text
python3 docs/validation/check_planning_foundation.py
PYTHONPATH=.:adws pytest -q tests/test_planning_foundation.py
python3 -m pytest -q tests/test_planning_foundation.py::test_closure_gate_requires_nonempty_exact_test_universe
python3 -m pytest -q tests/test_planning_foundation.py::test_older_consistent_snapshot_cannot_replace_authoritative_generation
python3 -m pytest -q tests/test_planning_foundation.py::test_windows_symlink_privilege_cno_is_machine_readable_non_pass
python3 -m pytest -q tests/test_planning_foundation.py::test_unrelated_notimplementederror_is_not_automatic_cno
python3 -m pytest -q tests/test_planning_foundation.py::test_closure_gate_includes_unrelated_notimplementederror_regression
python3 -m pytest -q tests/test_planning_foundation.py::test_sbx2_state_is_observed_from_authority_not_candidate_expectation
python3 -m pytest -q tests/test_planning_foundation.py::test_missing_governed_identity_or_bound1_predecessor_is_nonpass
python3 -m pytest -q tests/test_planning_foundation.py::test_authority_projection_rejects_missing_duplicate_or_conflicting_governed_identities
python3 -m pytest -q tests/test_planning_foundation.py::test_closure_gate_includes_authority_omission_and_predecessor_regressions
```

The validator positively checks the canonical lifecycle, all legal edges,
terminal/re-entry rules, the exact authoritative planning source/generation,
FUT-001/FUT-003/SBX-2 current states, durable transition records, exact ACTIVE
implementation identity shape, the exact unique `active-not-proven` planned
increment set and its matching planning-authority binding, ADR inventory,
current SBX holds, ownership, and links. In-memory
watched-red defects cover stale ADR status, illegal/unknown/skipped edges,
missing sequencing, unbound/partial ACTIVE identity, ACTIVE authority escape,
duplicate ADR identity, roadmap regression, competing lifecycle owners, and
broken cross-references. It manufactures each defect without writing files.

The successor containment correction also rejects URL/URI/remote-reference
syntax before filesystem resolution. Focused ACTIVE and retained-PROVEN tests
prove local `https:/...` aliases cannot establish repository evidence, and the
canonical watched-red suite creates transient project-contained symlinks to
out-of-root files for the ACTIVE authoritative reference plus all four retained
PROVEN evidence categories. A lexical-only resolution/containment mutation
makes each named symlink control red when symlink creation is available. A host
that cannot create the transient links reports each exact symlink property as
canonical machine-readable `{"outcome":"CNO","status":"UNVERIFIED"}` with
nonzero exit 2 rather than treating an unexercised control as observed-good.
The closure owner derives selection and completion from pytest collection/report
events and keeps FAIL > CNO > PASS property precedence, including an unrelated
`NotImplementedError`, an unrelated observable filesystem `OSError`, and a
simultaneous contradiction plus CNO control. Only direct WinError 1314 evidence
establishes Windows privilege/environment CNO.

The authoritative `ACTIVE` planning state is not `PROVEN`; no passing local
control grants task creation, execution, landing, acceptance, certification,
PRE_CERTIFICATION exit, or live-enablement authority. Those gates remain
outside this candidate.

## Successor containment correction

This branch carries the eight commits of immutable predecessor PR #24 in their
original order on exact contribution target
`991d3a64f1b96a8b9637f97060d692af3518228f`, whose tree is
`7b88546cd1f63e8304325ee35be37893268ae0e0`, and then adds only the bounded
correction. It does not modify or merge PR #24 head
`05d3addf8c9120e0824400041fa7235410a7ec4b` / tree
`ec52ce459fd9e2f3c722ca66e377b88ee1c13a05`, or PR #23 head
`4d4c42377dfaa99ea4bf818322cf422bc8cb06f7` / tree
`22b312002f7bde05b98ea95b04a45d70b2ba6157`; their measured and review
records remain predecessor evidence, not evidence for this successor.

The bounded correction addresses only the assignment-distinct repository-
containment findings, the closure-owner non-vacuity contract, Windows symlink
CNO semantics, and exact authoritative planning-generation reconciliation.
Categorical remote-identity rejection remains before path conversion, and
non-vacuous ACTIVE/retained-PROVEN symlink containment controls remain. FUT-001/
DSH is `SEQUENCED`; FUT-003 is `ACTIVE`, not `PROVEN`; SBX-2 is `HELD`; and no
runtime, producer, consumer, provider, Docker, Wayfinder, DSH, SBX-2,
landing, acceptance, certification, or live-enable authority is added.

<!--
Rebase-equivalence retention: these exact lines were present at the validated
head and are retained as historical bytes only; the visible wording above is
current authority and supersedes these predecessor descriptions.
implementation identity shape, ADR inventory, current SBX holds, ownership,
and links. In-memory
Repair the planning/lifecycle foundation carried by stale SSSF PR #16 without
rewriting that immutable predecessor or treating its head as current. The new
successor is based on supplied current main, not on the predecessor's stale
base. Reconcile
This branch carries the five commits of immutable predecessor PR #23 in their
`7b88546cd1f63e8304325ee35be37893268ae0e0`. It does not modify, merge, or
transfer evidence from predecessor head
`22b312002f7bde05b98ea95b04a45d70b2ba6157`.
-->
