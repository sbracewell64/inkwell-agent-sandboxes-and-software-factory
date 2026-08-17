# ADR-0005 — One mutation fact, compared in both directions, with a stated boundary

**Status:** Accepted
**Date:** 2026-08-16

## Context

A workflow's envelope claims what it changed, and nothing reconciled that claim
against the repository. `diff_matches_claims` walked the declared list and
asserted path existence, which is one direction and the wrong property: an
existing file is not a changed file. Claims on untouched paths passed, real
changes left out of the list were never looked for, and a truthful deletion claim
was refused because the path was gone.

Permission enforcement asked a related question — what did this agent touch —
using a different fingerprint (`git diff HEAD --numstat` line counts) taken at a
different moment (after all gate retries). Line counts are blind to an edit that
replaces a line with another of the same shape, and two snapshots of one tree read
at two moments are two sources of truth.

## Decision

One code-computed mutation fact, in `adws/adw_modules/mutation_fact.py`, is the
single answer to "what moved".

- Identity is content, not shape: per-path git blob oids before and after.
- Mutation kind is derived from that identity, never from a similarity heuristic.
  A rename is a deletion and an addition carrying equal bytes, linked as peers,
  with both paths still individually required.
- The comparison against the envelope is a set equality in both directions. A
  claimed path that did not move and a moved path that was not claimed are
  independent defects and neither is derivable from the other.
- The claim gate and the permission check consume the SAME observation object.
  `agents.execute` publishes one per gate attempt; `permissions.enforce` takes it
  as a parameter and only observes its own when a phase published none.

Every verdict carries its universe. `ObservationScope` names what was observed,
what is out of scope (gitignored files, out-of-repository writes, network effects,
process effects), and any candidate that could not be read. It is carried beside
the checks rather than as one of them, so a boundary statement can never
manufacture a PASS. A nonempty `unobservable` yields COULD_NOT_OBSERVE
(`INCOMPLETE_OBSERVED_UNIVERSE` / `MUTATION_FACT`), never an agreement; an
observed discrepancy remains FAIL regardless.

## Consequences

Agreement means agreement within the Git and permission fact set, and says so in
the console and in `gate_results.scope_json`. It does not mean nothing else
happened, and this decision does not attempt to close the out-of-scope classes.

An agent must now name exactly what it changed, including files it created
incidentally and both halves of a rename. Getting that wrong is a correctable gate
FAIL in the same session, not a run-ending breach.

`diff_matches_claims` outside a git repository is COULD_NOT_OBSERVE rather than a
pass, so an ADW that must prove what it built requires a repository.

`GateCNOReason` and `GateCNOSource` grew by one member each. Because the trace's
CHECK constraint enumerates them, `Tracer` rebuilds `gate_results` once when its
stored constraint predates a current member. The constraint is only ever widened,
so the rebuild cannot invalidate a stored row.

This decision covers the fact and its comparison only. What a contribution is
measured against — repository, worktree, branch, base, head, and the removal of
the ambient `git add -A` — is deliberately left to HD-05.
