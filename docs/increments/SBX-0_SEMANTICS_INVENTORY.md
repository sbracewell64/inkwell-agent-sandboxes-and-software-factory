# SBX-0 — provider-neutral semantics handoff publication

**Status:** published handoff candidate; CNO for SBX-0 exit and every promotion
**Starts from:** `b902cdcecd65c8ba03031875297d31e990f12c11`
**Ruling:** `SOL-FM-SSSF-SBX1-POSTMERGE-20260820-1203`
**Planning source examined by the scout:** `origin/planning/future-sssf` at `54ef67c3849b24b1eaa6e10d2ed0e49a09464a70`
**Durable inventory:** [`docs/reference/SBX-0_SEMANTICS_INVENTORY.json`](../reference/SBX-0_SEMANTICS_INVENTORY.json)
**Validator:** [`docs/validation/check_sbx0_inventory.py`](../validation/check_sbx0_inventory.py)

## Intent and boundary

This increment publishes the complete SBX-0 classification inventory as an
inspectable, exact handoff for SBX-1. It does not copy the mutable scout report
into the repository and does not make that path a control-plane authority.
The JSON inventory is the sole durable SBX-0 handoff record; it is not a second
runtime lifecycle store, evidence database, process supervisor, scheduler, or
architecture owner.

The publication records the source report's facts, evidence pointers,
classifications, three-valued observations, obligations, unresolved contract
questions, and Docker-qualification limits. It also records the current SSSF
main and planning identities separately, so a source-generation observation is
not silently rewritten as current acceptance evidence.

## Exact source and current reconciliation

The mutable fleet-local input was read completely before publication:

- logical path: `data/sssf-sbx-0/report.md`;
- source generation: `sbx-0-report/v1@code-bee9296a4c94b1dc3da6991acd1755a91fa681eb@planning-54ef67c3849b24b1eaa6e10d2ed0e49a09464a70`;
- content SHA-256: `2d16bee3db4c46062b460dfbd6752339e85228a3b6f2c5002313a4f06dc663b3`;
- size: `42031` bytes and `221` lines;
- examined canonical code: `bee9296a4c94b1dc3da6991acd1755a91fa681eb`;
- examined planning commit: `54ef67c3849b24b1eaa6e10d2ed0e49a09464a70`;
- current SSSF handoff base: `b902cdcecd65c8ba03031875297d31e990f12c11`.

The inventory content digest (computed with its digest field blank) is
`bce21bc40de2f94cb03b464e1baa3ccb94d6dedf25825588947d94663a6b5a52`.
The mutable report remains an evidence input. If it is absent or unreadable,
source replay is CNO; the durable inventory does not infer PASS from that
absence.

The current `SandboxProvider` contract at the exact starting main is recorded
as a contract/fake binding only. SBX-1 activation, acceptance, real provider
custody, Windows host observation, independent semantic review, landing
authorization, and SBX-2 unlock remain CNO in the durable identity.

## Inventory coverage

The handoff contains:

- 57 classified source facts, including all report classifications;
- 33 explicit SBX-1/publication obligations;
- 33 deferred items: 16 unresolved contract ambiguities and 17 Docker
  qualification boundaries; and
- 8 source recommendations retained as non-promoting recommendations.

The source classifications are preserved as:

- `provider-neutral-semantic`;
- `exe.dev/provider-mechanism`;
- `limitation`;
- `obsolete-artifact`;
- `external-dependency`; and
- `could-not-observe`.

Every fact and obligation has exactly one `owner_id`. Current owners are
reused rather than duplicated:

| Owner | Authority |
|---|---|
| `sandbox-contract` | `adws/adw_modules/sandbox_provider.py` |
| `process-supervisor` | `adws/adw_modules/subprocess_supervisor.py` |
| `evidence-manifest` | `tools/evidence_manifest.py` |
| `gate-outcome` | `adws/adw_modules/data_types.py` |
| `source-custody` | `just/sandbox/lifecycle/fill.just` |
| `legacy-exedev-lifecycle` | historical `just/sandbox/lifecycle/` mechanisms only |
| `observability-trace` | `adws/adw_modules/tracer.py` |
| `security-boundary` | `docs/architecture/SECURITY_AND_CREDENTIALS.md` |
| `agent-backend` | `adws/adw_modules/agents.py` |
| `planning-contract` | `docs/development/ROADMAP.md` |
| `source-of-truth-policy` | `docs/reference/SOURCE_OF_TRUTH.md` |
| `verification-controls` | this increment's deterministic validator |
| `sbx0-handoff-record` | this durable inventory and its publication boundary |

The handoff-record and verification owners govern the publication artifact and
its checks only. They do not own lifecycle semantics or acceptance.

## Observation rules

The inventory retains source observations and current contract observations as
separate fields. Each uses exactly `observed-good`, `observed-bad`, or
`could-not-observe`. Provider qualification is explicitly CNO for every source
fact and obligation because this increment performs no live provider or host
observation.

Missing, empty, unreadable, unavailable, interrupted, ambiguous, over-bound, or
unverified evidence remains CNO. A positive contradiction remains
`observed-bad`. No CNO is projected to `absent`, `PASS`, activation, acceptance,
or promotion.

## Deterministic proof and watched-red controls

Run the provider-free publication check with:

```text
python3 docs/validation/check_sbx0_inventory.py
python3 docs/validation/check_sbx0_inventory.py \
  --source-report /path/to/data/sssf-sbx-0/report.md
```

The optional replay verifies the mutable input's exact digest and reports a
missing/unreadable input as CNO. The default check validates the durable
identity without requiring that mutable path to exist.

The validator positively checks the report's command observations, exact source
generation/content digest, coverage, owner paths, classification projection,
and three-valued boundaries. It is included in the existing non-vacuous
`ci/checks.json` owner; no new scheduler or evidence store is introduced. It
also mutates in-memory copies and requires red results for:

- stale source generation;
- source content-digest mismatch;
- duplicate authority;
- dropped fact;
- dropped obligation; and
- CNO narrowed to absence or PASS.

No Docker, exe.dev, provider, model, browser, network, credential, Windows
host, Wayfinder, DSH, or irreversible environment action is part of this proof.

## Acceptance boundary

This increment proves publication integrity and an inspectable SBX-1 handoff
identity only. It does **not** establish SBX-0 exit, SBX-1 activation or
acceptance, real Docker/provider custody, Windows host observation, independent
semantic review, landing authorization, or SBX-2 unlock. Work on SBX-2,
Wayfinder, and DSH is explicitly out of scope.
