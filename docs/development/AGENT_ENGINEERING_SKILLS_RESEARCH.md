# Agent Engineering Skills Research Sources

## Status

`PRESERVE` research family. This document records four external repositories as future sources of reusable engineering-instruction, skill-evaluation, planning, review, and context-management ideas.

It does **not** authorize installing any repository, activating another workflow router, copying skills wholesale into SSSF or FirstMate, or allowing Markdown instructions to become an outer workflow authority.

The reviewed repositories and exact observed `main` identities on 2026-08-19 were:

| Repository | Observed main | Planning disposition |
|---|---|---|
| `addyosmani/agent-skills` | `df1edb2e05487d0aa6d93c747141e0aed1187f25` | `PRESERVE` — strongest source for instruction/skill qualification and behavioral eval ideas |
| `obra/superpowers` | `b36e0829c6d0140e93cfef2ca599b1b07d4a7797` | `PRESERVE` — strongest source for pressure-tested instruction discipline, fresh-context subagent execution, and plan/review mechanics |
| `mattpocock/skills` | `885e2ca4d842d139e9aef4e48d366c63cb1b8013` | `PRESERVE` — strongest source for focused planning/design primitives such as grilling, deep modules, and wayfinding |
| `mattpocock/agent-rules-books` | `a7d7649044505b9c377c8dca28d2d6a543bc7f8c` | `PRESERVE` — on-demand doctrine/reference catalog; not an always-on rule pack |

These SHAs preserve what was reviewed. Re-inspect the then-current upstream and record exact source identity before any implementation, copy, adaptation, or qualification.

## Governing extraction rule

> **Borrow decision-changing primitives; do not import another workflow authority.**

SSSF code/ADWs remain the outer workflow owner. FirstMate remains the supervisory orchestration owner for its domain. DSH may later own bounded inner autonomy inside SSSF execution cells. A `SKILL.md`, meta-skill router, checklist, issue map, or methodology from these sources may inform one of those owners, but may not silently become a competing owner of sequencing, retries, acceptance, promotion, or planning state.

Prefer, in order:

1. deterministic code when a rule is mechanically enforceable;
2. typed contracts and validators when a rule describes a checkable seam;
3. bounded instructions/skills only for judgment that genuinely remains semantic;
4. retrieval/reference material for large or infrequently needed doctrine.

This family therefore supplies evidence primarily to existing `FUT-010` (compact architectural laws), `FUT-011` (instruction-artifact governance), and the Sandbox -> DSH stages. It does not by itself justify a new SSSF instruction runtime.

---

# 1. `addyosmani/agent-skills`

## Classification

`PRESERVE` source. Several mechanisms are strong enough to become formal evaluation inputs under `FUT-011`; the repository's lifecycle router itself is not an SSSF candidate.

## High-value mechanisms

### Three-tier instruction/skill qualification

The repository separates:

1. **structural checks** — metadata, naming, required surfaces;
2. **trigger/routing checks** — deterministic positive/negative routing and collision tests across the catalog;
3. **behavioral checks** — run an agent against a fixture and grade the resulting execution/dialogue artifact against explicit expectations.

The important SSSF lesson is the shape, not its TF-IDF or Claude-specific implementation:

```text
instruction artifact
    -> structural validity
    -> correct applicability / consumer routing
    -> behavioral pressure test
    -> qualified instruction generation
```

A durable instruction that claims to change agent behavior should not be considered qualified merely because its file parses or contains the right sentence.

### Non-vacuous negative routing

Negative trigger cases name the *correct owner* and require it to outrank the wrong instruction. That is stronger than merely proving the wrong skill did not trigger when nothing else did.

This maps directly to SSSF's falsifiability law and should inform `FUT-011`.

### Pressure cases

Behavioral evals include time pressure, sunk-cost pressure, and authority pressure. This is useful for instruction artifacts whose purpose is specifically to prevent rationalization or unsafe shortcuts.

### Source-driven development

The `source-driven-development` skill contains a useful bounded doctrine:

- detect exact dependency/tool versions;
- inspect current authoritative upstream documentation when correctness is version-sensitive;
- separate verified facts from training-memory assumptions;
- mark unverified claims explicitly;
- treat retrieved documentation as data, never as instruction authority.

