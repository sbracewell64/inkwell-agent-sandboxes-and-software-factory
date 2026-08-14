# Baseline Proof Matrix

| Claim | Evidence | Result |
|---|---|---|
| Local repo is a valid Git checkout | `git status` on `main`, clean before local compatibility edits | PASS |
| Host toolchain can invoke SSSF | `git`, Bun, uv, just, Bash/cygpath verified | PASS |
| Host preflight | `just sbx manage doctor` | PASS |
| Inkwell payload baseline | 30 tests, 0 failures | PASS |
| exe.dev control-plane access | `ssh exe.dev`, VM create/list/delete exercised | PASS |
| Per-run key lifecycle | keys minted and revoked during failed-run cleanup | PASS |
| Failed run remains recoverable | run records retained; teardown later succeeded | PASS |
| Windows create path | CRLF normalization allowed VM name/readiness to proceed | PASS WITH LOCAL PATCH |
| Windows teardown path | portable `mktemp` template allowed teardown to complete | PASS WITH LOCAL PATCH |
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
| Host `just obs sessions` | Windows host lacks external `sqlite3` | NOT PROVEN |
| Operator-owned canonical repository | `origin` resolves to `sbracewell64/inkwell-agent-sandboxes-and-software-factory` | PASS |
| Upstream retained as reference | `upstream/main` remains `92f1701...`; push URL disabled | PASS |
| Canonical accepted branch | local `main` tracks canonical `origin/main` | PASS |
| Proven B0/B1 refs survived publication | remote branches/tags resolve to exact recorded commits | PASS |
| Sandbox default source authority | FILL resolved operator-owned canonical `origin` automatically | PASS |
| Exact sandbox source pin | FILL selected `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df` and guest HEAD matched exactly | PASS |
| Durable sandbox provenance | run record retained `source_repo`, `source_sha`, and matching `commit_sha` | PASS |
| Independent SETUP provenance gate | Gate A verified guest origin, exact HEAD, and clean tree | PASS |
| B2-002 cleanup | runtime key revoked, VM destroyed, run record closed, exe.dev fleet empty | PASS |
| B2-002 closure documentation hygiene | final closure had one trailing-whitespace finding; runtime proof unaffected | CORRECTED BY B2-003 |
| Windows Git Bash shell | `sh` resolves from Git for Windows | PASS |
| Windows `cygpath` availability | `cygpath` resolves from `C:\Program Files\Git\usr\bin` | PASS |
| Windows required PATH reachability | Git `bin`, Git `usr\bin`, `.local\bin`, and `.bun\bin` are reachable | PASS |
| Windows PATH reproducibility | Git paths are duplicated and currently depend on manually assembled environment state | NOT PROVEN |
| Repository-owned line-ending policy | `.gitattributes` defines `* text=auto eol=lf` | PASS |
| Line-ending renormalization safety | `git add --renormalize .` produced no modifications to existing tracked files | PASS |
| Fresh Windows LF checkout | corrected candidate `090fbff` cloned with `core.autocrlf=true`; representative text files were `i/lf w/lf` | PASS |
| B3-002 strict validator | `check_line_endings.py --require-worktree-lf` passed in fresh checkout | PASS |
| B3-002 first candidate hygiene | first candidate passed semantic proof but failed staged whitespace hygiene and had malformed Markdown | CORRECTED BEFORE ACCEPTANCE |
| B3-002 corrected candidate hygiene | corrected candidate passed `git diff --cached --check` and `git show --check` | PASS |
| exe.dev effective SSH policy | dedicated identity, `IdentitiesOnly yes`, and `StrictHostKeyChecking accept-new` apply to `exe.dev` | PASS |
| Dynamic sandbox SSH wildcard | same effective SSH policy applies to synthetic `*.exe.xyz` hostname | PASS |
| Windows SSH implementation selection | Git OpenSSH currently wins PATH precedence over Windows OpenSSH | OBSERVED |
| Windows Python selection | bare `python` resolves to Python 3.11.9 while multiple Python versions are installed | OBSERVED |
| External Windows sqlite3 | `where sqlite3` found no executable | ABSENT |
| Windows sandbox doctor after B2 | all six existing doctor checks passed | PASS |
| B3-001 audit isolation | only `docs/increments/B3-001_WINDOWS_PORTABILITY_BASELINE.md` changed during evidence collection | PASS |
| B3 portability complete | fresh clone/bootstrap/doctor/mount/teardown without manual compatibility intervention | NOT PROVEN |

## Rule

A `NOT PROVEN`, `UNRESOLVED`, `ABSENT`, or observational row remains visible until a later increment supplies evidence or deliberately changes the contract. Documentation must not convert absence of proof into a pass.