# ADR-0004 — One Authority and One Mutation Owner per Record Field

**Status:** Accepted
**Date:** 2026-08-17

## Context

SSSF writes run facts to several surfaces at once: append-only event JSONL, overwrite-style
envelope and agent-map files, SQLite trace tables, per-request query projections, frozen evidence
copies, and the sandbox lifecycle run record. Nothing named which surface was authoritative for a
given fact or which component was allowed to change it.

Two governed documents filled that gap incorrectly. They presented `sssf.db` as a derived copy of
the run's files and told the reader that destroying it cost nothing, and the root architecture
document still proposed a host observability fix that B3-004 had already shipped. The code disagrees:
only events are dual-written. Session, phase, process, gate, invalid-envelope, usage and
agent-session facts are SQLite-only or only partially represented on disk.

The practical consequences were an operator rebuilding the database believing the files were
canonical, calling the visualizer wholly read-only when it holds one deliberate triage write, and
reading that triage write as a run or evidence mutation.

## Decision

Every field of every record surface has exactly one authority and exactly one mutation owner,
declared in `tools/sqlite_authority.py` and rendered into `docs/reference/SQLITE_AUTHORITY.md`.

Six authority classes are kept distinct: `raw-transport`, `canonical-run-state`, `query-projection`,
`triage-state`, `archived-evidence-copy`, and `lifecycle-run-record`. Query projections and archived
evidence copies have **no** mutation owner. Canonical run state is mutated only by
`adws/adw_modules/tracer.py`. Triage state is `sessions.archived` and is mutated only by
`POST /api/sessions/:adw_id/archive`.

Every field additionally declares a `raw_source` — `none`, `complete:<file>`, or `partial:<file>` —
so "what survives losing the database" is a checkable field-level fact rather than a slogan.

Observation of a database is three-valued and consumes HD-08's vocabulary: `observed-good`,
`observed-bad`, `could-not-observe`, with exit codes `0`, `1`, `2`. A missing or empty database is
CNO. Observed-bad outranks CNO, which outranks observed-good.

The tracer, the visualizer and the read-only query helper are correct and are not changed. If
satisfying this matrix ever appears to require changing a write path, the code is wrong rather than
the document, and that is a separate increment and a separate decision.

## Consequences

Positive:

- deleting, rebuilding, relocating or archiving a trace database is an informed decision;
- the reference is generated from the executable owner, so a schema change that is not reflected in
  the matrix fails a deterministic check instead of ageing into a false document;
- archiving is provably incapable of touching terminal acceptance or evidence hashes;
- an unreadable database cannot be mistaken for a clean one, and cannot mask a real violation.

Cost:

- adding a table, column, projected value, manifest field or run-record field now requires a matrix
  entry in the same change;
- the generated Markdown block must be regenerated with `python3 tools/sqlite_authority.py render`
  rather than hand-edited;
- the visualizer read surface must be re-exercised under Bun whenever its server sources change,
  or the stdlib gate goes red on the digest binding — deliberately, since that red is the whole
  mechanism keeping the executed proof true.

## Executing the visualizer read surface

The visualizer's reader is TypeScript. Three options were weighed for proving its read-only
property, and the chosen one carries an addition without which it decays.

- **Make the CI gate execute it under Bun.** Rejected. This program already has a validator that is
  documented as the authority for its contract yet sits outside CI because of a toolchain
  dependency. A check that cannot run is worth less than a weaker check that does.
- **Assert it from source bytes only.** Rejected. Reading the construction site is not running the
  thing, and it is the defect class this campaign has been closing.
- **Chosen: execute it in a separate Bun-only control, and bind that control's result to the exact
  bytes it ran against.** `docs/validation/exercise_visualizer_read_surface.ts` runs the real
  `SssfDb`, requires the fixture digest unchanged across every read method, and requires a mutation
  through the connection those methods use to fail. It records the SHA-256 of the TypeScript it
  executed. The stdlib CI check fails when the current source digest differs from the recorded one.

The addition is not optional. A separately documented control is executed once and then not again;
its result becomes a claim about bytes that have since moved, and an unexecuted documented control is
prose. CI cannot execute TypeScript, but it can determine whether the TypeScript has changed since it
was last actually exercised, and comparing digests needs no Bun. That converts a decaying document
into a maintained one, keeps the gate stdlib-only, and makes the real proof real for exactly the
bytes it covers.

A reader of the CI result must be able to establish which bytes were executed, when, and that the
current bytes are those bytes — so the passing output prints both digests, the Bun version, the
script and the timestamp, and states plainly that the stdlib check did not itself execute the read
surface. An absent record is could-not-observe, never a pass.

## Alternatives considered

- **Leave the documents and add only a validator.** Rejected: the documents were the harm.
- **Rewrite `specs/scaffold.md` too.** Rejected: it is generated history under
  `SOURCE_OF_TRUTH.md`, and source custody forbids rewriting it. The supersession is recorded in the
  reference instead, and the validator asserts that notice exists.
- **Make the read helper itself return CNO for an empty database.** Rejected: the helper is correct
  and in scope only for the increment that owns its behaviour. Three-valued observation belongs to
  the new owner, not to the shipped read path.
