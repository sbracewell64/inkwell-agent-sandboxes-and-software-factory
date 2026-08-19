# Agentic Engineering Governance Research

## Status

Planning research only. This document records four promoted `CANDIDATE` mechanisms extracted from the Captain's prior Agentic Engineering (AE) architecture corpus. None is sequenced or authorized for implementation by this document.

Reviewed source corpus:

- `Agentic Engineering/docs/architecture`
- `Agentic Engineering/docs/eia`
- 67 Markdown documents reviewed from the Captain-supplied archive on 2026-08-19.

The source archive was supplied for architectural research; it is not committed into SSSF and is not a current SSSF authority. The durable value retained here is the evaluated architectural primitive, not AE's file hierarchy or component names.

## Governing extraction rule

> **Use AE to identify what SSSF must know and prove, not to decide how many components SSSF must have.**

AE repeatedly encoded strong governance properties through separate Runtime, Service, Repository, Registry, ledger, catalog, profile, Knowledge, Engineering Intelligence, Flow, Step, Skill, Execution Plan, Execution Unit, and Session layers. SSSF must not reproduce that topology merely because the underlying rule is useful.

All four candidates below carry a shared complexity constraint:

1. prefer an existing SSSF owner over a new subsystem;
2. prefer one machine-readable contract over several manually synchronized catalogs;
3. prefer generated/read-only projections over second sources of truth;
4. prefer deterministic validators over prose reminders;
5. preserve existing SSSF authority order: executable code/tests -> immutable evidence/Git objects -> current configuration -> docs;
6. do not create a new orchestration layer, transparency daemon, governance runtime, repository abstraction, or registry unless an existing owner is demonstrably insufficient;
7. planning promotion does not imply current implementation behavior.

## Shared evidence from the AE review

The strongest recurring AE concepts were:

- single authoritative ownership of facts and transitions;
- durable ownership for facts required after the producing invocation;
- immutable definition separated from mutable execution state;
- falsifiable verification rather than nominal green checks;
- explicit cannot-claim boundaries;
- composition proof at important seams;
- population-before-expansion discipline;
- deterministic mutation dispatch through one owner;
- generated non-authoritative indexes and ownership/catalog views;
- provenance as objective/inputs/observations/findings/evidence rather than model chain-of-thought;
- lineage as a read-only join across canonical owners rather than another ledger;
- certification identity independent of aggregate verdict;
- instruction artifacts with one authoritative semantic source and real consumers;
- deterministic derived documentation from canonical machine state.

The review also found that AE's major failure mode was not weak governance but **governance proliferation**: useful laws were repeatedly wrapped in new named components and document types until the architecture itself became difficult to reason about.

---

# FUT-009 — SSSF architecture-unit contract and generated governance views

State: `CANDIDATE`

## Problem

SSSF increasingly has architecture facts distributed across ADRs, architecture documents, code paths, validators, manifests, increment records, and evidence. As sandbox, DSH, subagents, verifier evidence, and future plugins arrive, manually maintained ownership/index/catalog documents can drift or duplicate one another.

## Evidence

AE's ADR index, component-ownership catalog, population plane, instruction-artifact catalog, lineage projection, certification records, and platform-profile work repeatedly solved the same class of problem: make architecture ownership and derived views machine-checkable. Their useful property was the contract/projection split; their cost was maintaining several overlapping catalogs and owners.

Current SSSF already has partial primitives that this candidate must reuse rather than replace, including `docs/manifest.yaml`, ADRs, `docs/reference/FILE_MAP.md`, source-custody validation, mapped-surface validation, front-door taxonomy, CI check registration, increment/proof records, and the planned run -> ADW -> outer attempt -> execution cell -> inner unit identity spine.

## Primitive

One compact machine-readable **architecture-unit declaration** format plus deterministic validation and generated read-only governance views.

An architecture unit may bind, as applicable:

- stable unit identity and kind;
- governing ADR(s);
- authoritative owner;
- code/config/state/artifact surfaces;
- owned facts/transitions;
- delegated facts/transitions;
- invariants;
- explicit cannot-claim boundaries;
- verifier(s);
- evidence/proof references;
- real consumers;
- lineage/parent relationships where useful.

The declaration states the intended architecture contract. It is not proof that implementation conforms. Validators establish that relationship.

## Owner

SSSF deterministic code/documentation validation owns the contract and projections. Browser Sol owns architectural promotion/meaning until a specific implementation increment is activated.

## Existing owners to preserve

