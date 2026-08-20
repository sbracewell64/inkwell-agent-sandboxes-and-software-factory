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
| HD-01 single strict LF authority | default validator and Windows doctor invoke the same strict owner; exact supported invocation is `python docs/validation/check_line_endings.py --require-worktree-lf` | PASS |
| HD-01 watched-red controls | CRLF and wrong attributes produce observed-bad; missing files produce could-not-observe; none prints PASS | PASS |
| HD-01 index-preserving remediation | explicit `checkout-index` fixture retained the same index tree and restored `i/lf w/lf` | PASS |
| HD-01 hostile-autocrlf fresh clone | disposable clone created with `core.autocrlf=true`; every representative file was `i/lf w/lf attr/text=auto eol=lf` | PASS |
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
| HD-03 zero required gate observations | focused `GateReport` and zero-discovery controls | COULD_NOT_OBSERVE; CANNOT ADVANCE |
| HD-03 explicit failed gate check | focused negative fixture | FAIL |
| HD-03 qualifying nonempty gate evidence | exact nonempty artifact fixture across existence/content/claim gates | PASS |
| HD-03 malformed/legacy gate outcome | parser, adapter, migration, console, and trace controls | CNO/REFUSED; NEVER BOOLEAN PASS |
| B3 portability complete | fresh clone/bootstrap/doctor/mount/teardown without manual intervention | NOT PROVEN |
| B4-001 offline check discovery | run `31907345967` at `29819d98ea2b046bc432bde2a3e9cd42be7640a4`: each OS discovered and executed 6/6 checks | PASS |
| B4-001 non-vacuous projection | each job retained 6 observed-good, 0 observed-bad, and 0 could-not-observe results | PASS |
| B4-001 watched-red controls | empty checks/matrix, validator failure, missing tool, cancellation/timeout, workflow path/trigger drift, and exact-head ref drift each observed red | PASS |
| B4-001 Linux GitHub execution | run `31907345967`, `ubuntu-24.04`, exact reviewed head: 6/6 observed-good; Inkwell 30 pass, 0 fail, 230 assertions | PASS |
| B4-001 Windows GitHub execution | run `31907345967`, `windows-2022`, exact reviewed head: 6/6 observed-good; Inkwell 30 pass, 0 fail, 230 assertions | PASS |
| B4-001 closure successor execution | provenance-only successor must complete the same nonempty Linux/Windows checks on its own exact head | CNO UNTIL OBSERVED |
| B4-001 default-branch push execution | accepted successor must trigger the same nonempty Linux/Windows checks after merge | CNO UNTIL OBSERVED |
| B4-002 strict launch surface | exact provider/model, effort, tools, JSON print, no session/resources/approval/fallback, closed stdin, allowlisted env | PASS — LOCAL FIXTURE |
| B4-002 credential environment refusal | sensitive names and credential-style names outside the fragment vocabulary are refused before launch; the fixed process-mechanics allowlist is the complete boundary | PASS — WATCHED RED + LOCAL FIXTURE |
| B4-002 shell-zero structured error precedence | deterministic children exit zero with provider error; missing, incomplete, and drifting target metadata remains secondary typed evidence while provider error remains primary | LOCAL FIXTURE REQUIRED; EXACT-CANDIDATE REVIEW CNO |
| B4-002 process bounds and cleanup | timeout, cancellation, ignored TERM, output overflow, reap, Unix group and escaped-descendant absence verification | PASS — LOCAL LINUX FIXTURE |
| B4-002 shipped extension-bearing production path | all ten shipped planner/scout agents across five rosters declare nonempty `harness_engineering`; each drives the real `agent_pi` launch path and its extensions are forwarded as `-e`, not rejected | PASS — WATCHED RED + LOCAL FIXTURE |
| B4-002 production integration boundary | `agent_pi.py`, `agents.py`, `data_types.py`, `console.py`, `gates.py`, `permissions.py` are byte-identical to canonical `main` `a984f6cf`, so the shipped ADW path is unchanged by this increment | PASS |
| B4-002 pre-launch cancellation | cancellation already set at `supervise()` entry is observed before the attempt claim: zero budget use, no custodian or provider identity, no spawn/exit/event callback; cancellation during pre-launch setup fails closed before the custodian while keeping its already-claimed attempt | PASS — WATCHED RED + LOCAL LINUX FIXTURE |
| B4-002 stdin parent-tail regression | inherited-stdin control suppresses marker; owned supervisor preserves required typed parent-tail marker | PASS — WATCHED RED + LOCAL FIXTURE |
| B4-002 protocol and attempt accounting | malformed/missing/duplicate terminal events and hidden retry are typed and charged against common budget | PASS — LOCAL FIXTURE |
| B4-002 immutable resolved-target enforcement | every assistant `message_end` retains event/message identity; incomplete or drifting tuples remain terminal despite later matching output | LOCAL FIXTURE REQUIRED; EXACT-CANDIDATE REVIEW CNO |
| B4-002 Windows descendant containment | Job Object path is not implemented; launch returns typed CNO before spawn | CNO — HONEST REFUSAL |
| B4-002 reviewed Linux PR-head projection | run `31911734134` completed the nonempty Linux checks on exact reviewed head `2291725cf0782b40ce01a17d29b6415a51b130de` | PASS — RULING `5304605032` |
| B4-002 reviewed Windows PR-head projection | run `31911734134` completed the nonempty Windows static/parser/refusal checks on the same exact reviewed head | PASS — FAIL-CLOSED REFUSAL PROJECTION |
| WINDOWS_PROVIDER_EXECUTION | green Windows CI proves refusal, not provider launch, Job Object custody, or descendant cleanup | CNO/REFUSED |
| B4-002 corrected candidate execution | run `31917258787` on corrected head `5447b56eac128c4dad80d751fbfa3c0144ee7cf7` returned `total_count: 2`; `deterministic (ubuntu-24.04)` and `deterministic (windows-2022)` both completed with conclusion `success`; this closing documentation change advances the head again, so fresh independent review and its own nonempty Linux/Windows checks must bind to the final exact head; a check observed on one head is never evidence for another; ruling `5304605032` is provenance only | CHECKS PASS AT `5447b56e`; FINAL-HEAD REVIEW AND CHECKS CNO |
| HD-02 ADW surface inventory | validator checked 12 installed, 12 template, and 1 disposable generated ADW; zero surfaces are CNO | PASS |
| HD-02 static contracts | imported attributes, concrete output types, dependencies, prompt Report fields, and bounded-prefix final-return finish contracts reconciled | PASS |
| HD-02 generated import | disposable generated script imported with declared dependencies and no provider call | PASS |
| HD-02 watched-red controls | missing export/rich/finish, Boolean and non-Boolean loop/match/nested finish violations, reachable-break duplication, stale `run.succeeded`, and prompt mismatch each made the validator red | PASS |
| HD-08 canonical manifest bytes | positive fixture round-trips through the sole serializer byte-for-byte | PASS |
| HD-08 offline checked inventory | positive fixture verifies every artifact hash/type and bound SQLite ADW row from frozen bytes without network/provider access | PASS |
| HD-08 nonvacuous qualification | empty directory/database/manifest/inventory, diagnostic-only evidence, and absent phase/dimension controls cannot pass | PASS |
| HD-08 identity and integrity refusal | wrong identities, failed unrelated item, tamper, duplicate/reorder, descriptor-relative traversal/symlink races, final/root symlinks, identity change, unsupported host, and malformed schema controls observed red/CNO as specified | PASS |
| HD-08 intermediate-component stat-to-open race | component swapped for an outside-root symlink between its no-follow stat and its descriptor-relative open; shipped implementation refused non-PASS with empty checked inventory and no outside-root bytes read, calibrated watched-red against a content-addressed defective variant with both intermediate protections removed | PASS |
| HD-08 runtime acceptance integration | intentionally deferred to HD-09 | NOT PROVEN |
| LAUNCH-1 tracked front-door contract | `bin/sssf-firstmate.cmd` validates canonical root/origin, Bash/Git/grep dependencies, live HEAD and honest branch state, FirstMate launcher/admission/session-start path, and non-secret identity; no orchestration surface | PASS — LOCAL STATIC/BEHAVIORAL |
| LAUNCH-1 caller-cwd independence | actual CMD/WSL `--print-menu` from `C:\\Windows` and `C:\\Users\\Public` reported `root=E:\\SSSF` and `handoff=firstmate` | PASS — HOST OBSERVED |
| LAUNCH-1 named-lab FirstMate handoff | guarded non-default `fm-lab-*` session created labeled `firstmate`; pane agent was Claude and returned idle; default-session tripwire held through teardown | PASS — GUARDED HOST OBSERVED |
| LAUNCH-1 authorized shortcut | `C:\\Users\\Public\\Desktop\\SSSF FirstMate.lnk` targets tracked `E:\\SSSF\\bin\\sssf-firstmate.cmd`, no arguments, working directory `E:\\SSSF` | PASS — HOST INSPECTED |
| LAUNCH-1 canonical post-merge installation launch | new tracked file is not present in the pre-merge canonical checkout used for the host observation | CNO — HONEST LIMIT |

## Rule

A `NOT PROVEN`, `UNRESOLVED`, `ABSENT`, or observational row remains visible until a later increment supplies evidence or deliberately changes the contract. Documentation must not convert absence of proof into a pass.
