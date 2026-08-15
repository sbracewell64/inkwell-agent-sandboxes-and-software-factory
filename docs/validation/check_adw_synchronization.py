#!/usr/bin/env -S uv run
# /// script
# dependencies = []
# ///
"""Deterministically synchronize installed, template, and generated ADWs."""

from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = Path(".claude/skills/sssf")
PACKAGE_BY_IMPORT = {
    "dotenv": "python-dotenv",
    "pydantic": "pydantic",
    "rich": "rich",
    "yaml": "pyyaml",
}
EXPECTED_RED_FIXTURES = frozenset({
    "exhaustive_match_finish",
    "infinite_loop_finish",
    "match-false-guard-unreachable-finish",
    "missing_export",
    "missing_finish",
    "missing_rich",
    "nested_compound_finish",
    "prompt_output_mismatch",
    "reachable_break_finish",
    "stale_run_succeeded",
    "unreachable_finish",
    "while-false-unreachable-finish",
})


@dataclass
class Inventory:
    surfaces: dict[str, int] = field(default_factory=dict)
    agent_calls: int = 0
    module_attributes: int = 0
    finish_calls: int = 0
    dependency_sets: int = 0
    prompt_reports: int = 0
    import_smokes: int = 0
    red_fixtures: int = 0


@dataclass(frozen=True)
class Surface:
    name: str
    scripts: tuple[Path, ...]
    modules: Path
    prompts: Path | None


def parse(path: Path, errors: list[str]) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError) as error:
        errors.append(f"{path}: cannot parse: {error}")
        return None


def module_trees(modules: Path, errors: list[str]) -> dict[str, tuple[Path, ast.Module]]:
    trees: dict[str, tuple[Path, ast.Module]] = {}
    if not modules.is_dir():
        errors.append(f"CNO: module directory not found: {modules}")
        return trees
    for path in sorted(modules.glob("*.py")):
        name = "adw_modules" if path.name == "__init__.py" else f"adw_modules.{path.stem}"
        tree = parse(path, errors)
        if tree is not None:
            trees[name] = (path, tree)
    if not trees:
        errors.append(f"CNO: no ADW modules discovered under {modules}")
    return trees


