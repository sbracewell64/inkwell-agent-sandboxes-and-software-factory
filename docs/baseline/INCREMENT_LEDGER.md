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
| B3-005 | CNO / HOLD — PRE_CERTIFICATION | Fresh Windows clone end-to-end portability proof | repaired candidate `7aedae1` proved insufficient-credit evidence stops CNO/HOLD with no downstream PASS; Browser Sol passed Windows-native environment freshness at exact reviewed head `63bc579`; roster, typed C/D/E marker, OBSERVE/end-to-end, no-CI, and merge/freeze remain held; all sandboxes cleaned |
| B4-001 | PASS | Non-vacuous deterministic GitHub CI bootstrap | run `31907345967` on reviewed head `29819d98ea2b046bc432bde2a3e9cd42be7640a4`: Ubuntu and Windows each discovered/executed 6/6 observed-good checks and passed Inkwell 30/30 with 230 assertions; closure successor and later `main` push require fresh checks |

## Future increments

Use IDs `B1-001`, `B1-002`, etc. after the B0 freeze. Every row should point to an ADR, proof record, test/trace, or immutable Git object when applicable.