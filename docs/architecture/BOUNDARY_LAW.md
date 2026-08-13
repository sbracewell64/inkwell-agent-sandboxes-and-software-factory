# Boundary Law

The central SSSF rule is:

> **Code owns sequencing, retries, and acceptance; agents own only the reasoning/work inside one bounded phase.**

## Consequences

### Code owns

- phase ordering,
- required-agent validation,
- retry budgets,
- gates,
- deterministic commands,
- permission enforcement,
- trace writes,
- commit conditions,
- final accepted/failed status.

### Agents own

- reading the bounded context,
- deciding within their assigned purpose,
- producing the typed output required by the phase,
- making only writes authorized by the roster.

### Typed envelopes cross seams

Agent prose is not the workflow contract. Concrete `EnvelopeBase` subclasses are.

The contract is a synchronized triad:

1. Python output type,
2. prompt JSON example,
3. `output_type=` at call sites.

### Gates validate claims

A model saying that a file exists is not proof. The gate checks the filesystem.

The baseline proved this twice:

- Nemotron declared plan artifacts that were absent; the gate rejected the phase.
- North Mini Code attempted a planner write outside `specs/`; permissions rolled it back.

### Known commands are code

If the command is known in advance, code executes it.

Example:

`bun test apps/inkwell/server.test.ts`

No tester agent is needed to rediscover a deterministic command.

## Design test for future increments

Before adding an agent, ask:

> Does this step require reading and deciding?

If no, make it code.

Before adding a new orchestration rule to a prompt, ask:

> Can deterministic code own this rule instead?

If yes, move it to code.