def exports(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(t.id for t in targets if isinstance(t, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name.split(".")[0])
    return names


def imported_module(current: str, node: ast.ImportFrom) -> str:
    if not node.level:
        return node.module or ""
    package = current.split(".")[:-node.level]
    if node.module:
        package.extend(node.module.split("."))
    return ".".join(package)


def check_import_graph(
    path: Path,
    tree: ast.Module,
    trees: dict[str, tuple[Path, ast.Module]],
    errors: list[str],
    inventory: Inventory,
) -> set[str]:
    external: set[str] = set()
    visited: set[str] = set()

    def visit(source_path: Path, source: ast.Module, module_name: str = "") -> None:
        aliases: dict[str, str] = {}
        for node in ast.walk(source):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root == "adw_modules" and alias.name in trees:
                        visit_module(alias.name)
                    elif root not in sys.stdlib_module_names:
                        external.add(root)
            elif isinstance(node, ast.ImportFrom):
                target = imported_module(module_name, node)
                if target == "adw_modules":
                    for alias in node.names:
                        child = f"adw_modules.{alias.name}"
                        if child in trees:
                            aliases[alias.asname or alias.name] = child
                            visit_module(child)
                        elif alias.name not in exports(trees[target][1]):
                            errors.append(f"{source_path}:{node.lineno}: missing import {target}.{alias.name}")
                elif target in trees:
                    available = exports(trees[target][1])
                    for alias in node.names:
                        if alias.name != "*" and alias.name not in available:
                            errors.append(f"{source_path}:{node.lineno}: missing import {target}.{alias.name}")
                    visit_module(target)
                elif target:
                    root = target.split(".")[0]
                    if root not in sys.stdlib_module_names and root != "adw_modules":
                        external.add(root)

        for node in ast.walk(source):
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id in aliases):
                inventory.module_attributes += 1
                target = aliases[node.value.id]
                if node.attr not in exports(trees[target][1]):
                    errors.append(
                        f"{source_path}:{node.lineno}: unresolved imported module attribute "
                        f"{target}.{node.attr}"
                    )

    def visit_module(name: str) -> None:
        if name in visited:
            return
        visited.add(name)
        module_path, module_tree = trees[name]
        visit(module_path, module_tree, name)

    visit(path, tree)
    return external


def dependencies(path: Path, errors: list[str]) -> set[str]:
    try:
        header = "\n".join(path.read_text(encoding="utf-8").splitlines()[:8])
        match = re.search(r"^# dependencies = (\[.*\])$", header, re.MULTILINE)
        if not match:
            errors.append(f"{path}: missing PEP 723 dependencies")
            return set()
        value = ast.literal_eval(match.group(1))
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError("dependencies must be a string list")
        return set(value)
    except (OSError, SyntaxError, ValueError) as error:
        errors.append(f"{path}: invalid PEP 723 dependencies: {error}")
        return set()


def expression_finish_calls(node: ast.AST | None) -> int:
    if node is None:
        return 0

    class Calls(ast.NodeVisitor):
        count = 0

        def visit_Call(self, call: ast.Call) -> None:
            if (isinstance(call.func, ast.Attribute) and call.func.attr == "finish"
                    and isinstance(call.func.value, ast.Name) and call.func.value.id == "run"):
                self.count += 1
            self.generic_visit(call)

        def visit_Lambda(self, _node: ast.Lambda) -> None:
            return

    visitor = Calls()
    visitor.visit(node)
    return visitor.count


@dataclass(frozen=True)
class Flow:
    finish_calls: int = 0
    exits: frozenset[str] = frozenset({"normal"})
    ambiguous: bool = False


def merge_flows(flows: list[Flow], prefix_calls: int = 0) -> Flow:
    return Flow(
        prefix_calls + sum(flow.finish_calls for flow in flows),
        frozenset().union(*(flow.exits for flow in flows)),
        any(flow.ambiguous for flow in flows),
    )


def irrefutable_pattern(pattern: ast.pattern) -> bool:
    return isinstance(pattern, ast.MatchAs) and pattern.pattern is None


def statement_flow(statement: ast.stmt) -> Flow:
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return Flow()
    if isinstance(statement, ast.Return):
        return Flow(expression_finish_calls(statement.value), frozenset({"return"}))
    if isinstance(statement, ast.Raise):
        return Flow(expression_finish_calls(statement.exc), frozenset({"raise"}))
    if isinstance(statement, ast.Break):
        return Flow(exits=frozenset({"break"}))
    if isinstance(statement, ast.Continue):
        return Flow(exits=frozenset({"continue"}))
    if isinstance(statement, ast.If):
        test_calls = expression_finish_calls(statement.test)
        constant = statement.test.value if isinstance(statement.test, ast.Constant) else None
        if constant is True:
            return merge_flows([reachable_finish_flow(statement.body)], test_calls)
        if constant is False:
            return merge_flows([reachable_finish_flow(statement.orelse)], test_calls)
        branches = [reachable_finish_flow(statement.body)]
        branches.append(reachable_finish_flow(statement.orelse) if statement.orelse else Flow())
        return merge_flows(branches, test_calls)
    if isinstance(statement, ast.Match):
        flows: list[Flow] = []
        exhaustive = False
        for case in statement.cases:
            guard_calls = expression_finish_calls(case.guard)
            if isinstance(case.guard, ast.Constant) and case.guard.value is False:
                flows.append(Flow(guard_calls))
                continue
            if case.guard is not None \
                    and not (isinstance(case.guard, ast.Constant) and case.guard.value is True):
                guarded = reachable_finish_flow(case.body)
                flows.append(Flow(
                    guard_calls + guarded.finish_calls,
                    guarded.exits | {"normal"},
                    True,
                ))
                continue
            flows.append(merge_flows([reachable_finish_flow(case.body)], guard_calls))
            if irrefutable_pattern(case.pattern):
                exhaustive = True
                break
        if not exhaustive:
            flows.append(Flow())
        return merge_flows(flows, expression_finish_calls(statement.subject))
    if isinstance(statement, (ast.With, ast.AsyncWith)):
        calls = sum(expression_finish_calls(item.context_expr) for item in statement.items)
        return merge_flows([reachable_finish_flow(statement.body)], calls)
    if isinstance(statement, (ast.For, ast.AsyncFor, ast.While)):
        control = getattr(statement, "iter", None) or getattr(statement, "test", None)
        control_calls = expression_finish_calls(control)
        is_never_entered = isinstance(statement, ast.While) \
            and isinstance(statement.test, ast.Constant) and statement.test.value is False
        if is_never_entered:
            else_flow = reachable_finish_flow(statement.orelse)
            return merge_flows([else_flow], control_calls)
        body = reachable_finish_flow(statement.body)
        is_infinite = isinstance(statement, ast.While) \
            and isinstance(statement.test, ast.Constant) and statement.test.value is True
        can_exhaust = not is_infinite
        else_flow = reachable_finish_flow(statement.orelse) if can_exhaust else Flow(exits=frozenset())
        exits = set(body.exits - {"normal", "continue", "break"}) | set(else_flow.exits)
        if "break" in body.exits:
            exits.add("normal")
        if can_exhaust and not statement.orelse:
            exits.add("normal")
        return Flow(
            control_calls + body.finish_calls + else_flow.finish_calls,
            frozenset(exits),
            body.ambiguous or else_flow.ambiguous,
        )
    if isinstance(statement, (ast.Try, ast.TryStar)):
        body = reachable_finish_flow(statement.body)
        normal_body = Flow(body.finish_calls, frozenset({"normal"}) if "normal" in body.exits else frozenset(), body.ambiguous)
        else_flow = reachable_finish_flow(statement.orelse) if "normal" in body.exits else Flow(exits=frozenset())
        handlers = [reachable_finish_flow(handler.body) for handler in statement.handlers]
        pre_final = merge_flows([
            Flow(0, body.exits - {"normal", "raise"}, body.ambiguous),
            merge_flows([normal_body, else_flow]) if statement.orelse else normal_body,
            *handlers,
            Flow(exits=frozenset({"raise"})),
        ])
        if not statement.finalbody:
            return pre_final
        final = reachable_finish_flow(statement.finalbody)
        exits = set(final.exits - {"normal"})
        if "normal" in final.exits:
            exits.update(pre_final.exits)
        return Flow(
            pre_final.finish_calls + final.finish_calls,
            frozenset(exits),
            pre_final.ambiguous or final.ambiguous,
        )
    simple = (
        ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Assert, ast.Delete, ast.Expr,
        ast.Global, ast.Import, ast.ImportFrom, ast.Nonlocal, ast.Pass,
    )
    if isinstance(statement, simple):
        return Flow(expression_finish_calls(statement))
    return Flow(exits=frozenset(), ambiguous=True)


def reachable_finish_flow(statements: list[ast.stmt]) -> Flow:
    count = 0
    exits: set[str] = set()
    normal = True
    ambiguous = False
    for statement in statements:
        if not normal:
            break
        flow = statement_flow(statement)
        count += flow.finish_calls
        exits.update(flow.exits - {"normal"})
        normal = "normal" in flow.exits
        ambiguous = ambiguous or flow.ambiguous
    if normal:
        exits.add("normal")
    return Flow(count, frozenset(exits), ambiguous)


def class_fields(
    tree: ast.Module,
) -> tuple[dict[str, ast.ClassDef], Callable[[str, set[str] | None], set[str]]]:
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}

    def fields(name: str, seen: set[str] | None = None) -> set[str]:
        seen = set() if seen is None else seen
        if name in seen or name not in classes:
            return set()
        seen.add(name)
        node = classes[name]
        result: set[str] = set()
        for base in node.bases:
            if isinstance(base, ast.Name):
                result.update(fields(base.id, seen))
        result.update(
            item.target.id for item in node.body
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
        )
        return result

    return classes, fields


