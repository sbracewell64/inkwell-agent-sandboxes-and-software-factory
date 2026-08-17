# Glossary

**ADW**  
AI Developer Workflow. A deterministic Python workflow containing bounded phases.

**agent**  
A configured model+harness+tools+prompt+write-boundary used inside a phase.

**agent session**  
The persisted context for one role invocation/correction sequence.

**envelope**  
Typed structured output crossing a phase seam.

**gate**  
Deterministic validation of an envelope's claims or resulting state.

**run_id**  
Sandbox lifecycle identity. Also used as the exe.dev VM name in the current provider.

**adw_id**  
Identity of one SSSF workflow execution inside a sandbox.

**roster**  
YAML configuration assigning models, prompts, tools, thinking, permissions, and harness extensions to named agents.

**harness**  
The coding-agent runtime used to execute a model with tools. SSSF v1 uses Pi for ADW agents.

**protected files**  
Factory machinery that ordinary agents cannot modify.

**writes**  
Per-agent repository path boundary enforced after an agent call.

**harvest**  
Extract the run branch/Git history from a sandbox into a host Git ref without merging it.

**teardown**  
Artifact collection, harvest, key revocation, VM destruction, run closure, and cleanup verification.

**baseline**  
An immutable source state with recorded proof and known limitations.

**increment**  
A bounded change from one trusted state to another, including proof and documentation.

**authority**

The single component whose copy of a field is definitive when copies disagree.

**mutation owner**

The single component permitted to change a field. A query projection and an archived evidence copy have none.

**canonical run state**

The SQLite rows that define what a run did. Not a derived copy of the run's files and not reconstructible from them.

**raw source**

Per field: which file, if any, still carries the fact once the trace database is gone — `none`, `complete:<file>`, or `partial:<file>`.

**triage state**

`sessions.archived`. A human's "I have looked at this run", written only by the visualizer's archive route and never by a run.
