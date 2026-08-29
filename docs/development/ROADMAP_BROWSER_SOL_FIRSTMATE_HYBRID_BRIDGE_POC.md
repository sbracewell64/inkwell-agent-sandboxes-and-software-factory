# Roadmap Amendment — Browser Sol ↔ FirstMate Hybrid Evidence Bridge POC

**Status:** `PLANNING_ONLY`

**Captain authorization:** 2026-08-29

**Purpose:** evaluate whether the strongest mechanism from `XiaoDuoYa/codex-with-chatgpt` can improve Browser Sol ↔ FirstMate communication by adding secure direct read-only local evidence access plus tiny structured synchronous messages, while retaining `sbracewell64/firstmate-sol-control` as the durable authority/event-history plane.

This amendment does **not** authorize installation, tunnel exposure, credential changes, replacement of `firstmate-sol-control`, a new authority writer, or production use of the upstream repository. It registers a structured future experiment whose execution is gated on Praxist maturation measurement being operational and the relevant Compound Engineering planning/operational work being implemented and qualified.

## Captain-authorized target principle

The experiment must preserve this split:

```text
Direct bridge
  = speed + live/read-only evidence + compact synchronous dialogue

GitHub firstmate-sol-control
  = durable authority + canonical writer + asynchronous governance + history
```

The upstream repository is classified for this purpose as:

> **High-value architecture reference + potentially useful read-only evidence substrate; not a direct replacement for `firstmate-sol-control`.**

The mechanism of interest is:

```text
secure direct Browser Sol → local workspace read access
+
tiny structured synchronous messages
```

The mechanism explicitly retained from the current architecture is:

```text
GitHub durable authority/event history
+
canonical Browser Sol writer
+
asynchronous governance
```

## Sequencing gates

This experiment is deliberately **after** the maturation/evaluation substrate, so the communication change can itself be measured rather than adopted on intuition.

Required sequence:

```text
Praxist maturation POC / accepted maturation-measurement method becomes operational
        ↓
REF-1 + longitudinal SSSF tracking operational enough to measure the change
        ↓
Compound Engineering prerequisite dossier/control #43 complete
        ↓
relevant CE plan/transfer work from control #41 and operational CE capability from control #42 implemented and qualified sufficiently for FirstMate to use CE methods autonomously
        ↓
CE plan used to design the hybrid bridge experiment
        ↓
HYBRID-BRIDGE-POC — sandboxed controlled comparison
        ↓
Praxist/REF-1/longitudinal evidence + FirstMate comparison
        ↓
retain / revise / reject / promote through normal governance
```

The exact CE prerequisite is the minimum accepted generation that makes the relevant CE planning method available to FirstMate without creating another workflow authority. This roadmap item must consume controls #41/#42/#43 rather than duplicate their source review or CE integration work.

Praxist does not become an authority prerequisite; it is the intended measurement instrument. If the accepted maturation architecture ultimately chooses `BORROW_METHODS_ONLY` instead of runtime Praxist, the equivalent accepted evidence/longitudinal method may satisfy this gate. The requirement is **operational evidence-based comparison capability**, not attachment to one tool.

## Baseline and candidate architectures

### Arm A — current durable GitHub-only control path

```text
FirstMate
   ↕
firstmate-sol-control
   ↕
Browser Sol
```

Measure the current workflow as it actually exists at the exact accepted generation.

### Arm B — hybrid communication path

```text
                         Browser Sol
                        /           \
                       /             \
       durable authority              live evidence / dialogue
              |                               |
              v                               v
   firstmate-sol-control              read-only bridge
              |                               |
              +----------- FirstMate ---------+
                              |
                             SSSF
```

The bridge may accelerate evidence inspection and non-authority dialogue. Authority-bearing results remain durable through the existing canonical control-plane writer unless a later separately authorized architecture changes that rule.

## CE-plan requirement

Once Compound Engineering is implemented and qualified for FirstMate, FirstMate should use the accepted **CE planning method** to design this POC rather than improvising the experiment ad hoc.

The CE plan should at minimum:

