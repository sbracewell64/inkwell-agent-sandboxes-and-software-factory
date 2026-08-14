set dotenv-load

# Unix keeps the engineer's interactive zsh environment so shell functions
# such as ipi remain available there.
#
# Windows deliberately uses cmd.exe for linewise root recipes. Windows SSSF
# must not require zsh merely to enter the factory or list its commands.
# Recipes with their own shebang bypass this setting entirely.
[unix]
set shell := ["zsh", "-ic"]

[windows]
set shell := ["cmd.exe", "/d", "/c"]

# Silences macOS's "Saving session..." on every interactive shell exit.
export SHELL_SESSIONS_DISABLE := "1"

# default config every run uses — override: SSSF_CONFIG=other.yaml just adw sdlc "..."
# (or pass --config in args)
# Still needed at root: the observability recipes below read the same roster/db.
config := env_var_or_default("SSSF_CONFIG", "adws/adw_sssf_config/sssf.config.yaml")

# Two layers, deliberately separate:
#   `mod adw`            — IN-sandbox execution. The ADWs themselves; identical
#                          whether run here or on a VM that has this repo.
#   `mod sbx`            — OUT-of-sandbox orchestration. Creates, fills, and
#                          observes the VMs the ADWs run inside. It ships to the
#                          sandbox like everything else; what a sandbox cannot do
#                          is USE it, because the exe.dev account and the
#                          OpenRouter provisioning key never leave the host.
# A module namespaces its recipes and inherits nothing from this file — see the
# header of just/adws.just for what that costs. An `import`, by contrast, shares
# its parent module's scope and working directory, which is why the phase files
# under just/sandbox/ are imports and carry no `set` lines of their own.

# boot and test the Inkwell app itself
mod inkwell 'just/inkwell.just'

# boot an orchestrator agent that works on THIS machine
mod local 'just/local.just'

# the ADWs themselves: just adw sdlc "..."
mod adw 'just/adws.just'

# sandbox orchestration: mount, execute, observe, tear down VMs
mod sbx 'just/sandbox/mod.just'

# read the trace db: sessions, phases, tail, procs
mod obs 'just/obs.just'

# list commands
default:
    @just --list

# ── raw ADW runs live in the module: just adw ──────────────────────────────