# B2-001 — Canonical Repository Ownership

**Status:** PROVEN  
**Starts from:** `sssf-b1-agent-doc-discovery`

## Problem

The local SSSF evolved beyond Disler's upstream repository, but no operator-owned remote contained the proven platform history and future increments.

## Desired outcome

Establish `sbracewell64/inkwell-agent-sandboxes-and-software-factory` as the writable canonical repository while retaining Disler's repository as a reference-only upstream.

## Repository contract

- `origin` — operator-owned canonical repository.
- `upstream` — Disler reference repository.
- `origin/main` — latest accepted/proven platform state.
- `increment/*` — bounded development increments.
- `sssf-*` — immutable proven tags.
- Pushes to `upstream` are disabled locally.

## Non-goals

- Change sandbox clone behavior.
- Change `fill.just`.
- Replace exe.dev.
- Change ADWs or agent rosters.
- Rewrite B0 or B1 history.

## Acceptance

1. `upstream/main` remains `92f1701810993b8303562265ba04c727468fe070`.
2. `origin/main` is proven B1 commit `49342bd3851cb71a79c69b8438d2b5062836b08d`.
3. B0 and B1 branches exist on `origin`.
4. Proven B0/B1 tags exist remotely at their exact commits.
5. Local `main` tracks `origin/main`.
6. `upstream` fetches from Disler and its configured push URL is disabled.
7. No existing proven history is rewritten.

## Evidence

- `python docs/validation/check_repository_ownership.py` -> PASS.
- Canonical `origin`: `https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git`.
- Reference-only `upstream`: `https://github.com/disler/inkwell-agent-sandboxes-and-software-factory.git`.
- `upstream` push URL configured as `DISABLED`.
- `upstream/main` remained `92f1701810993b8303562265ba04c727468fe070`.
- `origin/main` resolved to proven B1 commit `49342bd3851cb71a79c69b8438d2b5062836b08d`.
- Local `main` tracks `origin/main`.
- Remote B0/B1 branches and all existing `sssf-*` tags were verified at their exact proven commits.
- `git diff --check` reported no whitespace errors.
- All B2-001 files validated as UTF-8.

## Result

The operator-owned GitHub fork is now the canonical writable source for the evolving SSSF. Disler's repository remains available as a reference-only upstream. Accepted platform history can now advance through exact proven commits without rewriting B0 or B1.

Sandbox source selection is intentionally not included in this increment. B2-002 will make the sandbox repository URL and exact source revision explicit inputs.

## Boundedness delta

```text
boundedness_delta: none
boundedness_reason: this increment predates the boundedness registry. Its
  growth surfaces, where it created any, were inventoried and bound
  retrospectively by BOUND-1 against the post-increment source rather than
  claimed here after the fact. See
  docs/reference/BOUNDEDNESS_REGISTRY.json and
  docs/development/BOUNDEDNESS_LAW.md.
```
