# ADR-0003 — Three-valued nonvacuous gate outcomes

**Status:** Accepted
**Date:** 2026-08-15

## Context

Gate success was inferred from `not violations`. Empty required evidence
therefore looked identical to fully observed positive evidence and could advance
an agent phase, emit `gate_pass`, and render green.

## Decision

`adws/adw_modules/data_types.py` owns one typed gate outcome with statuses
`PASS`, `FAIL`, and `COULD_NOT_OBSERVE`. CNO requires closed reason/source data
and cannot coerce to Boolean. Every gate report declares whether nonempty
observations are required. Only PASS advances.

Trace storage and readers retain all three values. The old SQLite `passed`
column is a nullable compatibility projection, never an authority. Historical
Boolean negatives migrate to FAIL; historical positives and missing typed
fields migrate/project to CNO because their evidence sufficiency is unknown.

## Consequences

Empty or unavailable evidence no longer appears as a defect or a success. Gate
authors must construct `GateReport(nonempty_required=...)`; legacy return lists
are refused as CNO. Console and UI require a third rendering state. Existing
positive artifact and negative permission controls retain their bounded claims,
but this decision does not establish Git mutation/claim completeness.
