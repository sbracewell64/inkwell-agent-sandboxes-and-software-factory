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
| Host `just obs sessions` | Windows host lacks `sqlite3` | NOT PROVEN |
| Operator-owned canonical repository | `origin` resolves to `sbracewell64/inkwell-agent-sandboxes-and-software-factory` | PASS |
| Upstream retained as reference | `upstream/main` remains `92f1701...`; push URL disabled | PASS |
| Canonical accepted branch | local `main` tracks `origin/main` at proven B1 commit | PASS |
| Proven B0/B1 refs survived publication | remote branches/tags resolve to exact recorded commits | PASS |
| Sandbox clones canonical evolving source | current FILL still hard-codes Disler upstream | NOT PROVEN |
| Sandbox default source authority | FILL resolved operator-owned canonical `origin` automatically | PASS |
| Exact sandbox source pin | FILL selected `0ad16d939366ad0b6bb9c2bdb28eea7799a8e8df` and guest HEAD matched exactly | PASS |
| Durable sandbox provenance | run record retained `source_repo`, `source_sha`, and matching `commit_sha` | PASS |
| Independent SETUP provenance gate | Gate A verified guest origin, exact HEAD, and clean tree | PASS |
| B2-002 cleanup | runtime key revoked, VM destroyed, run record closed, exe.dev fleet empty | PASS |
| B2-002 closure documentation hygiene | final closure had one trailing-whitespace finding; runtime proof unaffected | CORRECTED BY B2-003 |

## Rule

A `NOT PROVEN` or `UNRESOLVED` row remains visible until a later increment supplies evidence. Documentation must not convert absence of proof into a pass.