def derives(classes: dict[str, ast.ClassDef], name: str, base_name: str) -> bool:
    if name not in classes:
        return False
    for base in classes[name].bases:
        if (isinstance(base, ast.Name)
                and (base.id == base_name or derives(classes, base.id, base_name))):
            return True
    return False


def check_prompts(
    prompt_dir: Path | None,
    data_types: ast.Module,
    errors: list[str],
    inventory: Inventory,
) -> None:
    if prompt_dir is None:
        return
    reports = sorted(prompt_dir.glob("*/user.md")) if prompt_dir.is_dir() else []
    reports = [path for path in reports if "## Report" in path.read_text(encoding="utf-8")]
    if not reports:
        errors.append(f"CNO: no prompt Report examples discovered under {prompt_dir}")
        return
    classes, fields = class_fields(data_types)
    for path in reports:
        text = path.read_text(encoding="utf-8")
        section = text.split("## Report", 1)[1]
        type_match = re.search(r"matching `([A-Za-z_]\w*)`", section)
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", section, re.DOTALL)
        if not type_match or not json_match:
            errors.append(f"{path}: Report must name an output type and contain a JSON example")
            continue
        output_type = type_match.group(1)
        try:
            example = json.loads(json_match.group(1))
        except json.JSONDecodeError as error:
            errors.append(f"{path}: invalid Report JSON: {error}")
            continue
        if output_type not in classes:
            errors.append(f"{path}: unknown Report output type {output_type}")
            continue
        expected = fields(output_type)
        actual = set(example) if isinstance(example, dict) else set()
        if actual != expected:
            errors.append(
                f"{path}: prompt/output fields mismatch for {output_type}: "
                f"missing={sorted(expected - actual)}, extra={sorted(actual - expected)}"
            )
        inventory.prompt_reports += 1


