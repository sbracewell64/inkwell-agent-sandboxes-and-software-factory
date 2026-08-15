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
- requires exactly one reachable `run.finish()` from `main()` and rejects removed `run.succeeded` use;
- recursively derives third-party imports and compares them with each script's PEP 723 dependencies;
- compares every prompt `Report` JSON object's fields with its named output type, including inherited fields;
- imports the disposable generated script with its declared dependencies without calling `main()` or any provider.

A missing surface, module tree, prompt Report inventory, generator, or watched-red fixture is CNO and cannot print PASS.

## Bounded repairs

The existing installed API remains the sole quality naming contract: `run_inkwell_tests` and `run_inkwell_quality`. Installed quality call sites and template exports/call sites now use it.

The generator now declares `rich`, emits `run.finish()`, and writes UTF-8 deterministically. The installed and template Scout Report examples now include inherited `notes_for_next_agent`, matching `ScoutOutput`.

No claim is made that all prior ADWs were broken: all twelve installed ADWs already used `run.finish()` before this increment. The defects were bounded to the two quality call sites, template/API drift, generator dependencies/completion/encoding, and the Scout prompt field examples.

## Watched-red controls

Mutation fixtures under `docs/validation/fixtures/adw_sync/` remove a quality export, remove `rich`, restore `run.succeeded`, remove or make finish unreachable through returns, exhaustive match, and infinite loops, exercise reachable break and nested compound flow, and mismatch a prompt field. The validator copies the bounded surfaces to disposable roots and requires every mutation to turn that same validator red for its expected reason.

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
- 25 reachable `run.finish()` calls;
- 25 dependency/import sets;
- 10 prompt Report contracts;
- 1 generated import-only smoke;
- 10 watched-red fixtures.

The validator printed `HD-02 ADW synchronization: PASS` and `compound-reachability-red-controls: PASS`. No provider/model or sandbox was invoked.
