# Agentless Research

## Status

`EXPLORE` / supporting research only.

This document preserves SSSF-relevant findings from:

- **Agentless: Demystifying LLM-based Software Engineering Agents**
- arXiv: `2407.01489`

The paper is evidence for choosing the lowest sufficient autonomy class; it is not an SSSF runtime or workflow adoption decision.

## Governing interpretation

The central SSSF lesson is:

> **Use deterministic narrowing first; escalate to bounded autonomy only for residual uncertainty.**

This reinforces the three value creators:

- ENGINEER owns VALUE and reserved AUTHORITY;
- AGENT owns UNCERTAINTY REDUCTION;
- CODE owns STATE TRANSITION and should remove uncertainty mechanically wherever stable/checkable structure can do so.

## Authorized durable findings

### 1. Lowest-sufficient-autonomy principle

SSSF should eventually select the lowest execution class capable of resolving the remaining uncertainty.

Conceptual ladder:

```text
CLASS A — deterministic code only
CLASS B — bounded semantic call(s) inside code-owned sequence
CLASS C — bounded autonomous DSH cell
CLASS D — bounded multi-agent DSH cell
```

Selection must be policy/code-owned using typed task/risk/uncertainty facts. An agent may recommend a class where classification itself is semantic, but cannot enlarge its own authority.

DSH should be treated as an escalation mechanism for residual uncertainty, not as the universal first execution mode.

Likely routing: FUT-010 and FUT-001/DSH admission policy.

### 2. Hierarchical context narrowing

Prefer progressively earned context over maximally supplied context.

Pattern:

```text
repository structure
    -> relevant files/modules
    -> symbols/elements
    -> exact edit locations
    -> bounded source windows
```

Cheap CODE-owned structure should narrow the search space before expensive model reasoning where practical. Candidate sources may include repository tree, symbol/LSP structure, imports/dependencies, changed-file neighborhoods, test ownership, call/reference graphs, Git history and retrieval signals.

This does not forbid broader autonomous search when narrowing evidence remains insufficient.

Likely routing: FUT-001 DSH-5, code-intelligence work, and future harness scorecard localization metrics.

### 3. Watched-red qualification for generated reproduction/verifier tests

A model-generated verifier is a proposal, not accepted evidence merely because it exists.

Where technically possible, a generated reproduction test intended to prove a repair should demonstrate discriminatory power on the exact pre-fix state:

```text
candidate verifier
   -> exact baseline
   -> expected defect/failure observed?
       no: reject/unproven verifier
       yes: bind watched-red evidence
   -> exact candidate
   -> expected repair behavior observed?
```

Positive controls, negative controls, exact source identity, verifier scope and applicable CNO semantics remain required under the governing VerificationContract.

The implementation/maker agent may propose a verifier but may not unilaterally remove or redefine acceptance obligations.

Likely routing: VerificationContract evolution, FUT-010, and later FUT-005..008 verifier work.

## Additional supporting findings retained without separate promotion

- measure localization separately from implementation quality so harness failures can be attributed;
- combine independent localization channels deterministically rather than relying on one open-ended search loop;
- preserve separate candidate hypotheses instead of prematurely merging diverse contexts;
- Best-of-N candidate count should be bounded by measured marginal value, not available parallelism;
- normalize candidate identity before comparing consensus to avoid formatting/noise masquerading as independent agreement;
- DSH must earn its complexity against a strong deterministic/bounded-agent baseline rather than against no-AI execution;
- WorkPackage/intake should be able to distinguish sufficient specification, fact discovery, engineering judgment, Captain decision, and underdetermined/CNO conditions.

## Negative boundaries

Do not:

- create an Agentless subsystem or duplicate workflow engine;
- make DSH mandatory for every engineering task;
- let an implementation agent exclude existing tests from acceptance on its own authority;
- treat majority agreement among generated patches as correctness;
- treat generated reproduction tests as accepted verifiers without qualification;
- dump maximum repository context into models merely because the context window permits it.

## Relationship to existing SSSF research

Paper #1 (`Code as Agent Harness`) establishes the need to measure the harness itself. This paper strengthens that by requiring the baseline to include the strongest simple deterministic/bounded-agent pipeline available.

Paper #2 (`Agentic Software Engineering`) supports risk/uncertainty-dependent autonomy. This paper adds an empirical simplicity prior: start from the lowest sufficient autonomy class and expand only when residual uncertainty requires it.

No roadmap sequence or FUT state is changed by this research record alone.
