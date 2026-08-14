# B3-004 — SQLite-Free Windows Host Observability

**Status:** PROVEN
**Starts from:** `sssf-b3-003-windows-bootstrap-host-doctor`
**Accepted candidate:** `9d160bb21ae15283acaca5fa98aa56587c3db414`
**Proof date:** 2026-08-14

## Problem

The Windows host does not have an external `sqlite3` executable.

Before B3-004:

`where sqlite3`

reported no executable.

`just obs sessions`

therefore failed because `just/obs.just` directly invoked the external sqlite3 CLI.

The same external dependency existed in:

- `sessions`
- `phases`
- `tail`
- `procs`
- the live-process lookup used by `kill`

`just obs rosters` remained operational because it does not query SQLite.

## Existing owned capability

SSSF already uses Python's standard-library `sqlite3` module for its trace database.

Adding a separate host SQLite executable solely for read queries would unnecessarily expand the Windows prerequisite surface.

B3-004 therefore reuses the Python standard library that SSSF already depends on.

## Diagnostic finding

The canonical checkout does not normally contain:

`adws/adw_data/sssf.db`

Trace databases are runtime state and are ignored by Git.

During initial B3-004 probing, a diagnostic call using ordinary:

`sqlite3.connect(...)`

against the missing path created an empty zero-byte database before the subsequent table query failed.

The artifact was identified as:

`adws/adw_data/sssf.db`

with size:

`0 bytes`

It was deleted before implementation began.

After deletion:

`dir /a adws\adw_data\sssf.db*`

reported:

`File Not Found`

and the Git working tree remained clean.

This strengthened the B3-004 contract: an observability read must never create runtime state merely because the operator asked to inspect it.

## Desired outcome

Host observability must work without an external sqlite3 executable.

The replacement must:

1. use Python standard-library `sqlite3`;
2. open observability databases read-only;
3. never create a missing DB;
4. preserve existing query semantics;
5. preserve pipe-delimited output;
6. parameterize ADW IDs;
7. permit deterministic fixture databases through `SSSF_DB`;
8. preserve the normal runtime database location;
9. preserve the existing `kill` PID-reuse safety behavior;
10. make external sqlite3 optional rather than required.

## Implementation

B3-004 adds:

`tools/obs_query.py`

Supported commands are:

- `sessions`
- `phases ADW_ID`
- `tail ADW_ID`
- `procs ADW_ID`
- `live-pids ADW_ID`

The helper opens SQLite using a URI with:

`mode=ro`

and enables:

`PRAGMA query_only=ON`

It also applies a bounded SQLite busy timeout suitable for reading a live WAL-backed trace database.

## Database path contract

The default database remains:

`adws/adw_data/sssf.db`

The observability Just module accepts:

`SSSF_DB`

as an override.

This provides a deterministic validation seam and permits an explicitly selected runtime database without changing the normal default.

## Parameterization

ADW-scoped queries use SQLite parameter binding:

`WHERE adw_id = ?`

The requested ADW ID is passed separately from SQL text.

The validator supplies an injection-shaped ADW ID and requires it to return no unrelated records.

## Missing-database contract

A missing database must:

- return non-zero;
- report `database not found`;
- remain absent after the command.

This behavior is enforced by the read-only open path.

## Just namespace migration

B3-004 routes:

- `just obs sessions`
- `just obs phases`
- `just obs tail`
- `just obs procs`

through:

`tools/obs_query.py`

The PID lookup inside:

`just obs kill`

also uses the helper.

The subsequent PID validation and process-kill logic is otherwise unchanged.

## Deterministic validator

B3-004 adds:

`docs/validation/check_obs_query.py`

The validator creates a disposable temporary SQLite fixture containing deterministic:

- session
- phase
- event
- live-process
- ended-process

records.

It verifies:

- direct Python helper queries;
- `sessions`;
- `phases`;
- `tail`;
- `procs`;
- live PID lookup;
- parameterized ADW-ID handling;
- the real `just obs` recipes through `SSSF_DB`;
- missing-database non-creation.

The fixture does not enter normal runtime state.

## Pre-candidate proof

Before the implementation candidate was committed:

`where sqlite3`

continued to report no executable.

The validator was run with:

`--require-no-external-sqlite3`

and reported:

`B3-004 sqlite-free observability: PASS`

with:

- stdlib sqlite3 serving sessions/phases/tail/procs;
- ADW-ID queries parameterized;
- missing databases failing read-only without creation;
- external sqlite3 CLI absent.

`just obs sessions`

against the absent normal runtime DB failed explicitly with:

`obs_query: database not found`

Immediately afterward:

`dir /a adws\adw_data\sssf.db*`

reported:

`File Not Found`

`just obs rosters`

continued to work.

The B3-002 line-ending validator passed.

The Windows host doctor reported:

`observability query contract — B3-004 validator PASS`

and:

`external sqlite3 — absent; host observability uses Python stdlib sqlite3`

The host doctor ended:

`SSSF Windows host doctor: OK`

## First candidate hygiene rejection

The first local candidate commit was:

`1cf6c9c4198794a9181f40d442cace1793c9cd59`

Its substantive B3-004 tests passed.