- ADRs own architectural decisions/rationale;
- executable code/configuration own current behavior;
- validators own their measured property;
- evidence/Git objects own proof identity;
- `docs/manifest.yaml` remains the documentation/planning router unless a later decision deliberately changes it.

This candidate must not become a competing architecture database.

## Replacement

Potentially replaces future pressure for separately hand-maintained:

- ADR index;
- component ownership catalog;
- durable-state/population plane;
- instruction-artifact inventory;
- validator-coverage map;
- lineage summary tables.

These should be generated projections where the required facts are mechanically derivable.

## Inputs

Architecture-unit declarations, ADR identities, repository paths, existing manifests/contracts, validator registrations, code/configuration identities, evidence references.

## Outputs

Validated architecture-unit state and generated read-only projections such as:

- architecture-unit index;
- ADR index;
- ownership map;
- durable-artifact map;
- validator coverage;
- consumer/reference map;
- lineage projection where canonical identities exist.

## State

Declarations are version-controlled source. Generated views are projections and explicitly non-authoritative.

## Trigger

Evaluate for sequencing when SSSF has enough recurring architecture drift/duplication that one compact contract demonstrably removes more machinery than it adds, preferably before DSH substantially expands the number of attributable execution units.

## Verifier

A deterministic architecture-contract validator should prove structural integrity and selected reality bindings rather than keyword presence.

## Required negative controls

- duplicate architecture-unit identity fails;
- duplicate/ambiguous ADR identity fails;
- ADR filename/declared identity disagreement fails;
- referenced path/validator/ADR that cannot be resolved is non-pass/CNO as appropriate;
- two units claiming exclusive ownership of the same fact fail unless the contract explicitly defines a valid composition;
- a generated projection edited out of agreement with declarations fails regeneration/digest comparison;
- a declaration that points at a verifier which does not actually own/check the claimed property fails;
- stale evidence identity cannot satisfy a moved implementation;
- generated projection cannot become a second mutation owner.

## Failure behavior

Fail closed for contradictory/invalid declarations; use CNO when required repository state cannot be observed. Never infer ownership from prose when the machine contract is incomplete.

## Rollback

Remove the declarations/generator before canonical adoption; existing ADRs/code/evidence remain valid independently. After adoption, retirement must first migrate any uniquely owned machine facts back to an explicit owner.

## Documentation

Prefer generated views under an explicit generated/non-authoritative location. Keep authored rationale in existing ADR/architecture surfaces.

## Documentation verifier

Generated output must be reproducible from canonical inputs and byte-stable for identical canonical state.

## Telemetry

Track declaration count, generated-view count, unresolved/duplicate ownership findings, drift findings, and number of manual governance surfaces retired.

## Promotion criteria

Promote only if a prototype demonstrates net simplification: fewer manually synchronized architecture surfaces, mechanically detected real drift, and no new runtime/orchestration authority.

## Retirement

If the contract becomes a second architecture source or requires more maintenance than the views it replaces, retire it and keep the smaller existing owners.

## Net complexity target

Negative or near-zero. The candidate is successful only if it collapses multiple future catalogs into one small source + validator + projections.

## Authority class

Architecture metadata and validation only. It does not authorize execution, planning promotion, acceptance, or landing.

## State transition

None in the SSSF runtime. This candidate governs description/verification of architecture state.

## Determinism boundary

Code validates declarations and generates projections. Models may propose edits but cannot declare their proposal conformant.

## Provenance

Every generated view must identify the exact source identity/declaration set and generator identity used to produce it.

---

# FUT-010 — Compact SSSF architectural laws

State: `CANDIDATE`

## Problem

SSSF already follows several strong architectural principles, but some are distributed across the Boundary Law, increment protocol, audit rulings, security rules, planning lifecycle, and individual ADRs. As new sandbox/DSH capabilities arrive, the same constitutional questions can be rediscovered unless a small stable law set makes them explicit.

## Evidence

AE's Platform Constitution and governing-law ADRs were valuable where they stated falsifiable architectural properties, but became costly where they encoded AE-specific component names and grew into their own governance architecture.

The useful laws extracted from the review are largely consistent with current SSSF behavior:

1. **Single Owner Law** — every authoritative fact/state transition has one owner.
2. **Durability Law** — a fact needed after its producer invocation requires a durable owner.
3. **Definition/Execution Separation** — immutable authorization/definition does not carry mutable execution progress.
4. **Falsifiability Law** — a verification claim is legitimate only when the verifier demonstrably rejects a defect in the property claimed.
5. **Boundary-Honesty Law** — important boundaries state both guarantees and cannot-claim limits.
6. **Composition Law** — independently valid units do not prove their composition; important seams require composition proof.
7. **Population-before-Expansion Law** — new machinery must prove existing owners cannot reasonably absorb the need.
8. **Evidence-over-Assertion Law** — absence/unobserved state is never satisfaction.
9. **Explicit Judgment Boundary** — semantic/human judgment enters through an explicitly owned boundary and cannot be smuggled into deterministic transition logic.

