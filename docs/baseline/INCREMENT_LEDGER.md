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

## Future increments

Use IDs `B1-001`, `B1-002`, etc. after the B0 freeze. Every row should point to an ADR, proof record, test/trace, or immutable Git object when applicable.
