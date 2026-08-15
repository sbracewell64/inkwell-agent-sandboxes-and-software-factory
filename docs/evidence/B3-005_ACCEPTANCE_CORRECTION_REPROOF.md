# B3-005 Setup Acceptance Correction and Fresh Reproof

**Commission:** `SOL-FM-SSSF-B3-005-001`
**Mode:** `PRE_CERTIFICATION`
**Acceptance repair candidate:** `7aedae1c3e8e7d3683ffea11f60d54458efb3cc6`
**Fresh proof clone:** `E:\SSSF-B3-005-REPROOF-20260815-160826`
**Reproof run:** `b3-005-reproof-20260815-b30006`
**Disposition:** correction proved fail-closed; end-to-end result `CNO / HOLD`

## Causal diagnosis

The first proof printed four roster failures caused by insufficient credits and then printed Gate C/D/E PASS. The host-side setup recipe treated the SSH process result as the entire acceptance result. It did not require typed per-dimension evidence and did not reconcile remote diagnostics before printing downstream PASS lines.

That made transport success capable of overriding observed-bad or unavailable subgate evidence. The source-level acceptance contract was defective even though the first sandbox was later cleaned correctly.

The first proof at `efd84ab02fee4cb4c8e1e116616e039ba84a0546` is therefore rejected as final B3-005 evidence. Its source, lifecycle, and teardown records remain diagnostic history only.

## Bounded correction

Candidate `7aedae1c3e8e7d3683ffea11f60d54458efb3cc6` changes acceptance, not credentials, roster, provider, spend, or lifecycle order.

The correction adds:

- `tools/setup_cde_acceptance.py` — deterministic three-valued reconciliation;
- `docs/validation/check_setup_cde_acceptance.py` — regression fixtures;
- complete remote output capture and explicit remote exit capture in SETUP;
- a required `SSSF_CDE_RESULT` marker with `roster`, `cost`, and `credit` states;
- explicit `PASS`, `FAIL`, and `CNO` state handling;
- host refusal to print C/D/E PASS unless one valid marker says all PASS, remote exit is zero, and diagnostics do not contradict it;
- CNO/HOLD when the marker or other required evidence is absent/unavailable;
- composition of the new validator into Windows host doctor.

Regression fixtures prove:

- clean all-PASS evidence passes;
- failure diagnostics plus an all-PASS marker fail;
- legacy failure output without a marker is CNO/HOLD;
- unavailable, malformed, duplicate, and transport-contradictory evidence cannot pass;
- explicit FAIL cannot pass.

No deterministic gate was weakened. The corrected gate is stricter.

## Fresh-clone restart

The repaired candidate was pushed before proof. A newly allocated proof clone was created with:

```bat
git clone --single-branch --branch increment/b3-005-fresh-windows-clone-proof https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git E:\SSSF-B3-005-REPROOF-20260815-160826
```

Exact HEAD:

`7aedae1c3e8e7d3683ffea11f60d54458efb3cc6`

The branch tracked the commissioned remote at `+0/-0`; tracked status and diff were clean.

The independently constructed Windows-native child again began without Git `bin`, Git `usr\bin`, `sh`, `cygpath`, or `zsh`. Root `just` and `just local` passed before bootstrap. `bin\sssf-windows.cmd --sandbox` passed and reported:

`setup C/D/E acceptance — B3-005 validator PASS`

B3-002, B3-004, host doctor, and composed sandbox doctor also passed. Persistent HKCU/HKLM environment captures were unchanged.

Evidence:

`docs/evidence/b3-005/reproof/bootstrap/`

Browser Sol later ruled `WINDOWS_NATIVE_EQUIVALENCE = PASS` for environment freshness only at exact reviewed head `63bc5792e0db4d6fb152a947648e161ae47f1b14`; provenance is recorded in `B3-005_BROWSER_SOL_RULING.md`. The PASS does not extend to GUI/Explorer/session properties, and the provenance-only successor requires applicability confirmation or exact-successor review before stronger use.

## Fresh live lifecycle reproof

One newly named reproof sandbox was created:

`b3-005-reproof-20260815-b30006`

CREATE, FILL, provisioning, SETUP Gate A, and SETUP Gate B were lawfully observed.

FILL and Gate A agreed on:

- canonical repository;
- exact source/commit SHA `7aedae1c3e8e7d3683ffea11f60d54458efb3cc6`;
- clean guest tracked tree.

