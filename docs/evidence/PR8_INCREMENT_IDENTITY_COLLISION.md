# Pull request 8 increment-identity collision calibration

**Recorded:** 2026-08-17  
**Pre-correction pull request head:** `8a644b79278f12f29d7f107dbbc38a71a3b75581`  
**Scope:** pull requests 8–13 based on trunk `bee9296a4c94b1dc3da6991acd1755a91fa681eb`

This record preserves a content defect that an ordinary textual merge need not
reject. At the pre-correction head, pull request 8 added this ledger row:

> `| HD-04 | CORRECTED CANDIDATE — CNO | Typed mapped-surface parity and fresh-stamp verification | ... |`

Pull request 10 independently adds `HD-04` for mutation-fact reconciliation.
The rows can occupy different locations after a merge, so conflict detection is
not an identity-uniqueness control.

## Authoritative identity evidence

Landed history assigns HD-04 to mutations. At trunk
`bee9296a4c94b1dc3da6991acd1755a91fa681eb`,
`docs/increments/HD-03_NONVACUOUS_GATE_OUTCOME.md` states in its Non-goals
section:

> “This increment does not reconcile envelope claims with actual Git/path/content
> mutations (HD-04), define contribution Git context (HD-05), or change path/diff
> semantics.”

Pull request 10 implements exactly that reserved mutation scope. Its immutable
head `e5e0c34c4500cbe5a99374b25968ad7ab2bc1fef` contains
`docs/increments/HD-04_MUTATION_FACT_RECONCILIATION.md`, whose title is:

> “HD-04 — One mutation fact, reconciled bidirectionally against the claims”

Pull request 8 instead owns mapped-surface parity and fresh-stamp verification.
Its immutable pre-correction head has no mapped-surface increment document under
`docs/increments/`, its branch/task identity is
`fm/sssf-live-mirror-adw-drift`, and its commits before the erroneous ledger row
assign no HD identity. Its architectural decision is ADR-0004, but an ADR number
is not an increment assignment.

The ledger's own future-ID instruction says:

> “Use IDs `B1-001`, `B1-002`, etc. after the B0 freeze.”

That convention does not authoritatively map this candidate to a particular B
identity. Choosing an unused HD or B number would therefore invent identity from
availability. The correct observed state is **could-not-observe an authoritative
increment assignment**, not a guessed identity. Until an authoritative assignment
is made, pull request 8 has no ledger row.

## Complete claim check for the affected pull-request set

The ledger deltas at the immutable heads were inspected for every open SSSF
feature pull request in the affected set:

| Pull request | Immutable head | Claimed identity before correction |
|---|---|---|
| 8 | `8a644b79278f12f29d7f107dbbc38a71a3b75581` | HD-04 (erroneous; now withdrawn) |
| 9 | `5a7d8a36c18dfb84c3ac895a0c93139c630c7f84` | HD-11 |
| 10 | `e5e0c34c4500cbe5a99374b25968ad7ab2bc1fef` | HD-04 (authoritative mutation scope) |
| 11 | `9e498bc28db111e38b5962006d523b69e22a37c3` | HD-15 |
| 12 | `b5a00ff392c340a98c4a0156eb547865c078c20e` | HD-14 |
| 13 | `84ce1e74cbb3d8fad88edab280192102961cbe14` | HD-13 |

Trunk's HD rows are HD-01, HD-02, HD-03, and HD-08. Before correction, HD-04
was the only duplicate claim across trunk and the six pull requests. After
withdrawing pull request 8's unsupported claim, every assigned identity in that
combined set is unique.

## Three-valued calibration result

- **Observed-bad:** pull request 8's pre-correction head claimed HD-04 for mapped
  parity while landed HD-03 reserves HD-04 for mutations.
- **Observed-good:** immutable ledger deltas establish the complete claim map
  above and show that withdrawing pull request 8's claim leaves unique assigned
  identities.
- **Could-not-observe:** no authoritative source assigns a replacement increment
  ID to pull request 8. This is why the correction leaves it unregistered rather
  than treating absence as a guessed pass.

The defective row remains discoverable in immutable commit
`8a644b79278f12f29d7f107dbbc38a71a3b75581` and in this calibration record; its
removal from the current ledger does not rewrite that evidence.
