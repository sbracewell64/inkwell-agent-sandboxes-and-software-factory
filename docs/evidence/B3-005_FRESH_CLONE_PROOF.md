# B3-005 Fresh Windows Clone End-to-End Proof

**Commission:** `SOL-FM-SSSF-B3-005-001`
**Mode:** `PRE_CERTIFICATION`
**Proof candidate:** `efd84ab02fee4cb4c8e1e116616e039ba84a0546`
**Run ID:** `b3-005-proof-20260815-b30005`
**Disposition:** reversible proof complete; certification dimensions held

## Source identities

- Repository: `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`
- Base tag: `sssf-b3-004-closure-hygiene-correction`
- Base tag object: `0f9505b68b47b40751a172ceb58ee83d5fc78112`
- Base tag peeled commit: `04e5484a6190f033d25e1626b96a4cca93b7f755`
- Remote `main` before publication: `04e5484a6190f033d25e1626b96a4cca93b7f755`
- Commissioned branch: `increment/b3-005-fresh-windows-clone-proof`
- Proof candidate: `efd84ab02fee4cb4c8e1e116616e039ba84a0546`
- Proof clone: `E:\SSSF-B3-005-PROOF-20260815-154222`

The branch, base, remote `main`, annotated tag peel, branch absence, and PR absence were checked before first publication. Remote movement was checked again before later branch updates. No default-branch push or tag operation occurred.

## Fresh native environment and clone

The Windows-native environment method and exact observations are retained in:

- `B3-005_WINDOWS_NATIVE_EQUIVALENCE.md`
- `b3-005/bootstrap/process-creation.txt`
- `b3-005/bootstrap/native-process-environment.txt`
- `b3-005/bootstrap/persistent-environment-before.txt`
- `b3-005/bootstrap/persistent-environment-after.txt`
- `b3-005/bootstrap/stdout.txt`

Exact clone command:

```bat
git clone --single-branch --branch increment/b3-005-fresh-windows-clone-proof https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git E:\SSSF-B3-005-PROOF-20260815-154222
```

The clone selected exact HEAD `efd84ab02fee4cb4c8e1e116616e039ba84a0546`, the commissioned branch and canonical origin. Status and diff were clean.

Before bootstrap, the independently created native child PATH contained Git `cmd`, but neither Git `bin` nor Git `usr\bin`. `git` resolved through Git `cmd`; `ssh` resolved through Windows OpenSSH; `sh`, `cygpath`, and `zsh` were absent. Root `just` and `just local` succeeded.

After those controls, only the existing host provisioning-key entry was copied into ignored `.env`; its value was never emitted or retained. `bin\sssf-windows.cmd --sandbox` passed complete host doctor and composed sandbox doctor. Git Bash session paths then appeared and resolved as designed. Persistent HKCU/HKLM environment records remained byte-identical after excluding capture timestamps.

The method/evidence proposal was posted by FirstMate to control issue #3:

`https://github.com/sbracewell64/firstmate-sol-control/issues/3#issuecomment-5302981383`

Browser Sol had not ruled when this record was prepared. Windows-native equivalence therefore remains `CNO / HOLD`, not PASS.

## Bootstrap restart discipline

The first allocated clone, `E:\SSSF-B3-005-PROOF-20260815-154950`, stopped at bootstrap exit 54 because the new proof harness requested composed sandbox doctor before staging approved ignored configuration. The proof clone was not edited or continued. Evidence is retained in `b3-005/failed-bootstrap/`.

The harness was corrected only on the contribution branch in proof candidate `efd84ab02fee4cb4c8e1e116616e039ba84a0546`. The failed clone was discarded and a newly allocated proof clone restarted from the exact corrected candidate.

## Exactly one sandbox

The successful fresh clone created, filled, set up, and observed exactly one disposable exe.dev sandbox:

`b3-005-proof-20260815-b30005`

Complete output is retained in:

- `b3-005/lifecycle/stdout.txt`
- `b3-005/lifecycle/stderr.txt`
- `b3-005/lifecycle/process-creation.txt`
- `b3-005/lifecycle/native-process-environment.txt`

CREATE recorded the run before creating the VM, then minted one bounded `$50.00` runtime key. FILL selected the proof clone's canonical origin and exact committed HEAD. It injected only the disposable runtime key; no host auth home or provisioning key entered the guest.

FILL and independent guest inspection agreed on:

- origin: `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`
- source SHA: `efd84ab02fee4cb4c8e1e116616e039ba84a0546`
- commit SHA: `efd84ab02fee4cb4c8e1e116616e039ba84a0546`
- guest branch: `sbx/b3-005-proof-20260815-b30005`
- guest tracked status: clean

SETUP Gate A independently repeated origin, HEAD, and cleanliness checks and passed. Provisioning completed. OBSERVE started the application and observability service; the public app returned HTTP 200 and the owner-gated observability endpoint returned HTTP 307.

## Three-valued setup observation

The SETUP roster probe printed four `Insufficient credits` failures but subsequently printed Gate C/D/E PASS and declared the overall setup gate passed. This is the known pre-existing suspect gate behavior already retained in the baseline. The contradictory Gate C claim is classified `FAIL / UNRESOLVED`, never PASS. No credits were purchased or enabled to alter the result.