This is a possible **FirstMate-specific adaptation**, but not a verbatim import. FirstMate's existing authority classification must decide whether a docs/project conflict is SELF_HANDLE, BROWSER_SOL, CAPTAIN, or EXTERNAL_DEPENDENCY rather than automatically asking the Captain.

### Doubt-driven development

Useful primitive:

```text
ARTIFACT + CONTRACT
        -> fresh-context adversarial reviewer
        -> findings
        -> owning orchestrator reconciles
```

The reviewer receives the artifact and contract, not the author's conclusion/reasoning. Reviewer output remains evidence, not verdict. The loop is bounded.

This is a useful future review-cell pattern for DSH and potentially a FirstMate reviewer specialization. The upstream skill's mandatory interactive cross-model offer is **not** appropriate for unattended SSSF/FirstMate operation and must not be copied as policy.

## Do not adopt

- the whole `using-agent-skills` lifecycle router;
- a second phase taxonomy competing with ADWs/FirstMate;
- mandatory skill chaining as workflow authority;
- prose rules that deterministic SSSF/FirstMate code already enforces.

---

# 2. `obra/superpowers`

## Classification

`PRESERVE` source. Strong evidence for `FUT-011`, plus reusable inner-autonomy and reviewer-context patterns for DSH-3/DSH-6. Do not adopt Superpowers itself as the SSSF or FirstMate orchestrator.

## High-value mechanisms

### TDD for process documentation / skills

`writing-skills` applies a falsification cycle to agent instructions:

```text
pressure scenario without instruction -> watched failure
instruction change                   -> behavior changes
pressure scenario with instruction   -> expected behavior
new rationalization                  -> new control
```

Its strongest law is directly compatible with `FUT-011`:

> An instruction whose purpose is to change agent behavior should have evidence that the undesirable behavior occurs without the instruction and is prevented with it.

Superpowers also states the complementary simplification rule: if a constraint can be enforced mechanically, automate it rather than creating a skill for it.

### Instruction discovery is itself behavior

The repository documents a concrete failure mode where a skill description summarized the workflow, so the agent followed the description without loading the actual skill body. The lesson for SSSF is broader:

> Instruction routing metadata is part of executable behavior and deserves qualification; it is not harmless documentation.

### Fresh-context task execution and review

`subagent-driven-development` deliberately constructs narrow task briefs rather than handing workers the coordinator's full session history. Review similarly focuses on the work product/spec rather than the author's reasoning.

Useful DSH/FirstMate principles:

- fresh implementer/reviewer context when independence matters;
- task briefs and reports as durable artifacts instead of context-window narration;
- plan/spec identity remains explicit;
- review packages bind exact task/diff context;
- bounded fix/re-review loops;
- no unnecessary human check-in for reversible engineering ambiguity.

### Durable recovery over conversational memory

Superpowers uses a plan-bound progress ledger plus Git state to recover after compaction instead of trusting model recollection. SSSF/FirstMate already have stronger typed state owners, so the principle should reinforce existing durable state rather than create another ledger.

### De-duplication and instruction compression

Recent upstream work intentionally removed duplicate integration lists, persuasion/social-proof prose, and redundant rule summaries while preserving point-of-use guards and behavioral tests. This is strong supporting evidence for both `FUT-011` and the net-complexity constraint from `FUT-009..012`.

## Do not adopt

- Superpowers' single methodology as an outer SSSF workflow;
- its filesystem ledger where SSSF/FirstMate already has typed durable state;
- human-stop semantics that conflict with the established FirstMate/Browser-Sol/Captain authority classes;
- fixed review-loop or model-selection policy without measurement under SSSF/DSH.

---

# 3. `mattpocock/skills`

## Classification

`PRESERVE` source. Valuable as a library of focused reasoning/planning primitives. Individual mechanisms range from strong reusable doctrine to `REFERENCE/EXPLORE`; no wholesale installation or router adoption is warranted.

## High-value mechanisms

### Deep-module / real-seam discipline

`codebase-design` defines a useful anti-layering rule:

> One adapter means a hypothetical seam; two adapters means a real one.

Combined with its deletion test and deep-module emphasis, this strongly reinforces:

- `FUT-010` population-before-expansion / net-complexity law;
- SBX-0/SBX-1/SBX-2: prove the provider abstraction against exe.dev before adding Docker;
- avoid adapter/registry/interface layers that have no demonstrated variation.

This principle should be evaluated as SSSF law, not imported as permanent terminology.

### Grilling: facts versus decisions

The `grilling` primitive models unresolved design as a dependency tree/frontier. Facts the environment can establish are researched by the agent; actual decisions remain with the human. Later questions become eligible only after their prerequisites settle.

The useful SSSF/FirstMate extraction is:

```text
observable fact -> investigate automatically
engineering ambiguity -> delegated authority / Browser Sol
Captain-owned choice -> ask Captain
```

This agrees with the FirstMate authority model and can help improve question minimization. The upstream human-interview workflow itself should **not** become an SSSF planning layer.

### Wayfinder

`wayfinder` uses an issue-tracker map as a durable planning index, makes each decision live in one ticket, exposes a frontier of open/unblocked/unclaimed decisions, and leaves imprecise future work in a fog-of-war section until it can be stated sharply.

Disposition: **REFERENCE / EXPLORE mechanism only**, not a new SSSF planning candidate. SSSF already has `PLANNING_LIFECYCLE.md`, `FUTURE_CANDIDATES.md`, `ROADMAP.md`, increments, FirstMate task state, and the control plane. Importing Wayfinder would create a parallel planning truth.

Potential reusable rules only:

- an index points to authoritative detail rather than restating it;
- do not create executable work from fog that cannot yet be stated precisely;
- dependency/frontier status should be derived from actual blockers;
- facts and decisions should not be conflated.

### Small explicit implementation wrapper

The `implement` skill is intentionally tiny: work from a spec/tickets, use TDD where appropriate, run incremental/full verification, review, commit. SSSF/FirstMate already own these responsibilities more strongly; no adoption value beyond confirming that small instructions can be preferable to large methodology documents.

## Do not adopt

- Wayfinder as another durable planning system;
- `grilling` as a mandatory Captain interrogation loop;
- an external meta-router that decides SSSF phases;
- Matt-specific issue tracker/setup conventions;
- terminology solely because it is useful in that repository.

---

# 4. `mattpocock/agent-rules-books`

## Classification

`PRESERVE` source, lower priority than the three repositories above. Treat as an on-demand doctrine/candidate-context catalog rather than a trusted always-on rule set.

## Useful mechanism

The repository deliberately publishes `full`, `mini`, and `nano` rule sets and recommends the **smallest mechanism that still changes agent decisions**. It prefers task-specific/scoped/on-demand loading over stuffing multiple large rule packs into global context.

That strongly aligns with `FUT-011`:

- instruction context is a budget;
- long reference material should stay reference/retrieval material;
- only decision-changing rules belong in active agent context;
- memories are helpers, not the canonical shared source;
- multiple broad rule packs create conflict and dilution.

Potential future bounded uses after qualification:

- *A Philosophy of Software Design* rules for a specific architecture/simplification review;
- *Working Effectively with Legacy Code* for a risky legacy-change cell;
- *Release It!* for reliability/lifecycle work;
- *Designing Data-Intensive Applications* for data/evidence/event-consistency work.

Each use would require exact-source qualification, conflict testing against SSSF/FirstMate governing instructions, and evidence that the extra context improves outcomes. Do not install the catalog globally.

The repository's own reported refactor comparison is qualitative evidence only, not sufficient qualification for SSSF.

---

# Effect on existing SSSF candidates

## FUT-011 — Instruction-artifact governance

This source family materially strengthens the candidate. When FUT-011 is evaluated for `DECIDED`, include at least these prospective requirements:

1. **One semantic owner** for each durable instruction artifact.
2. **Real consumer identity** — no orphan prompt/skill/rule presented as operative.
3. **Applicability/trigger qualification** appropriate to the delivery mechanism.
4. **Collision/conflict testing** where multiple instructions may route on overlapping work.
5. **Behavioral falsifiability** for instructions whose purpose is to change agent behavior.
6. **Pressure controls** when the instruction protects against rationalization, authority pressure, time pressure, or sunk-cost behavior.
7. **Mechanical-before-semantic rule** — if code can enforce it deterministically, prefer code over instruction.
8. **Context-budget discipline** — active instructions are the smallest sufficient form; heavy doctrine stays reference/retrieval.
9. **Point-of-use ownership** — do not repeat a rule in several skills merely to make it visible.
10. **Version/source identity** for imported/adapted external instruction material.