def check_script(
    path: Path,
    trees: dict[str, tuple[Path, ast.Module]],
    errors: list[str],
    inventory: Inventory,
) -> None:
    tree = parse(path, errors)
    if tree is None:
        return
    data_types = trees.get("adw_modules.data_types")
    if data_types is None:
        errors.append(f"CNO: {path}: adw_modules.data_types was not discovered")
        return
    classes, _ = class_fields(data_types[1])
    imported_types = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "adw_modules.data_types"
        for alias in node.names
    }
    for call in (node for node in ast.walk(tree) if isinstance(node, ast.Call)):
        is_agent_call = isinstance(call.func, ast.Name) and call.func.id == "AgentCall"
        if not is_agent_call:
            continue
        inventory.agent_calls += 1
        keyword = next((item for item in call.keywords if item.arg == "output_type"), None)
        if keyword is None or not isinstance(keyword.value, ast.Name):
            errors.append(f"{path}:{call.lineno}: AgentCall.output_type must be a concrete class name")
            continue
        name = keyword.value.id
        if name not in imported_types:
            errors.append(f"{path}:{call.lineno}: AgentCall.output_type {name} is not imported")
        if name == "EnvelopeBase" or not derives(classes, name, "EnvelopeBase"):
            errors.append(f"{path}:{call.lineno}: AgentCall.output_type {name} is not concrete")

    mains = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main"]
    if len(mains) != 1:
        errors.append(f"{path}: expected exactly one main(), found {len(mains)}")
    else:
        flow = reachable_finish_flow(mains[0].body)
        inventory.finish_calls += flow.finish_calls
        if flow.ambiguous:
            errors.append(f"CNO: {path}: unsupported or ambiguous control flow in main()")
        elif flow.finish_calls != 1:
            errors.append(
                f"{path}: reachable run.finish() calls: expected 1, found {flow.finish_calls}"
            )
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and node.attr == "succeeded"
                and isinstance(node.value, ast.Name) and node.value.id == "run"):
            errors.append(f"{path}:{node.lineno}: stale run.succeeded is not a finish path")

    imported = check_import_graph(path, tree, trees, errors, inventory)
    required = {PACKAGE_BY_IMPORT[name] for name in imported if name in PACKAGE_BY_IMPORT}
    unknown = sorted(name for name in imported if name not in PACKAGE_BY_IMPORT)
    if unknown:
        errors.append(f"{path}: unmapped external imports: {unknown}")
    declared = dependencies(path, errors)
    inventory.dependency_sets += 1
    if declared != required:
        errors.append(
            f"{path}: dependency/import mismatch: "
            f"missing={sorted(required - declared)}, extra={sorted(declared - required)}"
        )


