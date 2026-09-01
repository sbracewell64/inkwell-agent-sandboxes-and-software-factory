# B1-001 — Agent Documentation Discovery

**Status:** PROVEN  
**Starts from:** `sssf-local-b0`

## Problem

The frozen B0 system has a durable `docs/` record, but repository-level agent entrypoints do not consistently route agents to it. Existing bootstrap material also contains stale pre-B0 claims.

## Desired outcome

A fresh repository-level orchestrator is deterministically directed to the durable documentation index and frozen baseline before using task-specific skills or references.

## Non-goals

- Change ADW sequencing or acceptance.
- Change agent models or roster qualification.
- Replace exe.dev.
- Force bounded ADW role agents to ingest the platform documentation.
- Recursively load the whole documentation tree at startup.

## Files / boundaries in scope

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/commands/prime.md`
- `.claude/skills/sssf/SKILL.md`
- `.claude/skills/sssf-sandbox-orchestrator/SKILL.md`
- `docs/README.md`
- `docs/manifest.yaml`
- `docs/validation/check_agent_bootstrap.py`

## Design

Root agent entrypoints route to `docs/README.md` and `docs/baseline/BASELINE.md`. The documentation index remains a lazy-loading router. Existing portable skills conditionally use the local docs only when they exist. Executable code and current evidence remain higher authority than narrative documentation.

## Acceptance

1. `docs/validation/check_agent_bootstrap.py` passes.
2. `git diff --check` passes.
3. Every changed documentation/bootstrap file is valid UTF-8.
4. Frozen B0 tags remain unchanged.
5. No ADW runtime session evidence is edited.
6. Known stale claims about namespace count, teardown proof, visualizer availability, and fixed default model are removed or corrected.

## Evidence

- `python docs/validation/check_agent_bootstrap.py` -> PASS; 7 durable entrypoints/references validated.
- `git diff --check` -> PASS.
- All changed/untracked files validated as UTF-8.
- No `adws/adw_data/sessions/` runtime evidence changed.
- `sssf-local-b0` remained `c54b7b9ae83802023a52c46f8e960567c1e946f0`.
- `sssf-proof-b0` remained `042dfb9d34a14fe5952538fedddbd136b334947e`.

## Result

Repository-level agents now have durable bootstrap entrypoints that route through the documentation index and frozen baseline. Claude Code, `/prime`, `/sssf`, and `/sssf-sandbox-orchestrator` discover the local system record without recursively loading the documentation tree. Stale pre-B0 bootstrap claims were corrected.

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