- reobserve exact current `XiaoDuoYa/codex-with-chatgpt` source/release before implementation;
- map the upstream architecture to current FirstMate/control-plane owners;
- identify the smallest transplant/adaptation rather than install the upstream stack wholesale by default;
- define sandbox/network/OAuth/tunnel/workspace/credential boundaries;
- define exact typed message semantics and transport ownership;
- preserve canonical-writer singleton authority;
- define rollback before activation;
- define baseline/candidate experiment arms and controlled variables;
- define positive and watched-red fixtures;
- identify what existing GitHub evidence-shuttling machinery can be simplified or removed if the hybrid succeeds;
- preserve the SSSF simplification hierarchy.

CE planning remains subordinate to Captain/FirstMate/SSSF security, privacy, cost, authority, verification, and landing laws.

## Communication semantic layer

Transport should not become semantic authority. FirstMate should evaluate a compact transport-neutral envelope such as:

```text
ControlEnvelope
  correlation_id
  sender
  recipient
  kind
  generation
  project
  exact_subject
  evidence_refs
  authority_class
  payload
```

Candidate message kinds may include:

- `REQUEST`
- `OBSERVATION`
- `EVIDENCE_READY`
- `REVIEW`
- `RULING_REQUIRED`
- `RULING_AVAILABLE`
- `EXECUTION_UPDATE`
- `BLOCKED`
- `DONE`

These names are planning examples, not a registered runtime protocol.

The design objective is:

> **Transport may be interchangeable; authority persistence is not.**

Non-authority dialogue/evidence pointers may use the direct bridge when available. Authority-bearing Browser Sol/Captain decisions must continue to acquire canonical durable lineage through the accepted control-plane owner before FirstMate treats them as authoritative.

## Read-only evidence boundary

The strongest upstream property to preserve is that Browser Sol can inspect local evidence without receiving execution authority.

Initial scope should remain read-only and may include equivalent capabilities for:

- workspace identity;
- directory/file reads with bounded pagination;
- workspace search;
- git status;
- git diff;
- SSSF/FirstMate execution/evidence summaries;
- exact local branch/worktree/head identity;
- selected test/verification evidence **from canonical SSSF/FirstMate evidence owners**.

Do not treat an untyped local `tests: "passed"` summary or worker prose as authoritative verification. The hybrid must expose or reference the stronger existing typed verification/evidence owners rather than downgrade SSSF evidence semantics.

## Security / sandbox requirement

The POC must use qualified sandbox custody and must not expose writable canonical source or durable authority credentials to the bridge experiment.

Before any runtime POC, FirstMate must define and prove:

- exact workspace boundary and canonical path containment;
- sensitive-file deny policy;
- no shell/write/delete/commit/landing tools exposed to Browser Sol;
- no host control-plane credentials or auth homes visible through the bridge;
- no protected-ref mutation capability;
- exact OAuth/token/pairing lifecycle if the upstream mechanism is reused;
- tunnel/public-ingress risk and whether a safer qualified transport can preserve the same semantics;
- network policy and revocation;
- bridge teardown and proof of quiescence;
- bounded logs/state retention;
- exact upstream/source identity;
- no new paid service or spend without Captain authority.

The upstream Cloudflare Quick Tunnel is **not automatically accepted**. FirstMate should compare reuse, adaptation, and safer equivalent transports under the simplification/security laws.

## Evidence and comparison objectives

Praxist/REF-1/accepted longitudinal measurement should compare Arm A and Arm B on at least:

### Communication efficiency

- time from local evidence becoming available to Browser Sol inspection;
- number of GitHub comments/issues required per representative task;
- duplicated evidence/summaries transmitted;
- number of round trips to obtain missing local facts;
- stale-state incidents;
- Browser Sol decision latency;
- FirstMate waiting time attributable to evidence transport.

### Autonomy / operator burden

- Captain interventions;
- manual copy/paste or relay actions;
- recoverability after FirstMate/Browser session restart;
- ability to continue asynchronously when one side is unavailable.

### Evidence quality

- exact-head/worktree/source visibility;
- ability to inspect unpublished local work;
- typed verification/evidence availability;
- CNO rate caused by missing evidence;
- provenance/attribution clarity;
- audit reconstruction quality.

### Governance / safety

- canonical-writer singleton preserved;
- no sibling authority generations;
- authority-bearing direct messages cannot become effective without durable canonical lineage;
- maker/checker and independent review preserved;
- security/privacy/credential boundaries preserved;
- rollback and teardown proven.

