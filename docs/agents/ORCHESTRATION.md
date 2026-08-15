# Orchestration and Available Agents

## Current layers

### Browser GPT Sol High

Use as an **external supervisory/design authority**:

- architecture,
- defect diagnosis,
- increment design,
- review of evidence,
- acceptance recommendations,
- documentation planning.

It is outside the local runtime and therefore should not be treated as having implicitly executed local commands.

### Claude Code

The repository is designed to use Claude Code as an orchestrator through `/install`, `/prime`, and sandbox-agent paths.

When subscription quota is available, use Claude Code for repository-aware orchestration, but keep deterministic commands as the ground truth.

### Pi inside SSSF

Pi is the v1 coding-agent harness for ADW phases. Its strict execution seam is
`adws/adw_modules/pi_json_adapter.py`, backed by the provider-neutral owned
supervisor. The adapter requires exact provider/model, effort, and tool policy;
disables ambient sessions/resources/approval and fallback; and preserves a
typed terminal result. Refusal conditions and the current Windows execution
CNO are recorded in `docs/increments/B4-002_EXECUTOR_SUPERVISOR.md`.

The baseline proved Pi with a free OpenRouter model. B4-002 itself is
provider-free and does not re-qualify a model, credential transport, or roster.

## Recommended authority split

- **You / operator:** intent, irreversible business decisions, credentials.
- **Browser Sol:** supervisory reasoning and architectural approval.
- **Host orchestrator:** convert intent into deterministic SSSF/sandbox commands.
- **ADW code:** workflow state machine, retries, acceptance.
- **Pi role agents:** bounded reasoning/work.
- **deterministic gates/tests:** final claims where executable verification exists.

## Do not create a second sequencing authority

A browser agent, Claude orchestrator, and ADW must not each independently decide workflow progression.

The ADW/runtime remains the execution authority once a workflow is launched.
