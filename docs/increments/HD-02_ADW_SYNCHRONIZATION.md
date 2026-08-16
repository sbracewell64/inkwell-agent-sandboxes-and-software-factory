# HD-02 — ADW Static Synchronization

**Status:** PASS

**Starts from:** `04e5484a6190f033d25e1626b96a4cca93b7f755`

**Boundary:** installed ADWs, SSSF skill templates, one-shot generator, typed Report examples

## Intent

Prevent one-sided changes to ADW call sites, module exports, generated dependency metadata, typed output examples, and run completion from deferring failures to runtime.

Non-goals are provider execution, sandbox lifecycle, migration/expansion, gate semantics, contribution Git policy, and changes to retained session evidence.

## Design

`docs/validation/check_adw_synchronization.py` is the single provider-independent validator. It statically parses every discovered installed and template `adw_*.py`, generates a disposable representative ADW, and reports a nonempty inventory. For each surface it:

- resolves imports and imported module attributes against the matching `adw_modules` tree;
- requires every `AgentCall` to name a concrete `EnvelopeBase` subclass as `output_type`;
- requires exactly one `run.finish()` call as the final top-level `return` in `main()`, proves the bounded statement prefix can fall through to it, and rejects any other or nested finish and removed `run.succeeded` use;
- recursively derives third-party imports and compares them with each script's PEP 723 dependencies;
- compares every prompt `Report` JSON object's fields with its named output type, including inherited fields;
- imports the disposable generated script with its declared dependencies without calling `main()` or any provider.

A missing surface, module tree, prompt Report inventory, generator, or watched-red fixture is CNO and cannot print PASS.

## Bounded repairs

The existing installed API remains the sole quality naming contract: `run_inkwell_tests` and `run_inkwell_quality`. Installed quality call sites and template exports/call sites now use it.

The generator now declares `rich`, emits `run.finish()`, and writes UTF-8 deterministically. The installed and template Scout Report examples now include inherited `notes_for_next_agent`, matching `ScoutOutput`.

No claim is made that all prior ADWs were broken: all twelve installed ADWs already used `run.finish()` before this increment. The defects were bounded to the two quality call sites, template/API drift, generator dependencies/completion/encoding, and the Scout prompt field examples.

## Watched-red controls

Mutation fixtures under `docs/validation/fixtures/adw_sync/` remove a quality export, remove `rich`, restore `run.succeeded`, violate the final-return finish contract through Boolean and non-Boolean loops, match guards, nested compound flow, returns, and reachable break, and mismatch a prompt field. The validator copies the bounded surfaces to disposable roots and requires the exact fixture inventory to turn that same validator red for its expected reasons.

## Deterministic acceptance

Run:

```text
uv run docs/validation/check_adw_synchronization.py
```

Accepted inventory at implementation time:

- 12 installed ADWs;
- 12 template ADWs;
- 1 disposable generated ADW;
- 54 concrete `AgentCall.output_type` declarations;
- 25 top-level final-return `run.finish()` contracts;
- 25 dependency/import sets;
- 10 prompt Report contracts;
- 1 generated import-only smoke;
- 16 watched-red fixtures.

The validator printed `HD-02 ADW synchronization: PASS`, `compound-reachability-red-controls: PASS`, `top-level-final-return-finish-contract: PASS`, and `prefix-fallthrough-contract: PASS`. No provider/model or sandbox was invoked.

## Claim boundary — added 2026-08-16, normative clarification

Everything above stands as recorded. This section adds no claim and withdraws
none; it names the boundary of the claim that was always being made, because the
word "synchronization" in this increment's title reads wider than what its
validator checks.

**What `check_adw_synchronization.py` verifies:** the internal CONTRACT SHAPE of
each surface, independently — imports and imported module attributes resolve
against that surface's own `adw_modules` tree, every `AgentCall` names a concrete
`EnvelopeBase` subclass, exactly one top-level final-return `run.finish()`, PEP
723 dependencies reconcile with imports, and prompt `Report` fields match their
output model. It constructs installed, template and generated surfaces and loops
over them one at a time.

**What it does not verify, and never claimed to:** that the installed and
template surfaces hold the SAME CONTENT. It performs no cross-surface digest or
byte comparison. Both surfaces can satisfy every contract above while a module
differs between them, and this validator will correctly print `PASS`.

That is not a defect in this increment — it is outside its boundary. But the
gap was real and unowned, and it is how the live/template drift repaired in the
mapped-surface increment went undetected: a validator named "ADW synchronization"
was green while four modules and five prompts differed across the surfaces it
names.

**Content parity now has its own owner:** `docs/validation/check_mapped_surface_parity.py`,
governed by `docs/validation/mapped_surface_contract.json`. The two validators are
deliberately separate rather than merged — one owns contract shape, the other owns
the mapped content relationship, and mixing those semantics for naming convenience
would make both harder to reason about. This validator is preserved unchanged; its
verdict is not broadened retroactively by the existence of the newer one.