No host authentication home or provisioning credential entered the guest. Only the existing lifecycle's disposable bounded runtime key was injected. No paid or new credential path was purchased or enabled.

## Corrected unavailable-evidence result

The same four roster calls reported:

```text
CNO ... model evidence unavailable (insufficient credits)
```

The remote did not emit the required final typed marker, so cost/credit completion evidence could not be observed. The deterministic host reconciler reported:

```text
setup C/D/E acceptance: CNO/HOLD
reason: expected exactly one result marker, observed 0
```

SETUP then stopped with:

```text
[setup] FAILED: assertions C/D/E — CNO/HOLD; required remote evidence unavailable
```

Critically, no Gate C PASS, Gate D PASS, Gate E PASS, overall setup PASS, or observe PASS followed those unavailable results.

This is the required live proof that unavailable roster evidence cannot yield downstream PASS.

Because SETUP correctly refused acceptance, OBSERVE was not lawfully reachable and was not run. Its result is `CNO / HOLD`, never PASS. End-to-end B3 completion is likewise `CNO / HOLD`.

Complete lifecycle output:

- `docs/evidence/b3-005/reproof/lifecycle/stdout.txt`
- `docs/evidence/b3-005/reproof/lifecycle/stderr.txt`
- `docs/evidence/b3-005/reproof/lifecycle/exit-code.txt`

## Teardown and custody

After the recorded SETUP stop, teardown ran only through the existing lifecycle:

```bat
just sbx lifecycle teardown b3-005-reproof-20260815-b30006
```

Observed order:

1. target VM observed running;
2. spend recorded as `$0`;
3. artifacts copied to host custody;
4. harvest ran and found no guest commits;
5. runtime key revoked;
6. VM destroyed;
7. runtime key file shredded;
8. run record closed;
9. authoritative key-list absence gate passed.

Post-controls:

- key absent from authoritative list: PASS;
- runtime key file absent: PASS;
- target VM absent: PASS;
- complete fleet `{"vms":[]}`: PASS;
- closed record timestamp: `2026-08-15T16:10:30Z`;
- tracked proof-clone diff: empty;
- proof clone and ignored host config disposed: PASS.

Evidence:

- `docs/evidence/b3-005/reproof/teardown/`
- `docs/evidence/b3-005/reproof/closed-run-record.json`
- `docs/evidence/b3-005/reproof/artifact-sha256-manifest.txt`
- `docs/evidence/b3-005/reproof/final-proof-clone-state.txt`
- `docs/evidence/b3-005/reproof/proof-clone-disposal.txt`
- `docs/evidence/b3-005/reproof/validation.txt`

## Reproof acceptance table

| Dimension | Result |
|---|---|
| Exact repaired candidate and fresh clone | PASS |
| Pre-bootstrap native environment controls | PASS |
| Root `just` / `just local` before bootstrap | PASS |
| Bootstrap + complete host/composed doctor | PASS |
| B3-005 deterministic acceptance validator in host doctor | PASS |
| Persistent HKCU/HKLM environment unchanged | PASS |
| Windows B3-004 sqlite-free observability | PASS |
| Fresh reproof sandbox create/fill | PASS |
| Guest exact source and cleanliness | PASS |
| SETUP provisioning and Gates A/B | PASS |
| Roster availability | CNO / HOLD — insufficient credits |
| Typed final C/D/E marker | CNO / HOLD — not emitted |
| Downstream PASS suppression | PASS — no C/D/E/setup PASS emitted |
| OBSERVE | CNO / HOLD — correctly unreachable after SETUP refusal |
| End-to-end B3 portability | CNO / HOLD — not proven |
| Artifact/harvest ordering | PASS |
| Key revocation / file absence | PASS |
| VM absence / closed run record | PASS |
| Proof clone clean/no patch-and-continue | PASS |
| Proof clone/config disposal | PASS |
| Windows-native equivalence | PASS — environment freshness only; Browser Sol ruling 5303198972 and PR review 4944257620 bind exact head `63bc5792e0db4d6fb152a947648e161ae47f1b14` |
| Merge/main/final B3 freeze | HOLD / NOT PERFORMED |

## Result

The acceptance defect is repaired and proved fail-closed from a newly allocated fresh Windows clone and sandbox. Browser Sol passed only the independent Windows environment-freshness equivalence dimension. Credits remained unavailable, so `OVERALL_B3_005` lawfully remains `CNO / HOLD`. CI remains CNO, and this PR remains non-mergeable/non-freezable under PRE_CERTIFICATION.
