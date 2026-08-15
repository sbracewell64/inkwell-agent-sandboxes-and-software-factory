# Baseline Proof Matrix

| Claim | Evidence | Result |
|---|---|---|
| Local repo is a valid Git checkout | `git status` on canonical checkout | PASS |
| Host toolchain can invoke SSSF | Git, Bun, uv, just, Bash/cygpath verified | PASS |
| Host preflight | Windows host doctor + sandbox doctor | PASS |
| Inkwell payload baseline | 30 tests, 0 failures | PASS |
| exe.dev control-plane access | SSH, VM create/list/delete exercised | PASS |
| Per-run key lifecycle | keys minted and revoked during lifecycle cleanup | PASS |
| Failed run remains recoverable | run records retained; teardown later succeeded | PASS |
| Windows create path | CR normalization allowed VM name/readiness to proceed | PASS |
| Windows teardown path | portable `mktemp` template allowed teardown to complete | PASS |
| Full mount path | `baseline-proof-20260813-d38790` reached mounted state | PASS |
| Guest provisioning | Bun/just/uv/Pi/Claude/trace DB/visualizer provisioned | PASS |
| App public proxy | public :4501 endpoint returned HTTP 200 | PASS |
| Observability service | :4600 started and owner-gated | PASS |
| Paid stock roster inference | insufficient credits | NOT PROVEN |
| Free planner: Nemotron Ultra | declared artifacts but did not create them | REJECTED BY GATE |
| Planner artifact gate | missing artifact claim rejected | PASS |
| Free planner: North Mini Code | artifacts created and non-empty | PASS |
| Planner repo-write boundary | unauthorized app edit rolled back | PASS |
| Builder typed-output repair | malformed JSON retried in same session | PASS |
| Deterministic test phase | Inkwell suite passed | PASS |
| Commit gate | commit created after tests passed | PASS |
| Public HTML reflects committed change | public curl contained `Baseline proof` | PASS |
| Visual marker visibly rendered | not observed in browser | UNRESOLVED |
| Operator-owned canonical repository | `origin` resolves to `sbracewell64/inkwell-agent-sandboxes-and-software-factory` | PASS |
| Upstream retained as reference | upstream retained; push disabled | PASS |
| Canonical accepted branch | local `main` tracks canonical `origin/main` | PASS |
| Sandbox default source authority | FILL resolves operator-owned canonical `origin` automatically | PASS |
| Exact sandbox source pin | guest HEAD matched recorded source SHA exactly | PASS |
| Durable sandbox provenance | run record retains `source_repo`, `source_sha`, and `commit_sha` | PASS |
| Independent SETUP provenance gate | Gate A verifies guest origin, exact HEAD, and clean tree | PASS |
| B2-002 cleanup | runtime key revoked, VM destroyed, run record closed, fleet empty | PASS |
| B2-002 closure documentation hygiene | corrected without moving immutable B2-002 tag | CORRECTED BY B2-003 |
| Repository-owned line-ending policy | `.gitattributes` defines `* text=auto eol=lf` | PASS |
| Line-ending renormalization safety | renormalization produced no unrelated tracked-file changes | PASS |
| Fresh Windows LF checkout | B3-002 candidate cloned with `core.autocrlf=true`; representative files were `i/lf w/lf` | PASS |
| B3-002 strict validator | `check_line_endings.py --require-worktree-lf` passed | PASS |
| B3-002 first candidate hygiene | semantic proof passed but candidate record hygiene failed | CORRECTED BEFORE ACCEPTANCE |
| B3-002 corrected candidate hygiene | corrected candidate passed staged and commit whitespace gates | PASS |
| Windows root `just` without zsh | fresh CMD with no zsh successfully listed root namespaces | PASS |
| Windows `just local` without zsh | fresh CMD listed `cc`, `default`, and `pi` | PASS |
| Windows Git Bash bootstrap | fresh CMD began without `sh`; bootstrap selected Git Bash | PASS |
| Windows cygpath bootstrap | fresh CMD began without `cygpath`; bootstrap selected Git `usr\bin\cygpath` | PASS |
| Windows SSH bootstrap | pre-bootstrap Windows OpenSSH; post-bootstrap Git OpenSSH selected first | PASS |
| Windows PATH uniqueness | bootstrap reduced session PATH to unique entries | PASS |
| Windows Git PATH multiplicity | post-bootstrap Git `bin` count 1 and Git `usr\bin` count 1 | PASS |
| Windows bootstrap idempotence | second bootstrap produced byte-identical PATH | PASS |
| Windows persistent PATH boundary | HKCU and HKLM PATH remained unchanged | PASS |
| Windows Python compatibility | `python` 3.11.9 and `python3` 3.13.5 passed host-doctor floor | PASS |
| Windows just compatibility | just 1.58.0 passed >=1.56 requirement | PASS |
| exe.dev effective SSH policy | dedicated identity, `IdentitiesOnly yes`, `accept-new` | PASS |
| Dynamic sandbox SSH wildcard | same effective policy applies to synthetic `*.exe.xyz` host | PASS |
| B3-003 line-ending regression | B3-002 validator passed after bootstrap/front-door changes | PASS |
| B3-003 sandbox composition | `bin\sssf-windows.cmd --sandbox` composed and passed `sbx doctor` | PASS |
| B3-003 exact candidate | local and remote branch both `d5c53e871b32902ee76cd082a944afa4cdfc218d` | PASS |
| B3-003 fresh CMD reconstruction | persistent Windows state lacked Git Bash paths; committed bootstrap reconstructed complete required session | PASS |
| External Windows sqlite3 | `where sqlite3` reports no executable | ABSENT |
| B3-004 stdlib SQLite helper | `tools/obs_query.py` serves trace reads through Python standard-library sqlite3 | PASS |
| B3-004 sessions query | deterministic fixture through direct helper and real `just obs sessions` path | PASS |
| B3-004 phases query | deterministic fixture through direct helper and real `just obs phases` path | PASS |
| B3-004 tail query | deterministic fixture through direct helper and real `just obs tail` path | PASS |
| B3-004 procs query | deterministic fixture through direct helper and real `just obs procs` path | PASS |
| B3-004 live PID query | deterministic fixture returned only believed-live processes in kill order | PASS |
| B3-004 ADW-ID parameterization | injection-shaped ADW ID returned no unrelated rows | PASS |
| B3-004 missing DB safety | read-only query failed explicitly and did not create `sssf.db` | PASS |
| B3-004 external sqlite3 independence | full validator passed with `--require-no-external-sqlite3` | PASS |
| Windows host observability without sqlite3 | B3-004 deterministic fixture and Windows host-doctor contract passed | PASS |
| B3-004 host-doctor integration | Windows doctor reported `observability query contract — B3-004 validator PASS` | PASS |
| B3-004 corrected implementation-candidate hygiene | amended implementation candidate `9d160bb` passed `git show --check` | PASS |
| B3-004 exact implementation-candidate publication | local and remote candidate branch both `9d160bb21ae15283acaca5fa98aa56587c3db414` before documentation closure | PASS |
| B3-004 first published closure hygiene | closure `15bbea9` contains three trailing-whitespace violations despite failed pre-commit hygiene gates | FAILED; CORRECTED BY B3-004-H1 |
| B3-004 original closure tag immutability | `sssf-b3-004-sqlite-free-observability` remains fixed at `15bbea9bbf94d4b1491da47d9032707af77c2b04` and was not moved | PASS |
| B3-004-H1 correction candidate hygiene | candidate `1b892ab084bc4785c6f31f8999b586534d9e477b` passed both staged `git diff --cached --check` and committed `git show --check` | PASS |
| B3-004-H1 correction isolation | only ledger, proof matrix, and B3-004 increment record differ from flawed closure `15bbea9` | PASS |
| B3-004-H1 clean closure correction | original B3-004 tag preserved; separate correction state establishes the clean base for subsequent B3 work | PASS |
| B3-005 exact proof source | fresh clone, guest, and closed run record agree on canonical repository and `efd84ab02fee4cb4c8e1e116616e039ba84a0546` | PASS |
| B3-005 fresh native environment equivalence | `CreateEnvironmentBlock(inherit=false)` method/evidence posted to control issue #3 | CNO / HOLD — BROWSER SOL RULING PENDING |
| B3-005 pre-bootstrap Git Bash absence | native PATH excluded Git `bin`/`usr\\bin`; `sh`, `cygpath`, and `zsh` did not resolve | PASS |
| B3-005 Windows root front doors | fresh native child ran root `just` and `just local` before bootstrap | PASS |
| B3-005 bootstrap reconstruction | repository bootstrap introduced required session paths and complete host + composed sandbox doctor passed | PASS |
| B3-005 persistent Windows environment boundary | HKCU/HKLM values were unchanged across bootstrap, lifecycle, and teardown child processes | PASS |
| B3-005 Windows sqlite-free observability | external sqlite3 absent; explicit B3-004 no-external validator passed | PASS |
| B3-005 exactly one sandbox | `b3-005-proof-20260815-b30005` completed create/fill/setup/observe | PASS |
| B3-005 guest provenance | FILL, SETUP Gate A, independent guest inspection, and run record agree on repo/SHA/cleanliness | PASS |
| B3-005 setup roster probe | four insufficient-credit failures were followed by contradictory Gate C/D/E PASS | FAIL / UNRESOLVED |
| B3-005 Linux guest sqlite absence | `/bin/sqlite3` exists; Windows-only executable-absence assertion was over-scoped to guest | NOT APPLICABLE; REJECTED OVER-SCOPE |
| B3-005 observe services | public app HTTP 200; owner-gated observability HTTP 307 | PASS |
| B3-005 teardown custody and order | spend, artifacts, harvest preceded revoke/destroy; artifact hash inventory retained | PASS |
| B3-005 runtime cleanup | key absent from authoritative list, key file shredded, fleet empty, run record closed | PASS |
| B3-005 proof clone source custody | first failed clone stopped/discarded; restarted clone had exact clean HEAD and no tracked diff | PASS |
| B3-005 disposable clone cleanup | successful proof clone and ignored host config removed after evidence capture | PASS |
| B3-005 merge/freeze authority | PRE_CERTIFICATION forbids merge, main advancement, and final B3 tag | HOLD / NOT PERFORMED |
| B3 portability complete | reversible proof prepared, but Windows-native equivalence and formal certification remain held | CNO / HOLD — NOT CERTIFIED |
| B4-001 offline check discovery | run `31907345967` at `29819d98ea2b046bc432bde2a3e9cd42be7640a4`: each OS discovered and executed 6/6 checks | PASS |
| B4-001 non-vacuous projection | each job retained 6 observed-good, 0 observed-bad, and 0 could-not-observe results | PASS |
| B4-001 watched-red controls | empty checks/matrix, validator failure, missing tool, cancellation/timeout, workflow path/trigger drift, and exact-head ref drift each observed red | PASS |
| B4-001 Linux GitHub execution | run `31907345967`, `ubuntu-24.04`, exact reviewed head: 6/6 observed-good; Inkwell 30 pass, 0 fail, 230 assertions | PASS |
| B4-001 Windows GitHub execution | run `31907345967`, `windows-2022`, exact reviewed head: 6/6 observed-good; Inkwell 30 pass, 0 fail, 230 assertions | PASS |
| B4-001 closure successor execution | provenance-only successor must complete the same nonempty Linux/Windows checks on its own exact head | CNO UNTIL OBSERVED |
| B4-001 default-branch push execution | accepted successor must trigger the same nonempty Linux/Windows checks after merge | CNO UNTIL OBSERVED |

## Rule

A `NOT PROVEN`, `UNRESOLVED`, `ABSENT`, or observational row remains visible until a later increment supplies evidence or deliberately changes the contract. Documentation must not convert absence of proof into a pass.