# dzhng/skills — SSSF skill-factory research addendum

## Status

- **Planning disposition:** `PRESERVE` supporting research under existing `FUT-013`.
- **Primary candidate informed:** `FUT-011` — instruction-artifact governance.
- **Secondary inputs:** `FUT-010`, `FUT-012`, BOUND-1 discovery, DSH-3/DSH-6.
- **No new FUT ID. No roadmap promotion. No install. No production dependency.**

Reviewed repository:

- repository: `dzhng/skills`
- exact reviewed commit: `75850bcf51e2c0cacef1669f7ea4e5d561c32e5e`
- reviewed date: 2026-08-22
- license: MIT

This addendum extends the research family in `AGENT_ENGINEERING_SKILLS_RESEARCH.md`. It does not change that family's governing extraction rule:

> **Borrow decision-changing primitives; do not import another workflow authority.**

Re-inspect the then-current upstream and pin exact source identity before any implementation, copy, adaptation, or qualification.

---

# 1. Architectural ruling

The repository demonstrates that skills can be useful semantic procedure artifacts, but its full software-factory loop also demonstrates why SSSF must not make `SKILL.md` the outer workflow authority.

Upstream skills such as `implement-spec`, `review`, and `implement-spec-with-codex` encode sequencing, continuation, fan-out, review ordering, reslicing, commits, human-wait behavior, and completion in prose. Those mechanisms are useful research examples, not SSSF execution authority.

Target SSSF split:

```text
SSSF / FirstMate CODE
  owns applicability, sequencing, budgets, retries, fan-out, effects,
  acceptance, promotion, and terminal state
        ↓
bounded AgentBackend / DSH ExecutionCell
        ↓
qualified skill generation
  owns semantic method, investigation heuristics, failure smells,
  judgment procedure, and semantic artifact shape
        ↓
agent produces typed semantic result/evidence
        ↓
CODE disposes
```

A skill may request another capability or suggest that additional semantic work is useful. The request does not grant authority. CODE decides admission.

---

# 2. Strongest extracted mechanisms

## 2.1 Explicit delegated-decision scope / decision budget

`write-spec` distinguishes decisions fixed by the plan from freedoms deliberately delegated to the implementer. An unlisted decision that the implementer must invent is treated as a specification gap rather than implicit discretion.

SSSF adaptation candidate:

```text
fixed_decisions
explicitly_delegated_decisions
reserved_decisions
```

When an execution unit encounters a required decision:

```text
specified? -> follow
else explicitly delegated? -> agent may decide and emit a typed choice fact
else mechanically observable? -> establish automatically
else -> route by existing authority classification
```

This is supporting evidence for typed WorkPackage / ExecutionCell authority and for minimizing silent agent-created architecture.

## 2.2 Choices as a review surface

`audit-choices` focuses on decisions the implementer made where the specification was silent. That is a valuable review surface, but reconstructing those decisions after the fact from transcripts, diffs, and self-report is weaker than SSSF's target evidence model.

Preferred SSSF form:

```text
choice_id
outer_attempt_id / execution_cell_id / inner_unit_id
specification gap
alternatives considered
chosen alternative
rationale
confidence
reversibility
affected contract/scope
authority class
```

Emit the choice fact at the semantic owner when practical. Later human/reviewer views are deterministic projections over durable choice facts. A separate audit may search for likely missing choice records, but reconstruction is not the primary truth source.

## 2.3 Skill = compact semantic operational memory

`write-skills` treats a skill as compressed operational memory that changes process, not as general documentation. Useful principles:

- metadata/description is part of applicability behavior;
- active skill bodies should be small;
- progressive disclosure should keep heavy reference material out of default context;
- repeatable fragile mechanics belong in scripts/tools rather than prose;
- generic competence reminders should be removed when they do not measurably change behavior;
- examples should teach failure recognition rather than freeze one historical fix;
- implementation-specific locators should stay out of durable semantic doctrine unless navigation itself is the skill.

SSSF interpretation:

> **A skill should change a semantic decision or investigation process that CODE cannot honestly make deterministic. Otherwise it is context tax or misplaced policy.**

## 2.4 Blind behavioral skill evaluation

`eval-skills` treats a skill like a function under test:

```text
exact skill generation
  -> fresh blind runner
  -> artifact
  -> separate fresh judge + explicit bar
  -> repeated trials when nondeterminism matters
  -> defect analysis
  -> revised generation
  -> rerun full case suite
```