However, the pre-commit whitespace gate had reported:

`docs/increments/B3-004_SQLITE_FREE_OBSERVABILITY.md:472: new blank line at EOF.`

The commit was mistakenly created despite that failed hygiene gate.

`git show --check`

reproduced the same finding.

The candidate had not been pushed.

It was therefore rejected before acceptance.

## Corrected candidate

The increment record EOF was normalized and staged.

`git diff --cached --check`

then passed with no output.

The unpublished candidate was amended.

The corrected implementation candidate is:

`9d160bb21ae15283acaca5fa98aa56587c3db414`

`git show --check --oneline HEAD`

reported the candidate with no whitespace finding.

The working tree was clean.

## Exact-candidate proof

All core B3-004 gates were rerun against exact candidate:

`9d160bb21ae15283acaca5fa98aa56587c3db414`

Results:

- external sqlite3 remained absent;
- deterministic B3-004 validator: PASS;
- B3-002 line-ending validator: PASS;
- Windows host doctor: PASS;
- B3-004 observability-query contract: PASS;
- stdlib sqlite3 selected for host observability;
- missing normal runtime DB produced an explicit error;
- missing DB remained absent after inspection;
- no direct `sqlite3 ` CLI call remained in `just/obs.just`;
- `git diff --check` passed;
- working tree remained clean.

## Remote candidate identity

The corrected candidate was pushed to:

`increment/b3-004-sqlite-free-observability`

Local:

`git rev-parse HEAD`

resolved:

`9d160bb21ae15283acaca5fa98aa56587c3db414`

Remote:

`git ls-remote --heads origin increment/b3-004-sqlite-free-observability`

resolved the same SHA.

The implementation proven locally is therefore the exact implementation published remotely.

## Host doctor integration

The Windows host doctor now executes the B3-004 validator as part of its deterministic checks.

The doctor reports external sqlite3 only as information.

Its absence is no longer a Windows portability defect.

## Documentation normalization

The initial implementation commit contained an increment record whose Markdown characters had been escaped during editing.

That formatting defect did not affect executable behavior or the exact-candidate proof.

The documentation-only B3-004 closure normalized this record to ordinary Markdown.

The implementation candidate remained unchanged.

## Post-freeze closure-hygiene incident

The first published B3-004 closure commit was:

`15bbea9bbf94d4b1491da47d9032707af77c2b04`

Before that commit, both:

`git diff --check`

and:

`git diff --cached --check`

reported trailing whitespace on the `Status`, `Starts from`, and `Accepted candidate` metadata lines in this document.

The closure commit was nevertheless created, tagged, and advanced to `main`.

`git show --check`

then reproduced the same three findings.

The already-published tag:

`sssf-b3-004-sqlite-free-observability`

is immutable and is not moved or deleted.

It therefore remains the durable historical record of the first published B3-004 closure, including its documentation-hygiene defect.

A subsequent correction removes only that trailing whitespace, records this incident explicitly, and is frozen under the separate tag:

`sssf-b3-004-closure-hygiene-correction`

The executable B3-004 implementation candidate remains:

`9d160bb21ae15283acaca5fa98aa56587c3db414`

No B3-004 runtime behavior is changed by the hygiene correction.

The clean correction state, rather than the original closure tag, is the base for subsequent B3 work.

## Non-goals

- Change trace schema.
- Change tracer write behavior.
- Commit a runtime trace DB.
- Change the observability UI.
- Change process-kill semantics beyond its database lookup.
- Replace exe.dev.
- Change ADW workflow behavior.
- Add a third-party SQLite dependency.

## Acceptance

1. External sqlite3 is absent on the proven Windows host.
2. `just/obs.just` no longer invokes the external sqlite3 CLI.
3. `sessions` passes against the deterministic fixture.
4. `phases` passes against the deterministic fixture.
5. `tail` passes against the deterministic fixture.
6. `procs` passes against the deterministic fixture.
7. live PID lookup passes through the Python helper.
8. ADW-scoped queries are parameterized.
9. missing DB queries fail explicitly.
10. missing DB queries do not create a database.
11. `SSSF_DB` overrides the default DB for deterministic validation.
12. the normal runtime DB location is unchanged.
13. `rosters` remains operational.
14. Python sources compile.
15. B3-002 line-ending validation passes.
16. the Windows host doctor enforces the B3-004 observability contract.
17. `git diff --check` passes.
18. the corrected candidate itself passes `git show --check`.
19. local and remote candidate SHAs match exactly.
20. external sqlite3 is informational rather than a required Windows dependency.
21. B3-003 remains frozen at `97858ca5b0e16333a0136b6d9652e501be699115`.
22. the malformed implementation-stage Markdown is normalized only in the documentation closure.

All B3-004 acceptance criteria are satisfied.

## Result

B3-004 removes the external sqlite3 CLI from the Windows host observability dependency surface.

SSSF now uses its already-owned Python standard-library SQLite capability for host trace queries.

Observability reads are explicitly read-only, missing databases cannot be silently created, ADW identifiers are parameterized, and deterministic fixture validation exercises the real Just front doors without requiring live runtime state.

**Result: PASS**