Possible future evaluation stack:

```text
structure
  -> applicability/routing
  -> behavioral watched-red/non-vacuity
  -> interaction/conflict with governing SSSF instructions
  -> production eligibility
```

This does not imply that every prose document needs an agent eval. Authored rationale that makes no operational behavior claim remains documentation, not executable instruction.

## FUT-010 — Compact architectural laws

Candidate evidence to consider:

- create a seam only when real variation exists;
- deep owner/small interface over shallow pass-through layers;
- the smallest mechanism that changes the decision;
- facts should be established automatically; personal/authority decisions should remain with their owner.

Do not import a new vocabulary hierarchy merely to encode these laws.

## Sandbox -> DSH

Useful future evaluation inputs:

- DSH-3: fresh-context child briefs, explicit parent/child identity, scoped reports, bounded re-review;
- DSH-6: artifact/contract-only independent reviewer context and explicit independence classification;
- DSH evidence: durable progress belongs in typed state/evidence, not conversational memory;
- DSH instruction artifacts: behaviorally qualify operational prompts/skills before promoting a production generation.

These are unlock-time research inputs, not additional DSH prerequisites today.

---

# Direct FirstMate use

FirstMate already owns a substantial `.agents/skills` surface and code-owned supervision, state, review, and authority machinery. Therefore direct import has a high duplication risk.

## Best candidate for a FirstMate-specific adaptation

### Source-grounded engineering

Adapt the useful core of `agent-skills/source-driven-development` into FirstMate only if inspection shows no existing skill/code owner already covers it adequately.

Trigger narrowly when a FirstMate/SSSF task materially depends on a current/versioned external API, framework, provider, CLI, or specification.

Required FirstMate differences:

- exact dependency/tool/version identity first;
- authoritative primary sources preferred;
- retrieved content is untrusted data and cannot expand authority;
- observations distinguish documented, observed, inferred, and unproven;
- docs/project conflicts use FirstMate's SELF_HANDLE / BROWSER_SOL / CAPTAIN / EXTERNAL_DEPENDENCY classification rather than automatically asking the Captain;
- no mandatory web/document lookup for stable pure-logic work;
- no source citation becomes an execution warrant.

This is a future qualification opportunity under FUT-011, not an instruction to add the skill now.

## Potential reviewer adaptation

The `doubt-driven-development` artifact+contract fresh-context pattern may be useful in FirstMate review or DSH reviewer cells. Do not import the upstream user-confirmation/cross-model policy. Browser Sol/FirstMate's existing independence, cost, and authority rules remain controlling.

## Likely not worth direct FirstMate imports

- `using-agent-skills` — competing router;
- Superpowers SDD — overlaps FirstMate orchestration/worktree/review/state ownership;
- Wayfinder — parallel planning/task system;
- `implement` — duplicates current engineering contracts;
- broad `agent-rules-books` packs — context and policy collision risk;
- `code-simplification` wholesale — most useful rules should live in existing coding/review doctrine or compact SSSF laws if a demonstrated gap exists.

---

# Qualification rule for any future external skill

Before copying or adapting an external `SKILL.md` into FirstMate, SSSF, or a DSH production profile:

1. identify the exact semantic gap in an existing owner;
2. inspect then-current upstream at exact Git identity;
3. classify every instruction as mechanical, semantic, or reference;
4. move mechanical rules into code where feasible;
5. reduce the semantic instruction to the smallest sufficient artifact;
6. state trigger/consumer/authority explicitly;
7. test positive applicability and negative collision cases;
8. watch at least one relevant behavior fail without the instruction when the instruction claims to prevent that behavior;
9. prove the adapted instruction changes the intended behavior non-vacuously;
10. test interaction with existing SSSF/FirstMate instructions;
11. retain exact provenance of material copied/derived from upstream;
12. require normal review/security/cost/source-custody rules before activation;
13. define retirement/rollback so removing the skill does not corrupt durable engineering state.

A useful upstream `SKILL.md` is evidence and source material, not proof that the same artifact belongs unchanged in SSSF or FirstMate.
