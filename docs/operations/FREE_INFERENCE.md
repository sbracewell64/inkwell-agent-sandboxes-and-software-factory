# Free Inference Record

## Proven working model

`openrouter/cohere/north-mini-code:free`

Baseline roles successfully exercised:

- planner
- builder

## Successful behavior

Planner:

- wrote both required plan artifacts,
- passed existence and non-empty gates,
- attempted one unauthorized app write,
- permissions rolled that write back.

Builder:

- first output did not contain valid `BuildOutput` JSON,
- same session was corrected,
- second output passed,
- tests passed,
- commit landed.

## Cost/performance observation

Proof ADW:

- tokens reported: 420,217
- cost reported: $0.0000
- planner duration: about 243.5 seconds
- builder duration: about 105.3 seconds

Treat these as one measured run, not guaranteed performance.

## Role qualification rule

A model is not qualified for a role because it appears in `pi --list-models`.

Qualification requires a representative task with the actual:

- prompt,
- tools,
- write boundary,
- typed output,
- gates.

## Free-model maintenance

When a free model changes:

1. create a roster experiment,
2. run a qualification fixture,
3. retain trace,
4. update this document,
5. promote only after evidence passes.
