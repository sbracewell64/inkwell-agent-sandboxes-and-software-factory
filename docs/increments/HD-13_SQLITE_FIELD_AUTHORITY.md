# HD-13 — Field-Level Record Authority for SQLite Facts

**Status:** PROVEN
**Starts from:** `bee9296a4c94b1dc3da6991acd1755a91fa681eb`

## Problem

No document assigned an authority or a mutation owner to individual trace fields, and two governed
documents asserted the opposite of what the code does. The observability reference presented
`sssf.db` as a derived copy of the run's files and told the reader that destroying it cost nothing.
The root architecture document still proposed, as future work, the Python-only host observability
path that B3-004 had already shipped. Both were observed-bad documentation over observed-good code.

The harm: an operator deletes or rebuilds the database believing the files are canonical, calls the
visualizer wholly read-only, or reads an archive triage write as a run or evidence mutation.

The tracer appends every **event** to both `events.jsonl` and SQLite. Nothing else is dual-written.
Sessions, phases, processes, gate checks, all envelope attempts, usage totals and agent-session
facts are SQLite-only or only partially represented by overwrite-style files. The smallest
counterfactual: delete the database after an invalid-envelope or gate attempt, and no file
necessarily reconstructs the phase, gate, process or session canonical row.

## Desired outcome

One executable owner assigning exactly one authority and one mutation owner to every field of every
record surface across six distinct classes, plus a deterministic validator for two assertions:
read-only surfaces cannot mutate, and only the archive route can change triage state.

## Non-goals

- no change to the tracer's write paths, the visualizer's behaviour, or the read-only query helper —
  all three were found correct; only stale contract comments and guidance are corrected;
- no new runtime acceptance authority; observation is reporting, not a gate;
- no rewrite of `specs/`, which is retained history under `SOURCE_OF_TRUTH.md`;
- no claim that a green observation authorizes deleting or rebuilding a trace database.

## Files / boundaries in scope

- owner: `tools/sqlite_authority.py`;
- deterministic validator: `docs/validation/check_sqlite_authority.py`;
- contract and generated matrix: `docs/reference/SQLITE_AUTHORITY.md`;
- corrected root document: `docs/architecture/OBSERVABILITY.md`;
- corrected skill documents: `.claude/skills/sssf/references/observability.md`,
  `.claude/skills/sssf/references/handoff.md`;
- CI registration: `ci/checks.json` and `docs/validation/check_ci_contract.py`;
- ledger/proof/reference/router updates.

## Design

`tools/sqlite_authority.py` holds the matrix as data and projects it three ways: canonical JSON,
the Markdown block the reference must embed verbatim, and a three-valued observation of a database.
The reference document is generated from the owner rather than hand-maintained, so a schema change
that is not reflected in the matrix cannot leave the documentation quietly stale.

Six authority classes are kept distinct, and the four duties the increment must separate are held
by four different owners: observation (`tools/obs_query.py` and the visualizer read connection, no
mutation owner), triage (the archive route, `sessions.archived` only), archive/evidence copy
(`tools/evidence_manifest.py`, frozen hash-bound bytes), and run-state mutation
(`adws/adw_modules/tracer.py`, every other SQLite column).

Every field also carries a `raw_source`: `none`, `complete:<file>`, or `partial:<file>`. This is the
operational answer to "if the database is destroyed, what file still carries this fact?", and it is
what makes the corrected documents checkable rather than merely reworded.

Terminology is consumed from HD-08 rather than reinvented: `observed-good` / `observed-bad` /
`could-not-observe`, exit codes `0` / `1` / `2`, and canonical sorted-key UTF-8 JSON with one final
LF. Precedence is fixed: observed-bad outranks CNO, which outranks observed-good.

## Risks / failure modes

- A missing, zero-byte, unreadable, schema-less or row-less database is CNO, never an empty PASS.
- An unreadable database never masks a contradiction: every contradiction reachable without opening
  the file is still reported, and observed-bad wins when both are present.
- A column present but undeclared is observed-bad; a column declared but absent is CNO, matching the
  HD-03 rule that a reader facing an unmigrated schema projects CNO rather than guessing.
- The matrix is a documentation authority, not a runtime gate. A green observation does not
  authorize deleting or rebuilding a trace database.
- The validator reads the tracer's DDL out of its source bytes rather than importing it, so it stays
  stdlib-only and CI-runnable; a tracer that stops declaring `SCHEMA`/`MIGRATIONS` as literals makes
  the completeness control fail loudly rather than silently pass.

## Acceptance

### Deterministic checks

```text
python3 docs/validation/check_sqlite_authority.py
python3 docs/validation/check_sqlite_authority.py --controls
python3 docs/validation/check_ci_contract.py
python3 -m compileall -q tools/sqlite_authority.py docs/validation/check_sqlite_authority.py
```

Every claim is asserted as a property, never as a proxy:

- **read-only surfaces cannot mutate** — a fixture built from the tracer's real DDL is snapshotted
  as a whole-file SHA-256 *and* a full cell-by-cell logical dump; every `obs_query` surface runs
  against it; both components must be identical afterwards. A real `UPDATE` through the real
  `connect_read_only()` helper must then raise, and the snapshot must still be unchanged.
- **only the archive route can change triage state** — the archive `UPDATE` is extracted from the
  visualizer's own bytes rather than retyped, executed against the fixture, and every cell of every
  table is diffed. Any cell outside `sessions.archived` fails.