## Primitive

Strengthen the **existing** SSSF architectural-law surface, most likely `docs/architecture/BOUNDARY_LAW.md` plus machine-checkable references where applicable. Do not create an article-based constitution or new governance runtime.

## Owner

Browser Sol/Captain own architectural meaning through accepted ADR/planning decisions; SSSF code/validators enforce mechanically expressible portions.

## Existing owner

`docs/architecture/BOUNDARY_LAW.md` is the preferred existing owner. Other current authority documents remain referenced rather than duplicated.

## Replacement

Replaces repeated reinvention of these laws in future ADRs/prompts. It does not replace topic-specific ADRs or security/source-custody contracts.

## Inputs

Current Boundary Law, accepted ADRs, increment protocol, three-valued observation rules, source-custody/permission/evidence contracts, and the DSH execution-cell authority decision.

## Outputs

A compact law set with precise scope and cross-references to actual enforcement owners.

## State

Authored architecture law, version-controlled.

## Trigger

May be evaluated before DSH implementation because DSH will exercise these boundaries heavily. Sequencing should occur only when the candidate text is reconciled against current accepted architecture rather than copied from AE terminology.

## Verifier

Where a law is mechanically enforceable, link it to the actual validator/contract. Laws that remain semantic architecture constraints must not pretend to have deterministic enforcement.

## Required negative controls

- a law cannot name an AE-only component as an SSSF owner;
- two laws cannot assign the same exclusive fact to different owners without an explicit composition rule;
- a law cannot claim enforcement by a validator that does not test the property;
- a new subsystem proposed solely to implement a law must fail the population-before-expansion review unless existing owners are insufficient;
- CNO/unknown cannot be documented as satisfying a law that requires positive evidence.

## Failure behavior

Unclear/conflicting law remains unpromoted rather than being interpreted by agents ad hoc.

## Rollback

Revert the compact law additions; underlying ADRs/contracts remain authoritative.

## Documentation

One compact existing owner, not a new constitution hierarchy.

## Documentation verifier

Cross-reference validation may eventually be absorbed into FUT-009 if that candidate is adopted.

## Telemetry

Track how many future ADRs can cite rather than restate the laws, and whether new component proposals are rejected/absorbed by population-before-expansion.

## Promotion criteria

The final law set must be short, SSSF-native, non-duplicative, and each law must either have an enforcement owner or explicitly state that it is an architectural judgment constraint.

## Retirement

Retire any law that becomes redundant with a more precise authoritative contract; do not preserve slogans after their owner moves.

## Net complexity target

Very low. This candidate should reduce repeated prose and design ambiguity.

## Authority class

Architecture/governance constraint only; does not itself authorize work.

## State transition

None.

## Determinism boundary

Deterministic validators enforce only the mechanically decidable subset. Browser Sol/independent review handles semantic architecture applicability.

## Provenance

Each law should cite the accepted SSSF decisions/contracts from which it was derived, not the AE document as present-day authority.

---

# FUT-011 — Instruction-artifact governance

State: `CANDIDATE`

## Problem

As SSSF approaches DSH, the number of durable instruction-bearing artifacts may grow: system prompts, agent roles, skills, execution-cell doctrine, verifier criteria, subagent definitions, tool instructions, review policies, and plugin guidance. Duplicated or sedimentary instruction prose can create hidden conflicting authority.

## Evidence

AE's Instruction Artifact Authoring Standard was one of the strongest documents in the reviewed corpus. Its useful rules were semantic singularity, stable terminology, checkable completion conditions, explicit consumers, bounded claims, independent policy axes, and removal of speculative/duplicated instructions. AE's separate instruction catalog is useful only as a projection, not another manual registry.

## Primitive

A small SSSF instruction-artifact contract centered on:

> **One meaning, one authoritative instruction source.**

Rules should include:

- cite the semantic owner rather than paraphrasing it in multiple places;
- every durable instruction artifact has a declared owner and actual consumer;
- completion/acceptance instructions are mechanically checkable where possible;
- terminology is stable and defined once;
- bounds/capabilities/cannot-claim limits are truthful;
- independent policy axes stay independent;
- stale or contradictory duplicate instructions are defects;
- speculative instructions are not created before a real consumer exists;
- generated instruction inventories are projections only.

