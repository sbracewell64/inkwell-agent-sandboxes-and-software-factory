#!/usr/bin/env python3
"""Regression control for the shipped extension-bearing production ADW path.

Canonical `main` forwards every configured `harness_engineering` extension to
Pi as `-e <path>`. Shipped rosters populate that field nonempty for the planner
and scout, so a change that rejects configured extensions breaks those phases
before supervision or provider launch. No other offline check drives a shipped
nonempty `harness_engineering` configuration through the production launch
path, so that regression would pass a green gate unnoticed.

This control drives it. It makes no provider or model call: `PI_PATH` points at
a local recording stub that answers `--list-models` with the catalog rows the
configuration under test needs, records the argv it was launched with, and
emits one well-formed assistant event.

Two deliberate substitutions keep this runnable in the dependency-free offline
gate, which ships no pydantic, pyyaml, or dotenv:

- the shipped roster files are read by a small indentation-aware scan instead of
  pyyaml, and the scan must find a nonempty `harness_engineering` list or this
  control reports could-not-observe rather than passing vacuously;
- `agent_pi`'s two dependency-bearing imports are replaced by stdlib stand-ins.

Everything the assertion is about — request construction, argv assembly,
extension forwarding, and the rejection boundary — is the real `agent_pi`
source, not a stand-in.
"""

from __future__ import annotations

import json
import re
import stat
import sys
import tempfile
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools.ci_gate import COULD_NOT_OBSERVE_EXIT  # noqa: E402

CONFIG_DIR = ROOT / "adws" / "adw_sssf_config"
AGENT_NAME = re.compile(r"^(\s*)-\s+name:\s*(\S+)\s*$")
EXTENSION_KEY = re.compile(r"^(\s*)harness_engineering:\s*(\[\s*\])?\s*$")
LIST_ITEM = re.compile(r"^(\s*)-\s+(\S+)")

STUB = '''#!/usr/bin/env python3
"""Local stand-in for the Pi CLI. Records argv; never calls a provider."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()

if "--list-models" in sys.argv:
    print("PROVIDER MODEL CONTEXT")
    for provider, model_id in json.loads(HERE.with_suffix(".catalog.json").read_text()):
        print(f"{provider} {model_id} 272K")
    raise SystemExit(0)

HERE.with_suffix(".argv.json").write_text(json.dumps(sys.argv))
print(json.dumps({
    "type": "message_end",
    "message": {
        "role": "assistant",
        "content": [{"type": "text", "text": "typed-extension-path-marker"}],
        "usage": {},
    },
}))
raise SystemExit(0)
'''


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def shipped_extension_agents() -> list[tuple[str, str, str, list[str]]]:
    """Every shipped roster agent declaring a nonempty extension list.

    Returns (config file, agent name, model, extensions).
    """
    found = []
    for config_path in sorted(CONFIG_DIR.glob("*.config.yaml")):
        lines = config_path.read_text(encoding="utf-8").splitlines()
        agent_name = None
        agent_model = None
        # `load_config` fills an agent's unset `model` from `defaults`, so an
        # agent that declares none still ships a real target. Mirror that here
        # rather than driving the path with an empty model it never sees.
        defaults_model = None
        index = 0
        while index < len(lines):
            line = lines[index]
            name_match = AGENT_NAME.match(line)
            model_match = re.match(r"^\s*model:\s*(\S+)", line)
            if name_match:
                agent_name = name_match.group(2).strip('"\'')
                agent_model = None
            elif model_match and agent_name:
                agent_model = model_match.group(1).strip('"\'')
            elif model_match and defaults_model is None:
                defaults_model = model_match.group(1).strip('"\'')
            else:
                key_match = EXTENSION_KEY.match(line)
                if key_match and agent_name and not key_match.group(2):
                    extensions = []
                    cursor = index + 1
                    while cursor < len(lines):
                        item = LIST_ITEM.match(lines[cursor])
                        if not item or len(item.group(1)) <= len(key_match.group(1)):
                            break
                        extensions.append(item.group(2).strip('"\''))
                        cursor += 1
                    if extensions:
                        found.append((
                            config_path.name,
                            agent_name,
                            agent_model or defaults_model or "",
                            extensions,
                        ))
                    index = cursor
                    continue
            index += 1
    return found


def install_stdlib_stand_ins() -> None:
    """Serve `agent_pi`'s dependency-bearing imports from the standard library.

    The offline gate has no pydantic, pyyaml, or dotenv. Only the request and
    result carriers and two environment helpers are replaced; the module under
    test is loaded from its real source.
    """
    import os

    class PiUsage:
        def __init__(self) -> None:
            self.turns = []

        def add_turn(self, usage, turn) -> None:
            self.turns.append((usage, turn))

        def merge(self, other) -> None:
            self.turns.extend(getattr(other, "turns", []))

    class PiRequest:
        def __init__(self, **values) -> None:
            self.tools = None
            self.extensions = []
            self.cwd = "."
            self.thinking = "medium"
            for name, value in values.items():
                setattr(self, name, value)

    class PiResult:
        def __init__(self, **values) -> None:
            self.session_id = ""
            self.context_window = 0
            self.context_tokens = 0
            self.text = ""
            self.tokens = 0
            self.cost = 0.0
            self.returncode = 0
            self.terminal = {}
            self.usage = PiUsage()
            for name, value in values.items():
                setattr(self, name, value)

    data_types = types.ModuleType("adws.adw_modules.data_types")
    data_types.PiRequest = PiRequest
    data_types.PiResult = PiResult
    data_types.UsageBreakdown = PiUsage

    utils = types.ModuleType("adws.adw_modules.utils")
    utils.now_iso = lambda: "1970-01-01T00:00:00Z"
    utils.operator_env = lambda: os.environ.copy()
    utils.new_id = lambda size=4: "0" * size

    sys.modules["adws.adw_modules.data_types"] = data_types
    sys.modules["adws.adw_modules.utils"] = utils