def generate_surface(root: Path, temp: Path, errors: list[str]) -> Surface | None:
    generator = root / SKILL / "scripts/make_adw.py"
    if not generator.is_file():
        errors.append(f"CNO: ADW generator not found: {generator}")
        return None
    process = subprocess.run(
        [sys.executable, str(generator), "--name", "synchronization_smoke", "--agents",
         "planner,builder,scout,reviewer,documenter,custom"],
        cwd=temp,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    generated = temp / "adws/adw_synchronization_smoke.py"
    if process.returncode != 0 or not generated.is_file():
        errors.append(f"generated ADW smoke failed: {process.stdout.strip() or 'no output'}")
        return None
    source_modules = root / "adws/adw_modules"
    destination_modules = temp / "adws/adw_modules"
    shutil.copytree(source_modules, destination_modules)
    return Surface("generated", (generated,), destination_modules, None)


def import_smoke(script: Path, errors: list[str], inventory: Inventory) -> None:
    declared = sorted(dependencies(script, errors))
    uv = shutil.which("uv") or shutil.which("uv.exe")
    if uv is None:
        errors.append(f"{script}: import-only smoke could not observe uv")
        return
    command = [uv, "run", "--no-project"]
    for package in declared:
        command.extend(["--with", package])
    code = (
        "import importlib.util, pathlib, sys; "
        "p=pathlib.Path(sys.argv[1]); sys.path.insert(0,str(p.parent)); "
        "s=importlib.util.spec_from_file_location('generated_adw_smoke',p); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print('IMPORT_OK')"
    )
    command.extend(["python", "-c", code, str(script)])
    process = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if process.returncode != 0 or "IMPORT_OK" not in process.stdout.splitlines():
        errors.append(f"{script}: import-only smoke failed: {process.stdout.strip() or 'no output'}")
    else:
        inventory.import_smokes += 1


def validate(root: Path, *, smoke_import: bool = True) -> tuple[list[str], Inventory]:
    errors: list[str] = []
    inventory = Inventory()
    surfaces = [
        Surface(
            "installed",
            tuple(sorted((root / "adws").glob("adw_*.py"))),
            root / "adws/adw_modules",
            root / "adws/adw_data/prompt_engineering",
        ),
        Surface(
            "template",
            tuple(sorted((root / SKILL / "templates/adws").glob("adw_*.py"))),
            root / SKILL / "templates/adws/adw_modules",
            root / SKILL / "templates/prompt_engineering",
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="sssf-hd02-generated-") as directory:
        generated = generate_surface(root, Path(directory), errors)
        if generated is not None:
            surfaces.append(generated)
        for surface in surfaces:
            inventory.surfaces[surface.name] = len(surface.scripts)
            if not surface.scripts:
                errors.append(f"CNO: zero {surface.name} ADWs discovered")
                continue
            trees = module_trees(surface.modules, errors)
            for script in surface.scripts:
                check_script(script, trees, errors, inventory)
            data_types = trees.get("adw_modules.data_types")
            if data_types is not None:
                check_prompts(surface.prompts, data_types[1], errors, inventory)
        if smoke_import and generated is not None:
            import_smoke(generated.scripts[0], errors, inventory)
    return errors, inventory


def copy_fixture_root(source: Path, destination: Path) -> None:
    (destination / "adws").mkdir(parents=True)
    for script in (source / "adws").glob("adw_*.py"):
        shutil.copy2(script, destination / "adws" / script.name)
    shutil.copytree(source / "adws/adw_modules", destination / "adws/adw_modules")
    shutil.copytree(
        source / "adws/adw_data/prompt_engineering",
        destination / "adws/adw_data/prompt_engineering",
    )
    shutil.copytree(source / SKILL, destination / SKILL)


def run_red_fixtures(root: Path, errors: list[str], inventory: Inventory) -> None:
    fixture_dir = root / "docs/validation/fixtures/adw_sync"
    fixtures = sorted(fixture_dir.glob("*.json")) if fixture_dir.is_dir() else []
    if not fixtures:
        errors.append(f"CNO: no watched-red ADW synchronization fixtures under {fixture_dir}")
        return
    discovered = {fixture.stem for fixture in fixtures}
    if discovered != EXPECTED_RED_FIXTURES:
        errors.append(
            "CNO: watched-red fixture inventory mismatch: "
            f"missing={sorted(EXPECTED_RED_FIXTURES - discovered)}, "
            f"unexpected={sorted(discovered - EXPECTED_RED_FIXTURES)}"
        )
        return
    for fixture_path in fixtures:
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory(prefix=f"sssf-hd02-{fixture_path.stem}-") as directory:
            fixture_root = Path(directory)
            copy_fixture_root(root, fixture_root)
            target = fixture_root / fixture["path"]
            text = target.read_text(encoding="utf-8")
            old = fixture["old"]
            if text.count(old) != 1:
                errors.append(f"{fixture_path}: mutation anchor occurs {text.count(old)} times")
                continue
            target.write_text(text.replace(old, fixture["new"], 1), encoding="utf-8")
            fixture_errors, _ = validate(fixture_root, smoke_import=False)
            expected = fixture["expected"]
            if not fixture_errors:
                errors.append(f"{fixture_path}: stale mutation unexpectedly passed")
            elif not any(expected in error for error in fixture_errors):
                errors.append(
                    f"{fixture_path}: validator went red without expected {expected!r}: "
                    f"{fixture_errors[0]}"
                )
            else:
                inventory.red_fixtures += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root to validate")
    parser.add_argument("--skip-red-fixtures", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    errors, inventory = validate(root)
    if not args.skip_red_fixtures and not errors:
        run_red_fixtures(root, errors, inventory)
    red_controls_passed = (
        not args.skip_red_fixtures
        and inventory.red_fixtures == len(EXPECTED_RED_FIXTURES)
    )

    if errors:
        state = "CNO" if any(error.startswith("CNO:") for error in errors) else "FAIL"
        print(f"HD-02 ADW synchronization: {state}")
        for error in errors:
            print(f"- {error}")
        return 1

    print("HD-02 ADW synchronization: PASS")
    print("checked inventory:")
    for name, count in sorted(inventory.surfaces.items()):
        print(f"- {name} ADWs: {count}")
    print(f"- AgentCall.output_type declarations: {inventory.agent_calls}")
    print(f"- imported module attributes: {inventory.module_attributes}")
    print(f"- reachable run.finish() calls: {inventory.finish_calls}")
    print(f"- dependency/import sets: {inventory.dependency_sets}")
    print(f"- prompt Report contracts: {inventory.prompt_reports}")
    print(f"- generated import-only smokes: {inventory.import_smokes}")
    print(f"- watched-red fixtures: {inventory.red_fixtures}")
    if red_controls_passed:
        print("compound-reachability-red-controls: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
