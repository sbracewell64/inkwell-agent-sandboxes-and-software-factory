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

## Rule

A `NOT PROVEN` or `UNRESOLVED` row remains visible until a later increment supplies evidence. Documentation must not convert absence of proof into a pass.