### Complexity

- added persistent processes/services;
- configuration/operator concepts;
- external dependencies;
- maintenance burden;
- failure/recovery paths;
- state stores introduced;
- code/prose/control machinery eliminated or simplified in exchange.

## Praxist / longitudinal tracking requirement

This experiment must appear as a distinct longitudinal SSSF/FirstMate maturation generation once executed.

The comparison record should preserve at least:

- exact baseline FirstMate/control/SSSF generations;
- exact hybrid candidate generation;
- exact bridge upstream/adapted source identity;
- exact CE plan generation used;
- exact Praxist/measurement generation;
- controlled variables and attribution limitations;
- communication/evidence metrics above;
- safety and authority results;
- operator burden;
- final disposition.

No single latency/token metric may override an authority, correctness, security, provenance, maker/checker, or recoverability regression.

## Required dispositions

After the POC, FirstMate should recommend one of:

- `RETAIN_GITHUB_ONLY`
- `ADOPT_HYBRID_READ_ONLY_EVIDENCE`
- `ADOPT_HYBRID_EVIDENCE_AND_NONAUTH_DIALOGUE`
- `BORROW_PROTOCOL_METHODS_ONLY`
- `CNO_MORE_EVIDENCE_REQUIRED`

A direct replacement of `firstmate-sol-control` is **not an authorized outcome of this POC**. Any future proposal to remove the durable GitHub authority plane requires a separate Captain-authorized architecture decision supported by the POC evidence.

## Positive fixtures

Qualification should include at least:

1. Browser Sol inspects an unpublished local diff directly while FirstMate retains all write authority.
2. Browser Sol inspects exact local head/worktree identity and canonical verification evidence without a large GitHub evidence paste.
3. A non-authority dialogue round trip occurs over the direct channel and is correlated to the same durable work identity.
4. An authority-required condition causes durable canonical control-plane routing rather than direct-message authority activation.
5. Restart/reconnect preserves or reconstructs enough correlation state to continue safely.
6. Bridge teardown removes live access and leaves no unauthorized surviving process or token path.

## Watched-red fixtures

The experiment must fail/refuse when:

- Browser Sol is offered a write/shell/commit/merge/landing tool;
- a direct Browser Sol message is treated as authoritative without the required canonical durable lineage;
- the bridge exposes `.env`, credentials, auth homes, control tokens, or protected secrets;
- a workspace/path/symlink escape succeeds;
- local worker prose or an untyped `tests passed` field is promoted over canonical typed evidence;
- the direct path creates a second Browser Sol authority writer;
- a restart produces duplicate/sibling authority generations;
- a stale local observation overrides newer canonical state;
- public/tunnel ingress remains active after teardown;
- the hybrid adds more durable state/schedulers/control concepts than it demonstrably removes or improves.

## Simplification law

The hybrid survives only if it makes the overall system easier to understand or materially more effective without weakening governance.

Preferred result if successful:

```text
GitHub carries durable decisions and asynchronous history.
Direct bridge carries live evidence and fast non-authority dialogue.
SSSF/FirstMate remain execution/evidence owners.
Browser Sol remains architecture/review authority through the canonical writer.
```

Do not create a second planner, scheduler, workflow engine, verification authority, or state database to support the bridge.

## Relationship to Compound Engineering controls

Consume rather than duplicate:

- **control #43** — comprehensive CE upstream dossier prerequisite;
- **control #41** — FirstMate + SSSF CE transfer architecture;
- **control #42** — FirstMate operational CE integration and method-selection capability.

The hybrid bridge POC should use the accepted CE planning capability after those controls have produced and implemented the relevant qualified owner. It must not serialize their earlier dependency-safe planning work and must not cause a second CE integration path.

## Roadmap effect

This item is **SEQUENCED FOR FUTURE EVALUATION, NOT ACTIVE**.

It sits after operational maturation measurement and qualified CE planning capability. It does not alter the existing Docker/REF-1/Wayfinder/DSH hard prerequisites except where those accepted capabilities are required to provide sandbox custody or longitudinal measurement for this POC.

**Default until all gates are met:** retain the current GitHub control plane unchanged and use the upstream repository only as an architecture reference.
