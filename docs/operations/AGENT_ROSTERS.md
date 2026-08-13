# Agent Rosters

## Agent primitive

Within SSSF an agent is the composition of:

- model,
- harness,
- tools,
- prompt,
- enforced write boundary.

The name/purpose is not sufficient to define behavior.

## Stock roster

Canonical stock configuration:

`adws/adw_sssf_config/sssf.config.yaml`

Do not silently rewrite it to accommodate local quota or free-tier conditions.

## Free proof roster

For baseline proof, a separate config was created inside the sandbox:

`adws/adw_sssf_config/sssf.free.config.yaml`

For `adw_plan_build_test.py`, only `planner` and `builder` were required.

Both were set to:

`openrouter/cohere/north-mini-code:free`

Result: successful 5/5 ADW.

## Failed free planner experiment

`openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`

produced a typed report but failed to create declared files. SSSF correctly rejected it.

This is evidence that model availability is not the same as role qualification.

## Permanent roster policy

Never edit the stock roster merely to test a model.

Create named rosters:

- `sssf.config.yaml` — upstream/default
- `sssf.local-free.config.yaml` — local zero-cost profile
- future explicit profiles by purpose/cost/risk

Every permanent roster must record:

- model ID,
- role,
- thinking level,
- tools,
- writes,
- protected files,
- harness extensions,
- date last validated,
- validation workload,
- known limitations.

## Volatility

Free OpenRouter models can appear/disappear or change limits. Model IDs are operational configuration, not architectural constants.
