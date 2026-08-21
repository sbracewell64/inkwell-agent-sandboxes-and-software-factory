# LMCache — Self-Hosted Inference KV-Cache Research Reference

Status: `PRESERVE`
Planning owner: Browser Sol
Roadmap state: supporting research only; no FUT promotion
Activation condition: reconsider only if a self-hosted model-serving backend becomes a real SSSF / FirstMate / DSH candidate or measured self-hosted inference cost/latency becomes a project requirement.

## Preserved source

Repository: `LMCache/LMCache`
License: Apache-2.0
Reviewed branch: `dev`
Reviewed head: `1a430626ede5bfa5d49dbf7e00b964a7ebac02ee` (2026-08-21)

This record preserves LMCache as a future inference-infrastructure candidate. It does **not** authorize self-hosted GPU infrastructure, model-serving deployment, new paid compute, LMCache installation, or any roadmap change.

## Core interpretation

LMCache is a KV-cache management layer below the agent/harness layer. It does not provide agent memory, workflow state, semantic context, evidence, requirements, or acceptance authority.

Target placement if ever adopted:

```text
FirstMate / SSSF / DSH
        |
        | model request
        v
provider-neutral model backend
        |
        v
self-hosted serving engine (e.g. vLLM / SGLang / TRT-LLM)
        |
        +---- LMCache
        |       KV reuse only
        v
      model
```

Governing rule:

> Inference cache is a performance projection, not memory, evidence, or state authority.

KV reuse may change TTFT, throughput, GPU pressure, and compute consumed. It must not change requirement meaning, authority, accepted output semantics, evidence classification, workflow progression, or source custody.

## Why preserve it

LMCache is unusually relevant to long-running coding-agent workloads because multi-turn agent prompts repeatedly reuse large prefixes. Its published 2026 agentic-workload benchmark used anonymized Claude Code traces and reported substantial warm-cache TTFT/throughput benefits under high KV-memory pressure, while also showing that LMCache can add overhead when ordinary HBM prefix caching is already sufficient.

That conditional result is the correct framing for SSSF:

> LMCache is valuable only when repeated long-prefix workloads exceed effective GPU-resident KV capacity enough to justify an additional cache tier.

This should be measured on real SSSF/FirstMate/DSH replay workloads rather than inferred from synthetic cache-hit tests.

## Architecture findings

The current project direction favors multiprocess (MP) mode:

```text
vLLM instance(s)
       |
       v
ZMQ MessageQueueServer
       |
       v
MPCacheServer
       |
       +-- LookupModule
       +-- ManagementModule
       +-- transfer modules
       +-- optional P2P
       +-- optional CacheBlend
       |
       v
StorageManager
       |
       +-- L1 memory manager
       +-- L1/L2 eviction controllers
       +-- StoreController
       +-- PrefetchController
       +-- L2 adapters
       +-- quotas
```

MP mode is preferred for any serious future SSSF experiment because cache lifecycle/resource ownership is separated from the serving engine process, one cache can serve several engine instances, and the management/observability surface is explicit.

The cache key implementation already binds model identity, world size, worker identity, token-chunk hash, dtype, and optional `lmcache.tag.*` values. That tag mechanism is potentially useful for enforcing SSSF cache-isolation domains.

## SSSF security interpretation

KV tensors are derived from model inputs and may persist beyond the inference process. Treat them as **sensitive derived runtime state**, not harmless metadata.

If LMCache is ever admitted, CODE must mechanically own cache reuse policy, including at least:

- security / tenant / project domain;
- model and tokenizer generation;
- serving-engine and connector generation;
- cache runtime generation;
- retention / TTL;
- L1/L2 eligibility;
- remote storage/P2P eligibility;
- quota and deletion policy;
- encryption requirements where storage/network boundaries justify it.

Suggested future key scoping should consider bounded tags such as:

```text
lmcache.tag.security_domain
lmcache.tag.project
lmcache.tag.runtime_generation
```

Exact field names are not decided here.

Cache availability never implies cache authorization.

## Management-plane constraints

The recommended MP server exposes a FastAPI operator/admin surface alongside the ZMQ data plane. Current documentation includes operational endpoints for status, cache control, quotas, metrics, runtime reconfiguration, environment inspection, and a script-running endpoint.

If LMCache is ever qualified for SSSF:

- the HTTP management plane must not be reachable by untrusted DSH ExecutionCells;
- `/env` must not expose process secrets to agents;
- `/run_script` must not be available to agents or untrusted network peers;
- the admin plane should be loopback-only or otherwise protected by a tightly bounded management network/authentication layer;
- unrelated credentials should not be placed in the LMCache process environment;
- arbitrary LMCache runtime plugins must remain disabled unless independently qualified.

LMCache belongs in a trusted inference-service domain outside the ExecutionCell, not inside each worker sandbox.

## Telemetry constraint

LMCache includes a separate anonymous phone-home usage-telemetry subsystem. Its own documentation states that prompts, keys, and KV contents are not sent, but it transmits deployment/cache statistics and randomized machine/session identifiers.

Any SSSF-controlled runtime must explicitly disable this path, e.g. with the supported opt-out:

```text
LMCACHE_TRACK_USAGE=false
```

(or an equivalent qualified `DO_NOT_TRACK` setting).

Disabling phone-home telemetry should be part of effective runtime identity and a deterministic qualification check.

## Current multimodal blocker

