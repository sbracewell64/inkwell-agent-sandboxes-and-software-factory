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
| B3-004 corrected candidate hygiene | amended candidate `9d160bb` passed `git show --check` | PASS |
| B3-004 exact candidate publication | local and remote branch both `9d160bb21ae15283acaca5fa98aa56587c3db414` | PASS |
| B3 portability complete | fresh clone/bootstrap/doctor/mount/teardown without manual intervention | NOT PROVEN |

## Rule

A `NOT PROVEN`, `UNRESOLVED`, `ABSENT`, or observational row remains visible until a later increment supplies evidence or deliberately changes the contract. Documentation must not convert absence of proof into a pass.