- **a missing or empty database is could-not-observe** — missing, zero-byte, unreadable,
  schema-only and row-less databases each return CNO and exit `2`.
- **archiving never changes terminal acceptance or evidence hashes** — proven by the same
  cell-level diff, which covers `phases.status`, `gate_results.outcome` and every other column.
- **the visualizer read surface is executed, not inspected** — `exercise_visualizer_read_surface.ts`
  runs the real `SssfDb` under Bun against a fixture built from the tracer's real DDL, requires the
  whole-file digest unchanged across every public read method, and requires a mutation through the
  connection those methods use to fail. It records the SHA-256 of the TypeScript it ran, and the
  stdlib CI check fails when the present source differs — so the exercise cannot decay into a claim
  about bytes that have moved. Only that exercise needs Bun; the CI gate stays stdlib-only.

### Watched-red controls

Each of these must be observable going red, or the green above proves nothing:

1. the documentation control run against the real uncorrected files, captured before the correction;
2. a real mutation, to prove the digest *and* the logical dump can both detect one;
3. a widened archive statement that also sets `status`, caught by the cell diff;
4. a tampered reader carrying a second write statement, caught by the extractor;
5. a copy of the shipped read helper with `mode=ro` and `query_only` removed, watched mutating the
   database — the guarded and unguarded helpers must be distinguishable;
6. an unowned column alongside zero rows, which must stay observed-bad rather than being narrowed
   to CNO;
7. each superseded sentence exactly as it shipped, which must still be rejected after the real
   documents are corrected;
8. one changed byte of the visualizer source with no re-run of the exercise, which must fail the
   digest binding;
9. an absent exercise record, which must be could-not-observe rather than a pass;
10. a recorded exercise claiming the mutation succeeded, the fixture changed, no attempt was made, or
    an incomplete read-method list — each must be rejected.

Controls 2–10 run inside the validator on every invocation, so a control that stops being able to go
red fails the validator instead of quietly passing.

### Semantic review

Independent review is delegated to the required no-mistakes pipeline before publication.

## Evidence

- sandbox run: not applicable; offline documentation and validation only
- ADW: not applicable
- pre-fix watched-red capture: `docs/evidence/hd13/documentation-claims-red.txt` — the three
  shipped documents restored byte-for-byte from `bee9296a4c94b1dc3da6991acd1755a91fa681eb` and the
  new reference removed, run through the FINAL validator: ten refuted-claim sites across
  `docs/architecture/OBSERVABILITY.md`, `.claude/skills/sssf/references/observability.md` and
  `.claude/skills/sssf/references/handoff.md`, plus the absent reference, exit 1
- corrected-state capture: `docs/evidence/hd13/corrected-state-green.txt` — the same validator,
  exit 0, with every negative control still detectable. The two captures differ only in the
  documents, so the red is not a different program from the green.
- executed read-surface record: `docs/evidence/hd13/visualizer-read-surface-exercise.json` — Bun
  1.3.14 ran the real `SssfDb`; ten public read methods left the fixture digest unchanged and a
  mutation through their own connection was refused (`attempt to write a readonly database`)
- digest-drift watched red: `docs/evidence/hd13/visualizer-digest-drift-red.txt` — one byte of
  `db.ts` changed without a re-run, exit 1, both digests printed
- unexercised watched red: `docs/evidence/hd13/visualizer-unexercised-cno.txt` — the record removed,
  reported as could-not-observe rather than a pass, exit 1
- test result: validator prints `HD-13 SQLite field authority: PASS` over 158 authority rows

## Documentation changed

Root architecture observability document, two skill references, new field-authority reference,
ADR-0004, increment ledger, proof matrix, file map, command reference, glossary, documentation
router, and CI check registration.

## Result

Every table and field has one authority and one mutation owner. Observation, triage,
archive/evidence copy, and run-state mutation are distinct duties held by distinct owners. A missing
or empty database is could-not-observe. Archiving moves one column and cannot touch terminal
acceptance or evidence hashes. The governed documents now agree with the code.

## Known limits

`specs/scaffold.md` retains the superseded claim as generated history. Under `SOURCE_OF_TRUTH.md` it
is evidence, not current runtime authority, and source custody forbids rewriting it. The
supersession is recorded in `docs/reference/SQLITE_AUTHORITY.md`, and the validator asserts that
notice is present rather than leaving the limit undiscoverable.

The visualizer's read surface is genuinely executed under Bun and digest-bound to the bytes it ran
against, so the stdlib gate stays runnable without a JavaScript toolchain while the executed proof
stays true for exactly the source it covers. Re-running the exercise is required whenever the
visualizer server sources change; the check names that requirement rather than leaving it to
discipline. Bun is not necessarily on `PATH`; install the pinned `bun@1.3.14` package when needed
and pass its `node_modules/.bin/bun` executable with `--bun`. A run without Bun verifies the binding
and identifies that mode; it does not claim a fresh execution.

The triage contract is asserted by executing the archive statement extracted from the visualizer's
own bytes, not by driving the HTTP route end to end. A route that stopped calling `setArchived`
would be caught by the single-write-statement and single-POST-route assertions rather than by
observing a request, and that distinction is stated rather than claimed as covered.

## Follow-ups

If a future increment must change a write path to satisfy this matrix, that is a defect in the code
rather than the document and belongs in its own increment with its own decision.