Future SSSF/FUT-011 qualification should bind at least:

```text
skill_id
skill_generation
skill_content_digest
case_id
fixture/input digest
role
model/profile
AgentBackend generation
capability/tool contract
runner identity
judge identity
independence class
result + evidence refs
```

The runner must not receive the golden outcome/bar when doing so would leak the answer. The judge must not become promotion authority. CODE evaluates the qualification evidence against admission policy.

## 2.5 Skill qualification should include multiple executions / profiles

One successful agent run is not sufficient evidence that an operational instruction is robust. Where behavioral nondeterminism matters, qualification should use repeated blind runs and report pass rate / outcome distribution rather than treating one green trajectory as proof.

Where a skill claims harness/model portability, test more than the model/profile that authored it. Do not require universal model coverage without a real production need; bind qualification to the exact supported execution profiles.

## 2.6 Continuous CODEward migration

A successful skill is not necessarily a permanent skill.

If repeated use reveals a stable/checkable rule, move it toward:

```text
semantic skill
  -> typed contract / deterministic helper
  -> CODE-owned enforcement
```

The skill should then shrink or retire. This is a direct application of `Preserve -> Purify -> CODEward`.

---

# 3. Engineering-skill ideas worth preserving

## 3.1 `write-tests`

High-value ideas:

- tracer-bullet tests one behavior at a time;
- outermost practical observable seam;
- avoid pinning implementation/configuration accidents;
- avoid internal over-mocking;
- harness must wire the production path honestly;
- stochastic claims need distributional evidence rather than a lucky sample;
- regression tests should be falsified once so the test is observed red for the intended defect and green after restoration.

This strongly reinforces SSSF watched-red/non-vacuity discipline. It is potential semantic TDD-worker guidance, not a replacement for deterministic verification owners.

## 3.2 `refactor-clean`

Useful compact laws:

- one semantic concept should have one authoritative owner;
- before adding machinery, establish whether an existing platform/owner already provides it;
- a defensive check whose invalid state cannot be produced by an admitted writer may be noise;
- repeated requests should prefer idempotent end-state semantics where the operation is naturally idempotent;
- do not independently re-derive owner-computed facts merely to create a second drifting implementation;
- small behavior with disproportionate structural weight is a shape smell;
- remove lineage/sediment from active code; history belongs in evidence/Git, not current identifiers.

These are candidate inputs to FUT-010 and reviewer/worker doctrine, subject to conflict review with existing SSSF law.

## 3.3 `audit-performance`

This is a strong **semantic discovery lens** for BOUND-1 because it asks the agent to find:

- work that grows with history, tenants, input, outage duration, retries, or observations;
- retries/polls where nothing must change before another attempt;
- poison items that can block later work;
- fixed-prefix recovery loops that repeatedly rescan the same subset;
- unbounded transport sides, queues, streams, filesystem walks, and scheduled work;
- supposed performance findings already safely bounded by a real owner/healing mechanism.

For each candidate surface it asks for trigger, worst-case amplification, owner, forward-progress mechanism, existing bound/healing behavior, and what happens at overload.

**BOUND-1 use:** FirstMate/worker agents may use these questions during discovery to improve recall. They do not certify boundedness. The machine-readable boundedness registry, exact owner/enforcement evidence, boundary tests, and canonical validator remain authoritative.

## 3.4 `write-spec`

Preserve:

- one semantic work slice should aim for one contract, one seam, one review surface, and one focused verdict;
- large/foggy work should be recursively decomposed until the next unit is independently verifiable;
- research unfamiliar external practice before freezing a semantic plan;
- explicitly name freedoms delegated to the implementer;
- plan amendments should arise from execution evidence rather than pretending the first plan was complete.

Do **not** preserve its fixed prose-owned planning fan-out policy (including an at-least-three drafter floor). SSSF's Boundedness Law and lowest-sufficient-autonomy rule require CODE-owned finite fan-out and measured justification for additional agents.

SSSF plan amendment target:

```text
execution evidence
  -> agent proposes amendment
  -> CODE validates identity/authority/graph legality
  -> new immutable graph/spec generation
```

not model-owned mutable workflow state.

## 3.5 `explore-unknowns`

Useful mainly for FirstMate/Wayfinder intent refinement and bounded semantic discovery:

