# FUT-004 — LLM-as-a-Verifier research source

State: `PRESERVE`

Repository:

`https://github.com/llm-as-a-verifier/llm-as-a-verifier.git`

Observed upstream `main` on 2026-08-18:

`115de305f23ed89bc42e86e010853c40059f3f7d`

Paper:

`arXiv:2607.05391`, *LLM-as-a-Verifier*.

Purpose: preserve this project as a future post-DSH research source for probabilistic trajectory scoring, progress estimation, best-of-N selection, criteria decomposition, efficient pairwise ranking, verifier usage accounting, and related ideas.

This is not an SSSF dependency, allowlist, installation request, or production endorsement. Before any derived candidate is implemented, inspect the then-current upstream separately and record its exact source identity.

Detailed SSSF mapping and the four promoted candidates are recorded in [`VERIFIER_DSH_RESEARCH.md`](VERIFIER_DSH_RESEARCH.md):

- FUT-005 — verifier-guided DSH progress and refinement (`CANDIDATE`)
- FUT-006 — best-of-N DSH candidate selection (`CANDIDATE`)
- FUT-007 — typed criteria decomposition for inner semantic evaluation (`CANDIDATE`)
- FUT-008 — hierarchical probabilistic-verifier evidence and cost telemetry (`CANDIDATE`)

All four are gated behind the DSH execution-cell architecture and remain unsequenced. Probabilistic verifier output is advisory inner-cell evidence only and cannot override deterministic verification, maker/checker requirements, or SSSF acceptance authority.

TurboAgent is retained only as a research/transparency reference. Its transparent inference-proxy topology is not the target SSSF integration: generation, verification, selection, and refinement should remain attributable inner execution units.