## Owner

SSSF documentation/prompt/skill contracts own their specific instructions. This candidate defines cross-cutting authoring/validation rules, preferably through existing documentation validation rather than a new runtime.

## Existing owners

Current prompts, roster/config, `AGENTS.md`, skills, ADRs, DSH plan, and future execution-cell contracts remain individual semantic owners.

## Replacement

Replaces ad hoc prompt duplication and any temptation to create a manually curated instruction registry.

## Inputs

Declared instruction artifacts, their owners, consumer call sites/configuration, governing ADR/work contract, and generated inventory inputs where available.

## Outputs

Validated instruction ownership/consumer relationships and optionally a generated inventory.

## State

Version-controlled instruction artifacts and declaration metadata.

## Trigger

Evaluate before DSH-1/DSH-3 expands system prompts/subagents substantially. A minimal pre-DSH rule set may be worthwhile if it can reuse existing docs/skill validation without creating a new subsystem.

## Verifier

Deterministically validate declared ownership, path existence, consumer existence where mechanically observable, duplicate identities, and generated inventory freshness. Semantic contradiction/redundancy still requires review unless normalized machine contracts make it decidable.

## Required negative controls

- durable instruction with no declared/real consumer is rejected or explicitly classified unused;
- two artifacts claiming to be authoritative for the same instruction identity fail;
- a generated inventory edited independently fails regeneration;
- a consumer pointing at a stale/nonexistent instruction identity fails;
- a non-authoritative copy cannot silently override the owner;
- acceptance criteria omitted from the authoritative typed work contract cannot be created by a downstream prompt;
- DSH/verifier/subagent instructions cannot enlarge their external authority/budget beyond the execution-cell request.

## Failure behavior

Fail closed for structural ownership/consumer contradictions. Semantic contradiction remains an explicit review finding, not an automatically invented resolution.

## Rollback

Remove the cross-cutting metadata/validator; instruction owners remain in place.

## Documentation

Prefer a short authoring standard and generated inventory, not an AE-style catalog plus runtime.

## Documentation verifier

If a catalog/view exists, it must be generated from actual instruction declarations/consumers.

## Telemetry

Count authoritative instruction artifacts, unconsumed artifacts, duplicate-owner findings, stale consumer references, and manual duplicates retired.

## Promotion criteria

Demonstrate a real recurrence class or DSH-driven growth problem and show that the contract prevents it with less complexity than manual review alone.

## Retirement

If DSH or another accepted substrate later provides an equivalent stable machine-readable instruction ownership model, collapse into that owner rather than maintaining parallel governance.

## Net complexity target

Low and increasingly valuable as DSH autonomy grows.

## Authority class

Instruction ownership/validation only. It never grants execution authority beyond the governing work/cell contract.

## State transition

None in the outer work graph.

## Determinism boundary

Code checks identity/ownership/consumer structure. Semantic content quality remains bounded review unless encoded in typed contracts.

## Provenance

Instruction artifacts and generated views bind exact repository/source identity; DSH-generated or evolved instruction proposals remain immutable candidates until normal SSSF promotion.

---

# FUT-012 — Deterministic derived documentation

State: `CANDIDATE`

## Problem

Architecture/status/index/ownership tables that merely restate canonical machine state drift when humans or agents maintain them manually. Requiring every architecture change to update several redundant documents increases complexity and creates false confidence when prose is stale.

## Evidence

AE's Documentation Runtime and generated ADR/ownership/catalog views demonstrated the useful rule: identical canonical state should yield byte-identical derived documentation. The dedicated Runtime architecture is unnecessary for SSSF; the generator property is the valuable part.

Current SSSF already has examples of generated or validator-owned documentation patterns and several audit increments where stale prose contradicted good code. This candidate generalizes the rule selectively rather than mandating generation for all docs.

## Primitive

Classify documentation into two kinds:

1. **Authored rationale/explanation** — ADRs, architecture reasoning, operational explanation, human judgment.
2. **Derived projection** — indexes, ownership tables, state inventories, validator coverage, lineage/artifact maps that can be mechanically computed.

For derived projections:

- code owns generation;
- identical canonical inputs produce byte-identical output;
- generated output is explicitly non-authoritative;
- CI/validator detects stale or manually edited projection bytes;
- generated docs point back to their canonical sources/generator identity.

## Owner

The canonical code/config/declarations own the facts; deterministic generator owns the projection bytes.

## Existing owner

Existing SSSF docs remain authored unless a specific projection is deliberately converted. This candidate does not authorize bulk conversion.

## Replacement

