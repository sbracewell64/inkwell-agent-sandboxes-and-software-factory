# Agent bootstrap

This repository is evolved through proven, documented increments.

## Required orientation

1. Read `docs/README.md`.
2. Read `docs/baseline/BASELINE.md`.
3. Use `docs/README.md` as the router and load only documents relevant to the current task.
4. For changes to SSSF itself, read `docs/development/INCREMENT_PROTOCOL.md` before editing.

Do not recursively read the entire documentation tree at startup.

## Authority

When sources disagree, follow `docs/reference/SOURCE_OF_TRUTH.md`. Executable code and deterministic evidence outrank narrative documentation. Chat history is not durable system authority.

## Core boundary

Code owns sequencing, retries, permissions, gates, and acceptance. Agents own reasoning and work only inside bounded phases.

## Change discipline

Do not edit files under `adws/adw_data/sessions/`. Do not weaken a gate to make a failing run pass. Record architectural changes as proven increments and update the relevant durable documentation with the implementation.

Every increment declares a `boundedness_delta` (`docs/development/INCREMENT_PROTOCOL.md`, step 7).

## Boundedness

Any state that can grow with work, time, input, retries, descendants, or retained output needs a declared growth contract. Adding one means adding a `BOUNDEDNESS-OWNER: <surface_id>` marker beside the owner in source and a matching entry in `docs/reference/BOUNDEDNESS_REGISTRY.json`; `docs/validation/check_boundedness.py` fails required CI if either side is missing, if the registry disagrees with the limit it re-reads from source, or if an increment omits its delta. The law is `docs/development/BOUNDEDNESS_LAW.md`.

## Maintaining this file

Keep this file for knowledge useful to almost every future agent session in this project.
Do not repeat what the codebase already shows; point to the authoritative file or command instead.
Prefer rewriting or pruning existing entries over appending new ones.
When updating this file, preserve this bar for all agents and keep entries concise.
