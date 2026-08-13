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
