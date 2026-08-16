# Install

`/sssf install` — stamp the entire factory out of the skill and into the current working directory.

## Run it

```bash
uv run .claude/skills/sssf/scripts/install.py
```

Run from the **target repo root** — the cwd is where everything lands. If the skill lives in your user scope, the path is `~/.claude/skills/sssf/scripts/install.py`.

## What gets stamped

`install.py` copies `templates/` into the cwd:

| Stamped | From | Tracked? |
|---|---|---|
| `adws/adw_sssf_config/sssf.config.yaml` | `templates/sssf.config.yaml` | yes — the agent roster |
| `.env.sample` | `templates/env.sample` | yes |
| `adws/adw_*.py` | `templates/adws/` | yes — the twelve starter ADWs |
| `adws/adw_modules/` | `templates/adws/adw_modules/` | yes — all low-level logic |
| `adws/adw_data/prompt_engineering/{planner,builder,scout,reviewer,documenter}/` | `templates/prompt_engineering/` | yes — **the user-owned home for prompts** |
| `adws/adw_data/harness_engineering/` | `templates/harness_engineering/` | yes — **the user-owned home for pi extensions** |
| `justfile` | `templates/justfile` | yes — starter recipes: `just demo`, the workflows, the trace reads, `just obs` |
| `adws/adw_data/sessions/`, `adws/adw_data/sssf.db` | created at runtime | no — gitignored |

The two `*_engineering` dirs mirror the two config keys of the same name: `prompt_engineering` is what an agent is told, `harness_engineering` is what its harness can do. Both are yours the moment they are stamped. Edit them in `adws/adw_data/`, never back inside the skill.

## The mapping is not a mirror

Read the "From" column again: **template paths stamp to different live paths.** `templates/prompt_engineering/` becomes `adws/adw_data/prompt_engineering/`, `templates/sssf.config.yaml` becomes `adws/adw_sssf_config/sssf.config.yaml`, `templates/env.sample` becomes `.env.sample`. The two surfaces are a *mapping*, not a mirror, so comparing them by relative path — `diff -rq adws .claude/skills/sssf/templates/adws` — is not a parity check. It reports correctly-mapped trees as missing and tells you nothing about the paths it does line up.

The authority for that mapping is the `stamp()` calls in `install.py`'s `main()`. **`docs/validation/mapped_surface_contract.json`** transcribes them and assigns every governed path exactly one relation:

| Relation | Meaning |
|---|---|
| `EXACT_MIRROR` | Mapped content identity is required. Fails closed on divergent bytes or a missing counterpart. The module tree and both `*_engineering` trees are this. |
| `CONTRACT_ONLY` | Bodies may diverge, but a **named** verifier proves a **named** property. The property is the obligation — a filename is not proof. |
| `TEMPLATE_SCAFFOLD` | The template copy is a deliberate placeholder a stamped repo is expected to replace. `adw_modules/quality.py` is this: its blocks ship as `echo`s that announce they are fake, because a stamped repo cannot guess your test runner. Its shared API (`run_inkwell_tests`, `run_inkwell_quality`) is still enforced by name. |
| `USER_OWNED` | Stamped once as a starter, then yours. `sssf.config.yaml`, `.env.sample` and the `justfile` are this — `install.py` skips them when they already exist, so divergence is the designed steady state, not drift. |
| `LIVE_ONLY` | Present in this repository by design and never stamped, such as the alternate rosters selected with `--config`. |

An added, removed, or divergent governed path with **no declared relation** is a non-pass, never a silent accept. `docs/validation/check_mapped_surface_parity.py` enforces this and emits the status as structured state; `docs/validation/check_stamped_substrate.py` stamps into a disposable directory and checks what a fresh install really receives. Both run in CI.

If you change a `stamp()` call, update the contract in the same commit — the contract is a transcription, and a stale transcription is worse than none.

`harness_engineering/` ships with `subagents.ts` — the pi extension backing `subagent_create` / `_continue` / `_list` / `_remove`, wired to the planner and scout in the starter roster.

## Idempotency

Re-running is safe. `install.py` skips **every** file that already exists — your config, your prompts, and previously stamped code alike — and reports what it skipped, so a second run doubles as a drift check. To refresh stamped code (`adw_modules/`, the starter `adw_*.py`) to the skill's current version, run with `--force` — but know that `--force` overwrites ALL existing stamped files, including `sssf.config.yaml` and `prompt_engineering/`, so commit or back up user-owned edits first.

## Post-install checklist

1. **Env** — `cp .env.sample .env`, then set `OPENROUTER_API_KEY` in `.env`. (v1 runs Pi; `ANTHROPIC_API_KEY` / `CLAUDE_CODE_PATH` are only needed once Claude Code lands in v2.)
2. **Pi is installed and on PATH** — `pi --version`. Set `PI_PATH` in `.env` if it is not.
3. **The model resolves** — the config's default `gemini-3.6-flash` must be a registered id in `~/.pi/agent/models.json`. Check with `pi --list-models` or read the file directly; see `references/config.md` for model resolution.
4. **Gitignore** — `install.py` appends `adws/adw_data/sessions/`, `adws/adw_data/sssf.db*`, and `.env` for you; confirm they landed. All three are runtime or secrets and must never be committed.
5. **Git repo** — ADWs that end in a commit phase call `git_helper.commit_all`, which raises if the cwd is not a git repository. Run `git init` and make a first commit before using `adw_plan_build.py`, `adw_plan_build_test.py`, or `adw_simple_sdlc.py`. `adw_document.py` needs one too: it measures the change with `git diff` against a base ref (`main` by default, `--base` to override).
6. **Smoke test** — `just demo` runs two cheap read-only workflows back to back, or run the smallest ADW directly:

```bash
just demo                                                    # both, end to end
uv run adws/adw_prompt.py "reply with a one-line summary of this repo"   # the raw form
```

Green means the whole path works: config validated, session minted, Pi ran, envelope parsed, events landed in `adws/adw_data/sssf.db`. Verify the trace exists before trusting anything larger:

```bash
sqlite3 adws/adw_data/sssf.db "select adw_id, status from sessions order by started_at desc limit 1;"
```

If the smoke test fails, fix it before composing chains — every multi-agent ADW rides on this exact path.