- establish repository/domain facts instead of asking the Captain;
- distinguish explicit unknowns from tacit assumptions and blind spots;
- perform an evidence-based landmine sweep over the affected territory;
- convert true product/personal choices into explicit decisions rather than silently inventing them.

Do not turn this into a mandatory Captain-interview loop inside SSSF execution.

## 3.6 `write-docs` and `close-spec`

Useful documentation principle:

```text
mechanically derivable current inventory -> code/generated projection
human rationale / why / invariants        -> authored durable explanation
```

A live build plan and a post-build rationale have different purposes. SSSF should not destructively rewrite or delete immutable planning/evidence history merely to create the rationale. Prefer a current rationale/projection that points to preserved history and authoritative code/evidence.

This materially supports FUT-012.

---

# 4. Visual-review pattern

`compare-screenshots` and `screenshot-critique` provide a useful division:

```text
CODE / deterministic tool
  -> pixel, edge, crop, geometry, distance and capture-comparability facts

fresh semantic reviewer
  -> whether observed visual differences satisfy the actual target
```

The baseline itself is not automatically truth. A fresh reviewer should not be primed with the implementer's intended fix when independence matters.

Potential future use: DSH-6/product-review cells or visual engineering profiles. Deterministic telemetry remains evidence; semantic visual judgment remains advisory until SSSF acceptance policy consumes it.

---

# 5. Explicit non-adoptions

Do not import or reproduce as SSSF authority:

- `/goal -> /implement-spec` as an agent-owned outer factory loop;
- `review` as prose-owned review sequencing/terminal authority;
- agent-owned fan-out, retry/continuation, commits, reslicing, or completion;
- fixed three-or-more planning-agent minimum;
- timed human silence that converts Captain-owned authority into agent authority;
- `implement-spec-with-codex` as a competing orchestrator;
- host worktree execution as a security boundary;
- Codex `--dangerously-bypass-approvals-and-sandbox` policy;
- Claude `--dangerously-skip-permissions` policy;
- external skill routing as authorization;
- diff-only review as a substitute for deterministic qualification / maker-checker review;
- post-hoc reconstructed choice ledgers as the primary evidence source where typed owner emission is available.

SSSF's Docker SandboxProvider, AgentBackend contracts, FirstMate/Browser-Sol authority model, boundedness law, and deterministic outer graph remain controlling.

---

# 6. FUT-011 candidate strengthening

When FUT-011 is evaluated for promotion, add these prospective requirements to the existing research family:

1. exact skill/instruction generation and content digest;
2. explicit semantic role and real consumer;
3. applicability/trigger contract;
4. required capability/tool/effect contract;
5. context-budget bound;
6. behavioral watched-red / non-vacuity where the artifact claims to change behavior;
7. blind runner + independent judge qualification where semantic behavior is under test;
8. repeat trials/profile coverage proportionate to nondeterminism and claimed portability;
9. collision/interference tests with other active instructions;
10. explicit delegated-decision scope where the skill permits semantic discretion;
11. typed choice emission for load-bearing decisions made under that discretion where practical;
12. CODE-owned invocation/retry/fan-out/termination and production admission;
13. retirement/CODEward migration path;
14. rollback that removes the skill without corrupting durable engineering state.

Candidate lifecycle shape:

```text
EXPLORE
  -> AUTHOR
  -> STRUCTURAL VALIDATION
  -> APPLICABILITY / ROUTING VALIDATION
  -> BEHAVIORAL WATCHED-RED
  -> BLIND MULTI-RUN EVAL
  -> INTERACTION / COLLISION TEST
  -> QUALIFIED GENERATION
  -> PINNED ADMISSION
  -> OBSERVE
  -> MECHANIZE / REVISE / RETIRE
```

This is a research input, not a new planning lifecycle and not authorization to implement FUT-011 now.

---

# 7. Revisit rule

Re-review `dzhng/skills` at the then-current exact upstream identity when any of these become active implementation questions:

- FUT-011 instruction/skill governance;
- DSH production skill admission;
- DSH-6 semantic reviewer cells;
- a FirstMate-owned skill qualification framework;
- visual semantic-verification capability;
- a major BOUND-1 re-audit where new semantic discovery methods may improve coverage.

New upstream skills or changed evidence may alter the evaluation. Today's source pin is research provenance, not a grandfathered production version.
