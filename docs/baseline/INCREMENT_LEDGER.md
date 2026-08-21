# Increment Ledger

This ledger is append-only in intent. Do not rewrite history to make later results look cleaner.

| Increment | Status | Scope | Acceptance evidence |
|---|---|---|---|
| B0-001 | PASS | Clone and host-tool installation | Git/Bun/uv/just verified |
| B0-002 | PASS | OpenRouter + exe.dev credentials | doctor 6/6 |
| B0-003 | PASS | Inkwell baseline | 30/30 tests |
| B0-004 | PASS | Windows VM-name compatibility | clean VM name + SSH readiness |
| B0-005 | PASS | Windows teardown compatibility | two failed VMs destroyed, keys revoked |
| B0-006 | PASS | Full sandbox mount | `baseline-proof-20260813-d38790` mounted |
| B0-007 | REJECTED | Free Nemotron planner proof | artifact gates correctly failed |
| B0-008 | PASS | Free North Mini Code end-to-end ADW | ADW `5573998b`, 5/5, commit `042dfb9` |
| B0-009 | PASS | Archive/freeze baseline | `sssf-local-b0` + `sssf-proof-b0` created |
| B1-001 | PASS | Agent documentation discovery | bootstrap validator PASS; frozen B0 tags unchanged |
| B2-001 | PASS | Canonical repository ownership | validator PASS; origin canonical; upstream reference-only; B0/B1 refs preserved |
| B2-002 | PASS | Sandbox source provenance contract | live sandbox proved canonical repo + exact SHA + independent SETUP gate + teardown |
| B2-003 | PASS | Proof record hygiene | B2-002 closure evidence corrected; immutable B2-002 tag preserved |
| B2-004 | PASS | B2-003 ledger closure | published ledger reconciled with proven B2-003 state without moving immutable tags |
| B3-001 | PASS | Windows host portability baseline | host toolchain, PATH, line endings, SSH, sqlite3 gap, doctor, and follow-up increments audited |
| B3-002 | PASS | Repository line-ending contract | `* text=auto eol=lf`; corrected candidate `090fbff`; fresh Windows checkout passed with `core.autocrlf=true` |
| B3-003 | PASS | Windows bootstrap and host doctor | candidate `d5c53e8`; fresh CMD reconstructed deterministic PATH, Git Bash/SSH, front doors, and sandbox doctor without zsh or persistent PATH mutation |
| B3-004 | PASS | SQLite-free Windows host observability | implementation candidate `9d160bb` passed runtime/validator proof without external sqlite3; first published closure `15bbea9` later found to contain three trailing-whitespace violations |
| B3-004-H1 | PASS | Post-freeze B3-004 closure hygiene correction | candidate `1b892ab` passed staged and committed whitespace gates; original B3-004 tag preserved; clean correction state frozen separately |
| B4-001 | PASS | Non-vacuous deterministic GitHub CI bootstrap | run `31907345967` on reviewed head `29819d98ea2b046bc432bde2a3e9cd42be7640a4`: Ubuntu and Windows each discovered/executed 6/6 observed-good checks and passed Inkwell 30/30 with 230 assertions; closure successor and later `main` push require fresh checks |
| B4-002 | CORRECTED CANDIDATE — CNO | Provider-neutral subprocess supervisor + strict Pi JSON/print adapter | Run `31917258787` on corrected head `5447b56eac128c4dad80d751fbfa3c0144ee7cf7` had `total_count: 2`: `deterministic (ubuntu-24.04)` and `deterministic (windows-2022)` both completed with conclusion `success`; this closing documentation change advances the head again, so landing requires a fresh independent review and its own nonempty Linux/Windows checks bound to the final exact head; a check observed on one head is never evidence for another; Windows provider execution remains CNO/refused |
| HD-01 | PASS | One authoritative strict LF working-tree contract | default + doctor strict owner; CRLF/missing/wrong-attribute watched-red controls; hostile-`core.autocrlf=true` fresh clone remained `i/lf w/lf` |
| HD-02 | PASS | Static synchronization for installed/template/generated ADWs | nonempty static inventory, generated import-only smoke, and sixteen watched-red mutations passed without provider execution |
| HD-03 | PASS | Nonvacuous three-valued gate outcomes | 15 focused controls prove PASS/FAIL/CNO, fail-closed migration, trace provenance, and non-green CNO rendering |
| HD-08 | PASS | Offline nonempty run-bound evidence manifest core; no runtime acceptance integration | canonical positive fixture and watched-red identity/empty/diagnostic/tamper/duplicate/path/schema controls |
| LAUNCH-1 | CORRECTED CANDIDATE — CNO | Tracked Windows `E:\\SSSF` front door into the existing FirstMate primary/supervision path | `tests/test_windows_front_door.py`; named disposable Herdr-lab launch; public shortcut target recorded; post-merge launch from the installed canonical checkout remains CNO until observed |
| SBX-0 | PUBLISHED HANDOFF — CNO FOR EXIT/PROMOTIONS | Exact source-generation/content-digest semantics inventory and one-compatible-owner-per-fact SBX-1 handoff; no activation, acceptance, provider, Windows, review, landing, or SBX-2 claim | `docs/reference/SBX-0_SEMANTICS_INVENTORY.json`; source SHA `2d16bee3db4c46062b460dfbd6752339e85228a3b6f2c5002313a4f06dc663b3`; `python3 docs/validation/check_sbx0_inventory.py`; watched-red stale-generation/digest/duplicate-or-incompatible-authority/drop/CNO controls |
| SBX-1 | LANDED IMPLEMENTATION — provider-free fake controls observed-good; promotions CNO | Provider-neutral SandboxProvider contract, SSSF lifecycle record seam, destroy authorization gate, aggregate fold, and deterministic fake; no Docker/provider implementation | Landed as `b902cdcecd65c8ba03031875297d31e990f12c11`, tree-identical to PR #18 head `d38b9b4c4718389104ad5ffbd1ad05e70cb82db9`; provider-free validator/tests and exact-head CI establish only the fake-contract properties. SBX-1 is a landed implementation. SBX-1 is not activated, not accepted, not certified, and not real-provider-proven; it does not unlock SBX-2. Historical assignment-distinct review, applicable RulingEnvelope, LandingAuthorization, post-merge exact-main proof, supported Windows-host proof, and real-provider custody remain CNO or unmet. |
| FUT-003-FOUNDATION-REPAIR | CANDIDATE DOCUMENTATION — CNO FOR FUT-003 IMPLEMENTATION | Closed planning transition contract, observed-current-authority projection, BOUND-1 predecessor ordering, non-vacuous closure owner, Windows symlink CNO, containment controls, and deterministic watched-red validator; no producer/consumer/runtime implementation | `python3 docs/validation/check_planning_foundation.py` and `tests/test_planning_foundation.py` are the validation owners. That earlier increment recorded the superseded generation `planning/future-sssf@5f83760a6d71bb798b9f652f21267fad4b743f16:6e33db5ae5f7d43bf3a7f8c351d888c599d1997d`; the current successor observes `planning/future-sssf@d75103fb7ef8dd4ca40f62d40fc7479369bbdf0b:e29628eb5754a032dce989166f287b82d5c877dc`. FUT-003 is ACTIVE, not PROVEN; no task, runtime, landing, acceptance, certification, or live-enable claim. |
| FUT-003-AUTHORITY-REPAIR | CANDIDATE DOCUMENTATION — CNO FOR FUT-003 IMPLEMENTATION | One bounded successor correction for closure non-vacuity, observed current planning authority/projection, BOUND-1 predecessor ordering, Windows symlink capability CNO, credential-free CI, and retained containment/lifecycle controls; predecessor PR #23 and PR #24 remain immutable | PR #24 red reproductions and the required probes are owned by the [increment record](../increments/FUT-003_PLANNING_FOUNDATION_REPAIR.md); exact-head Linux/Windows checks and no-mistakes remain required. The projection observes `planning/future-sssf@d75103fb...:e29628eb...`, includes FUT-001..013 and named lifecycle identities, and cannot answer SBX-2 readiness. Fresh assignment-distinct semantic review is separate FirstMate work; landing, acceptance, certification, and live enablement remain CNO. |

## Future increments

Use IDs `B1-001`, `B1-002`, etc. after the B0 freeze. Every row should point to an ADR, proof record, test/trace, or immutable Git object when applicable.