Replaces manual synchronization of mechanically derivable tables/indexes only.

## Inputs

Canonical repository declarations/state that are stable and complete enough to derive the projection.

## Outputs

Byte-stable Markdown/JSON or other read-only generated views.

## State

Generated files may be tracked when useful for human/agent discovery, but their authority remains the source inputs + generator, not the checked-in rendering.

## Trigger

Adopt incrementally when a manual projection has demonstrated drift or when FUT-009/FUT-011 creates machine-readable source data worth rendering. Do not build a generic documentation runtime in advance.

## Verifier

Regenerate in a controlled environment and compare exact canonical bytes/digest, or derive the same representation through a deterministic checker.

## Required negative controls

- manual edit to generated output is detected;
- same canonical inputs with nondeterministic ordering/timestamps fail reproducibility;
- missing source data yields CNO/non-pass rather than invented prose;
- a generated view cannot be cited as higher authority than its source;
- generated history cannot silently overwrite authored rationale;
- a generator cannot mutate runtime/architecture state while rendering docs.

## Failure behavior

Stale generated projection is non-pass for the documentation contract; it does not rewrite source state automatically during validation unless an explicit safe generation command is invoked.

## Rollback

Return a projection to authored form only by explicitly choosing a new authority; never leave both generator and manual editor as competing owners.

## Documentation

Generated files must identify themselves as generated/non-authoritative and name the generator/source contract.

## Documentation verifier

The generator/digest comparison is the verifier.

## Telemetry

Count generated projections, stale-view catches, nondeterminism catches, and manual synchronization surfaces retired.

## Promotion criteria

At least one real manual projection must be simplified or made drift-proof without adding a standing service/daemon/runtime.

## Retirement

Remove generators whose source contract disappears or whose view no longer has a consumer.

## Net complexity target

Negative. Every added generator should retire more manual synchronization burden than it creates.

## Authority class

Read-only projection only.

## State transition

None.

## Determinism boundary

Code alone derives projection bytes from canonical inputs; models may author rationale but do not decide generated facts.

## Provenance

Generated projections bind source identities and generator identity/version/digest sufficient to reproduce the bytes.

---

# Relationship among FUT-009 through FUT-012

These are separate candidates because they may prove useful at different times, but they should compose without becoming four new subsystems.

Likely dependency shape for later evaluation:

```text
FUT-010 compact architectural laws
        │
        ├──────────────┐
        ▼              ▼
FUT-009 architecture   FUT-011 instruction-artifact
unit contract          governance
        │              │
        └──────┬───────┘
               ▼
FUT-012 deterministic derived documentation
        (only for projections worth generating)
```

This is **not roadmap sequencing**. All four remain `CANDIDATE` and unsequenced.

FUT-009 and FUT-012 may eventually share one validator/generation tool rather than separate machinery. FUT-011 should reuse FUT-009 declarations if architecture-unit metadata already captures instruction owner/consumer facts. FUT-010 should remain the smallest authored law surface and must not become a new hierarchy.

## Relationship to Sandbox -> DSH work

The AE candidates must not interrupt or expand the currently sequenced sandbox/DSH implementation plan by default.

- FUT-010 can be evaluated before DSH if it helps stabilize the laws DSH must obey.
- FUT-009 becomes increasingly valuable as sandbox/DSH adds execution-cell and inner-unit ownership surfaces, but must not block SBX-0/1 or DSH-0A unless a specific contract need is demonstrated.
- FUT-011 should be evaluated before DSH substantially multiplies system prompts/subagents/instruction artifacts; it does not authorize a pre-DSH instruction runtime.
- FUT-012 is selectively activated only where an existing/proposed manual projection has a canonical machine source.

The candidates therefore follow the governing principle:

> **Architecture/governance machinery is admitted only when it reduces net complexity or closes a demonstrated recurrence class.**

## Explicit non-goals carried from the AE review

Do not create merely to emulate AE:

- Runtime Kernel;
- generic Runtime Services layer;
- Repository interfaces for every durable object;
- Registry layer for single-provider/single-owner cases;
- Knowledge Runtime/Knowledge Layer;
- Engineering Intelligence Runtime;
- Methodology -> Flow -> Step -> Skill execution hierarchy;
- PRD Runtime;
- Documentation Runtime service;
- generic reconciliation Kernel above SSSF ADWs;
- Assignment Ledger when existing trace/state can own the facts;
- Lineage Ledger when lineage is derivable as a read-only join;
- separate governance registers when one machine contract/projection can express the needed fact;
- an external transparency process reconstructing facts that owning code can emit directly.
