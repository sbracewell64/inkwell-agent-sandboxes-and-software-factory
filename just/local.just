# just/local.just — the `local` namespace: boot an orchestrator agent that works
# on THIS machine.
#
# `just local cc` drives the factory (the ADWs in `just adw`) right here.
# `just sbx ...` drives sandboxes, where the factory runs on a throwaway VM.
# The namespace is the answer to "where does the work happen".
#
# A MODULE inherits NOTHING from the root justfile, so shell and working
# directory settings are repeated deliberately.
#
# Unix preserves the original interactive-zsh behavior because ipi is a zsh
# function in the engineer environment.
#
# Windows uses cmd.exe so `just local`, `just local cc`, and `just local pi`
# do not require zsh. ipi is intentionally Unix-only.
[unix]
set shell := ["zsh", "-ic"]

[windows]
set shell := ["cmd.exe", "/d", "/c"]

set working-directory := '..'

export SHELL_SESSIONS_DISABLE := "1"

# list the local commands
default:
    @just --list local

# Claude Code orchestrator — reads the sssf overview, then handles your ask
cc:
    claude --dangerously-skip-permissions "Read and Execute .claude/skills/sssf/SKILL.md"

# Pi orchestrator — same posture, pi harness
pi:
    pi "Read and Execute .claude/skills/sssf/SKILL.md"

# ipi is a zsh function rather than a Windows binary.
[unix]
ipi:
    ipi "Read and Execute .claude/skills/sssf/SKILL.md" --no-skills