def install_stub(directory: Path, models: list[str]) -> Path:
    stub = directory / "pi_stub.py"
    stub.write_text(STUB)
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    catalog = []
    for model in models:
        provider, _, model_id = model.partition("/")
        if provider and model_id:
            catalog.append([provider, model_id])
    stub.with_suffix(".catalog.json").write_text(json.dumps(catalog))
    if sys.platform == "win32":
        # CreateProcess cannot launch a Python script through its shebang. A
        # batch shim keeps PI_PATH directly executable on Windows while the
        # same local Python stub remains the argv recorder on every platform.
        launcher = directory / "pi_stub.cmd"
        launcher.write_text(
            f'@"{sys.executable}" "{stub}" %*\n',
            encoding="utf-8",
        )
        return launcher
    return stub


def main() -> int:
    errors: list[str] = []
    shipped = shipped_extension_agents()

    # Non-vacuity first: a control that drives no extension-bearing agent proves
    # nothing, and an empty result set is could-not-observe, never a pass.
    if not shipped:
        print("- could-not-observe: no shipped roster declares a nonempty harness_engineering agent")
        return COULD_NOT_OBSERVE_EXIT
    print("shipped extension-bearing agents:")
    for config_name, agent_name, model, extensions in shipped:
        print(f"  {config_name}:{agent_name} model={model} extensions={extensions}")

    install_stdlib_stand_ins()
    from adws.adw_modules import agent_pi  # noqa: E402 - after the stand-ins are installed
    from adws.adw_modules.data_types import PiRequest  # noqa: E402

    with tempfile.TemporaryDirectory(prefix="sssf-extension-path-") as directory:
        temp = Path(directory)
        stub = install_stub(temp, [model for _, _, model, _ in shipped])
        argv_record = stub.with_suffix(".argv.json")
        # The production path also reads the operator's merged Pi model
        # registry. Supply an empty one so the catalog answer comes from the
        # local stub instead of whatever is installed on the runner.
        registry = temp / "models.json"
        registry.write_text(json.dumps({"providers": {}}))
        original_path = agent_pi.PI_PATH
        original_registry = getattr(agent_pi, "MODELS_JSON", None)
        agent_pi.PI_PATH = str(stub)
        if original_registry is not None:
            agent_pi.MODELS_JSON = str(registry)
        if hasattr(agent_pi, "_pi_catalog"):
            agent_pi._pi_catalog.cache_clear()
        try:
            for config_name, agent_name, model, extensions in shipped:
                label = f"{config_name}:{agent_name}"
                if argv_record.exists():
                    argv_record.unlink()
                agent_dir = temp / config_name / agent_name
                agent_dir.mkdir(parents=True, exist_ok=True)
                request = PiRequest(
                    prompt="fixture prompt",
                    system_prompt="fixture system prompt",
                    model=model,
                    thinking="high",
                    session_id="sssf-fixture-session",
                    session_dir=str(agent_dir / "pi_sessions"),
                    raw_output_path=str(agent_dir / "raw_output.jsonl"),
                    execution_id="fixture-run",
                    phase_id="extension-path",
                    attempt_number=1,
                    tools=["read"],
                    extensions=extensions,
                    cwd=str(ROOT),
                    total_attempt_budget=1,
                )
                try:
                    agent_pi.run(request)
                except Exception as error:  # noqa: BLE001 - the rejection is the subject
                    errors.append(
                        f"{label}: configured extensions were rejected before launch: "
                        f"{type(error).__name__}: {error}"
                    )
                    continue
                if not argv_record.exists():
                    errors.append(f"{label}: could-not-observe: the launch recorded no argv")
                    continue
                argv = json.loads(argv_record.read_text())
                for extension in extensions:
                    forwarded = any(
                        argv[index] == "-e" and argv[index + 1] == extension
                        for index in range(len(argv) - 1)
                    )
                    check(forwarded, f"{label}: extension {extension!r} was not forwarded as -e", errors)
        finally:
            agent_pi.PI_PATH = original_path
            if original_registry is not None:
                agent_pi.MODELS_JSON = original_registry
            if hasattr(agent_pi, "_pi_catalog"):
                agent_pi._pi_catalog.cache_clear()

    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("production-extension-path: PASS")
    print("watched-red: configured extensions rejected before launch")
    print("provider-calls: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
