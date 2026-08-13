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