The required source-provenance, provisioning, service, and lifecycle observations remain independently evidenced. This proof does not use the contradictory roster assertion as acceptance evidence.

## B3-004 observability

On the Windows host, external `sqlite3` was absent. The Windows host doctor executed the B3-004 validator, and an explicit:

```bat
python docs\validation\check_obs_query.py --require-no-external-sqlite3
```

passed. This proves the commissioned Windows sqlite-free observability contract.

The first lifecycle harness revision additionally required external sqlite3 absence inside the Linux guest. The guest legitimately exposed `/bin/sqlite3`, so that over-scoped check failed at harness exit 70 after create/fill/setup/observe had completed. External sqlite3 absence is a Windows-host condition, not a Linux guest condition. The failure is retained in `b3-005/lifecycle/` and is not converted to PASS. The contribution-branch harness was corrected to run the cross-platform stdlib validator in the guest without imposing the Windows executable-absence condition. No source was edited in the proof clone, and no second sandbox was created.

## Ordered teardown and custody

Teardown ran explicitly through:

```bat
just sbx lifecycle teardown b3-005-proof-20260815-b30005
```

Retained output: `b3-005/teardown/stdout.txt`.

Observed order:

1. VM observed running;
2. spend recorded as `$0`;
3. artifacts copied to host custody;
4. harvest checked the run branch and found no new commits;
5. runtime key revoked;
6. VM destroyed;
7. runtime key file shredded;
8. run record closed;
9. authoritative key-list absence gate passed.

Artifact names, sizes, and SHA-256 values are retained in `b3-005/artifact-sha256-manifest.txt`. The runtime SQLite DB itself remains runtime evidence and is not committed. The exact closed record is `b3-005/closed-run-record.json`.

After teardown:

- runtime key absent from the authoritative OpenRouter key list: PASS;
- runtime key file absent: PASS;
- target VM absent: PASS;
- complete fleet result `{"vms":[]}`: PASS;
- run record `closed_at`: `2026-08-15T15:48:07Z`;
- guest runtime-key residue: absent with destroyed VM;
- host runtime-key residue: absent with shredded key file.

## Proof-clone source custody and disposal

The final proof-clone capture, `b3-005/final-proof-clone-state.txt`, recorded exact HEAD, branch, origin, clean tracked status, empty tracked diff, absent runtime key file, and ignored host config/run records. No transient compatibility edit occurred.

The disposable proof clone, including its ignored host configuration, was then removed. `b3-005/proof-clone-disposal.txt` records path absence. The redacted Windows evidence directory contains no credential value.

## Acceptance table

| Dimension | Result | Evidence |
|---|---|---|
| Exact base, branch, and proof SHA | PASS | immutable Git identities above |
| Fresh proof-clone creation and cleanliness | PASS | bootstrap output + final clone state |
| Worker-independent native process environment | CNO / HOLD | posted evidence; Browser Sol ruling pending |
| Pre-bootstrap Git Bash PATH absence | PASS | bootstrap native environment + negative controls |
| Pre-bootstrap accidental Git Bash executable absence | PASS | `where sh/cygpath/zsh` controls |
| Root `just` and `just local` before bootstrap | PASS | bootstrap output |
| Bootstrap session PATH reconstruction | PASS | bootstrap output |
| Persistent HKCU/HKLM environment unchanged | PASS | three before/after comparisons |
| Complete host doctor + composed sandbox doctor | PASS | bootstrap and lifecycle output |
| Windows B3-004 sqlite-free observability | PASS | explicit no-external-sqlite validator |
| Exactly one sandbox create/fill/setup/observe | PASS | run record + lifecycle output |
| Guest source repo/SHA/cleanliness | PASS | FILL, Gate A, independent inspection |
| Setup roster/model probe | FAIL / UNRESOLVED | contradictory insufficient-credit output |
| Linux guest external sqlite absence | NOT APPLICABLE; rejected over-scope | `/bin/sqlite3` observed |
| Observe app/owner-gated UI | PASS | HTTP 200 / 307 |
| Artifact custody before irreversible actions | PASS | teardown order + artifact manifest |
| Harvest before revocation/destruction | PASS | no guest commits; harvest ran before revoke |
| Runtime key revocation | PASS | authoritative list gate |
| VM absence | PASS | running pre-control, destroy, empty fleet post-control |
| Closed run record | PASS | exact retained JSON |
| Residual runtime-key material | PASS | key file shredded; key list absent; VM absent |
| No proof-clone patch-and-continue | PASS | stopped first clone; clean restarted clone |
| Proof clone disposed with ignored config | PASS | disposal record |
| Merge/main advancement/final B3 tag | HOLD / NOT PERFORMED | PRE_CERTIFICATION boundary |
| Unattended return-path certification | CNO / HOLD | control issue #2 remains outside this proof |

## Disposition

All independent reversible B3-005 PRE_CERTIFICATION gates are complete. The PR may be reviewed but must not merge or establish a final B3 freeze while the commissioned equivalence/certification holds remain unresolved.
