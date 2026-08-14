\# B3-004 — SQLite-Free Windows Host Observability



\*\*Status:\*\* IN\_PROGRESS

\*\*Starts from:\*\* `sssf-b3-003-windows-bootstrap-host-doctor`



\## Problem



The Windows host does not have an external `sqlite3` executable.



Before B3-004:



`where sqlite3`



reported no executable.



`just obs sessions`



therefore failed with:



`sqlite3: command not found`



The same external CLI dependency existed in:



\- `sessions`

\- `phases`

\- `tail`

\- `procs`

\- the live-process lookup used by `kill`



The roster command remained operational because it does not query SQLite.



\## Existing owned capability



SSSF already uses Python's standard-library `sqlite3` module for its trace database.



Adding a second host SQLite implementation solely for read queries would unnecessarily expand the Windows prerequisite surface.



B3-004 therefore reuses Python standard-library SQLite.



\## Diagnostic finding



The canonical checkout does not normally contain:



`adws/adw\_data/sssf.db`



Trace databases are runtime state and are ignored by Git.



During B3-004 probing, a diagnostic call to:



`sqlite3.connect(...)`



against the missing path created an empty zero-byte database before the subsequent table query failed.



That diagnostic artifact was identified and deleted before B3-004 implementation began.



This finding strengthens the observability contract:



read-only inspection must never create a missing trace database.



\## Desired outcome



Host observability queries must work without an external `sqlite3` executable.



The replacement must:



1\. use Python standard-library `sqlite3`;

2\. open observability databases read-only;

3\. never create a missing DB;

4\. preserve the existing query semantics;

5\. preserve pipe-delimited query output;

6\. parameterize ADW IDs;

7\. permit deterministic fixture databases through `SSSF\_DB`;

8\. preserve runtime default DB location;

9\. preserve the existing `kill` PID-reuse safety behavior.



\## Query helper



B3-004 adds:



`tools/obs\_query.py`



Supported commands:



\- `sessions`

\- `phases ADW\_ID`

\- `tail ADW\_ID`

\- `procs ADW\_ID`

\- `live-pids ADW\_ID`



The helper opens SQLite using URI:



`mode=ro`



and enables:



`PRAGMA query\_only=ON`



It also retains a bounded SQLite busy timeout for live WAL readers.



\## Database path contract



The default remains:



`adws/adw\_data/sssf.db`



The observability Just module also accepts:



`SSSF\_DB`



as an override.



This allows deterministic fixtures and explicit alternate runtime databases without changing normal SSSF behavior.



\## Parameterization



ADW-scoped queries use SQLite parameter binding:



`WHERE adw\_id = ?`



rather than interpolating the requested ID into SQL text.



The validator includes an injection-shaped ADW ID and requires it to return no unrelated rows.



\## Missing-database contract



A missing database must:



\- return a non-zero result;

\- report `database not found`;

\- remain absent after the query.



Observability reads must never create an empty trace DB merely because an operator asked for status.



\## Just namespace migration



B3-004 routes:



\- `just obs sessions`

\- `just obs phases`

\- `just obs tail`

\- `just obs procs`



through `tools/obs\_query.py`.



The PID lookup inside:



`just obs kill`



also uses the same read-only helper.



The destructive process-validation and kill behavior itself is otherwise unchanged.



\## Deterministic validation



B3-004 adds:



`docs/validation/check\_obs\_query.py`



The validator creates a temporary fixture database containing deterministic:



\- session

\- phase

\- event

\- live-process

\- ended-process



rows.



It verifies both:



\- direct Python helper behavior;

\- the real `just obs` recipes through `SSSF\_DB`.



The fixture is temporary and is not placed in runtime state.



\## External sqlite3 acceptance condition



On the proven Windows host:



`where sqlite3`



must continue to report no executable.



The B3-004 validator is run with:



`--require-no-external-sqlite3`



and must still pass all observability query fixtures.



\## Host doctor integration



The B3-003 Windows host doctor is extended to run the B3-004 observability validator.



After B3-004, external sqlite3 becomes informational only.



Its absence is no longer a portability defect.



\## Non-goals



\- Change trace schema.

\- Change tracer write behavior.

\- Commit a runtime trace DB.

\- Change the observability UI.

\- Change process-kill semantics beyond its SQLite lookup.

\- Replace exe.dev.

\- Change ADW behavior.

\- Add a third-party SQLite dependency.



\## Acceptance



1\. `where sqlite3` reports no external executable on the proof host.

2\. `just/obs.just` no longer invokes the external sqlite3 CLI.

3\. `sessions` works against the deterministic fixture.

4\. `phases` works against the deterministic fixture.

5\. `tail` works against the deterministic fixture.

6\. `procs` works against the deterministic fixture.

7\. live PID lookup works through the Python helper.

8\. ADW-scoped queries are parameterized.

9\. missing DB queries fail explicitly.

10\. missing DB queries do not create a database.

11\. `SSSF\_DB` overrides the default DB for deterministic testing.

12\. the default runtime DB path remains unchanged.

13\. `rosters` remains operational.

14\. Python sources compile.

15\. B3-002 line-ending validation still passes.

16\. the Windows host doctor includes the observability contract.

17\. `git diff --check` passes.

18\. B3-003 remains frozen at `97858ca5b0e16333a0136b6d9652e501be699115`.



\## Evidence



Pending implementation validation.



\## Result



Pending.