The reviewed `dev` code still contains `hex_hash_to_int16()` in the vLLM multimodal integration. Non-hex multimodal identifiers are SHA-256 hashed and truncated to 16 bits before modifying placeholder token IDs used in cache-key computation.

GitHub issue `LMCache/LMCache#3301` reported that this can create collisions between distinct multimodal inputs and potentially return KV derived from the wrong image. That issue was closed automatically as stale rather than with a documented fix, while the 16-bit code path remained present at the reviewed head.

Ruling:

> Multimodal cross-user / cross-security-domain LMCache reuse is `UNPROVEN` and must not be admitted without a fresh end-to-end key-path review and collision-resistance evidence.

This record does not assert every current multimodal deployment is exploitable. It preserves the unresolved evidence and blocks silent qualification.

## Candidate recipe mapping

LMCache recipes are model-architecture validation pages, not SSSF workflow recipes. If a self-hosted serving candidate is later authorized, the following progression is currently the most reasonable starting point.

### Infrastructure smoke test

`Qwen/Qwen3-8B` using the generic LMCache + vLLM MP quickstart.

Purpose: prove cold/warm behavior, connector identity, cache hits, metrics, restart behavior, isolation, and teardown with a relatively small model.

### SSSF / DSH coding-worker experiment

`Qwen/Qwen3-Coder-30B-A3B-Instruct` with vLLM + LMCache MP.

Reason: the current Qwen3 recipe validates this coding model with tool-call parsing and shows a one-GPU configuration, making it substantially more practical than the 4–8 GPU examples for a first meaningful coding-agent experiment.

### FirstMate representative long-context stress experiment

`MiniMaxAI/MiniMax-M2.5` with vLLM + LMCache MP.

Reason: LMCache's published agentic benchmark used MiniMax-M2.5 against real Claude Code traces, making this the closest preserved workload analogue for a supervisory coding agent. It is not the preferred first infrastructure pilot because the documented serving configuration is materially heavier.

### DeepSeek-specific DSH backend experiment

`deepseek-ai/DeepSeek-V4-Flash` with vLLM + LMCache MP only if that model/backend independently becomes an admitted DSH model candidate.

The current recipe includes sparse-MLA KV handling and MTP speculative decoding qualification, and explicitly distinguishes score-level equivalence from token-bit-exact equivalence. DSH's use of DeepSeek Harness does not itself authorize or require a DeepSeek model.

### Multimodal

Do not qualify from this record. Revisit only after the multimodal cache-key/collision issue is independently resolved and re-tested.

## Required future qualification

If self-hosted inference becomes a real candidate, compare at least:

```text
A. no prefix caching
B. serving-engine native HBM prefix caching
C. HBM prefix caching + LMCache
D. HBM + LMCache under deliberately stressed KV working set
```

Use both synthetic control workloads and real replayable SSSF/FirstMate/DSH traces where privacy/authority permits.

Required measurements should include:

- TTFT p50/p95/p99;
- accepted-work throughput;
- GPU memory pressure;
- cache-hit ratio;
- HBM/DRAM/L2 bytes transferred;
- wall time;
- inference cost;
- failure/restart recovery;
- stale or wrong-cache events;
- cold-vs-warm semantic divergence;
- accepted value per unit compute.

The critical acceptance question is:

> Does warm-cache reuse preserve the accepted outcome quality of the cold baseline while materially improving a real bottleneck?

## Effective runtime identity

If LMCache is ever admitted, cache configuration is behaviorally material and must be captured alongside model/runtime identity. A future manifest should include at least:

```yaml
inference_runtime:
  model_weights: <exact digest>
  tokenizer: <exact generation>
  serving_engine: <exact generation>
  connector: <exact generation>
  lmcache:
    version_or_commit: <exact>
    deployment_mode: mp
    chunk_size: <exact>
    hash_algorithm: <exact>
    transfer_mode: <exact>
    cache_domain_policy: <exact>
    l1_policy: <exact>
    l2_policy: <exact>
    serde: <exact>
    retention: <exact>
    usage_telemetry: disabled
```

The exact schema is not decided by this research record.

## Non-decisions

This preservation does **not** authorize:

- installing LMCache;
- self-hosting any model;
- purchasing or renting GPUs;
- enabling a new paid inference provider/service;
- changing SSSF/FirstMate/DSH model routing;
- treating cache state as durable memory/evidence;
- enabling remote L2/P2P storage;
- exposing LMCache management APIs to agents;
- enabling anonymous usage telemetry;
- production multimodal KV reuse;
- adding a new FUT candidate or changing roadmap order.

Any new monetary expenditure remains Captain authority.

## Activation condition

Re-open this research when either condition becomes true:

1. a self-hosted model-serving backend is proposed for `CANDIDATE` consideration for SSSF, FirstMate, or DSH; or
2. measured inference latency/cost/capacity creates a concrete requirement that self-hosting may address.

At that time Browser Sol should:

1. re-review the then-current LMCache head, roadmap, releases, security issues, recipes, and serving-engine integrations;
2. verify whether MP remains the preferred architecture;
3. verify the multimodal key path and all relevant security/advisory status;
4. compare LMCache against engine-native caching and current alternatives;
5. identify the exact candidate model/engine/hardware/runtime generation;
6. require Captain approval before any new paid compute or materially new infrastructure expenditure;
7. promote through the normal planning lifecycle only if a real requirement and qualification path exist.

Governing principle:

> Preserve the optimization option now; decide on the infrastructure only when an actual self-hosted inference requirement exists.
