#!/usr/bin/env python3
"""What a FRESH `/sssf install` actually produces, checked against the contract.

`check_mapped_surface_parity.py` proves the two surfaces relate as declared. That
is necessary but not sufficient: it compares bytes in this repository and never
runs the installer, so a mapping that is correct on paper but wrong in
`install.py` would still pass. This validator closes that gap by stamping into a
disposable directory and asserting what a stamped repo really receives.

Two obligations, and both matter equally:

  PRESENT   the reconciled low-level substrate and the mapped prompt semantics
            reach a stamped repo — including the dormant supervisor/adapter pair,
            which stamps together or not at all.
  PRESERVED the intentional divergences survive stamping. A stamped repo must get
            the GENERIC scaffold, not this repository's concrete bodies. If
            `quality.py` arrived wired to Inkwell's paths, or the roster arrived
            as Inkwell's roster, the install would be leaking one project's
            specifics into every other project — the exact failure that makes
            flattening the surfaces wrong.

Three-valued: CNO when the stamp itself could not be observed, FAIL when a
declared expectation is violated, PASS only over a nonempty assertion set.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = Path(".claude/skills/sssf/scripts/install.py")
CONTRACT = Path(__file__).resolve().parent / "mapped_surface_contract.json"


def joined_path(node: ast.expr, base: str) -> str | None:
    parts: list[str] = []
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        if not isinstance(node.right, ast.Constant) or not isinstance(node.right.value, str):
            return None
        parts.append(node.right.value)
        node = node.left
    if not isinstance(node, ast.Name) or node.id != base:
        return None
    return "/".join(reversed(parts))


def installer_mappings(installer: Path) -> tuple[set[tuple[str, str]] | None, str | None]:
    try:
        tree = ast.parse(installer.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError) as exc:
        return None, f"installer mapping could not be parsed: {exc}"
    main = next((node for node in tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == "main"), None)
    if main is None:
        return None, "installer mapping source has no main()"
    mappings: set[tuple[str, str]] = set()
    calls = [node for node in ast.walk(main)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
             and node.func.id == "stamp"]
    for call in calls:
        if len(call.args) < 2:
            return None, "stamp() call in main() has fewer than two arguments"
        template = joined_path(call.args[0], "TEMPLATES")
        live = joined_path(call.args[1], "root")
        if template is None or live is None:
            return None, f"stamp() pair at line {call.lineno} is not statically observable"
        pair = (f".claude/skills/sssf/templates/{template}", live)
        if pair in mappings:
            return None, f"duplicate stamp() pair: {pair[0]} -> {pair[1]}"
        mappings.add(pair)
    if not mappings:
        return None, "main() contains no observable stamp() calls"
    return mappings, None


def contract_mappings(contract: Path) -> tuple[set[tuple[str, str]] | None, str | None]:
    try:
        document = json.loads(contract.read_text(encoding="utf-8"))
        surfaces = document["surfaces"]
        pairs = {(surface["template"], surface["live"]) for surface in surfaces}
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        return None, f"mapped-surface contract could not be observed: {exc}"
    if len(pairs) != len(surfaces):
        return None, "mapped-surface contract contains a duplicate template/live pair"
    return pairs, None


def reconcile_mapping(installer: Path, contract: Path) -> tuple[list[str], list[str]]:
    actual, actual_error = installer_mappings(installer)
    declared, declared_error = contract_mappings(contract)
    if actual_error or declared_error:
        return [], [error for error in (actual_error, declared_error) if error]
    failures = [f"installer stamp pair has no declared surface: {template} -> {live}"
                for template, live in sorted(actual - declared)]
    failures.extend(
        f"declared surface has no installer stamp pair: {template} -> {live}"
        for template, live in sorted(declared - actual))
    return failures, []


def mapping_red_control(installer: Path, contract: Path,
                        baseline: list[str]) -> tuple[bool, str]:
    source = installer.read_text(encoding="utf-8")
    target = 'root / "adws" / "adw_data" / "harness_engineering"'
    replacement = 'root / "adws" / "adw_data" / "harness_engineering_probe"'
    if source.count(target) != 1:
        return False, "precondition absent: unique harness_engineering stamp destination"
    with tempfile.TemporaryDirectory(prefix="sssf-stamp-map-red-") as directory:
        mutated = Path(directory) / "install.py"
        mutated.write_text(source.replace(target, replacement), encoding="utf-8")
        failures, cno = reconcile_mapping(mutated, contract)
    introduced = [line for line in failures
                  if line not in baseline and "harness_engineering_probe" in line]
    if cno:
        return False, f"mutation became unobservable: {cno[0]}"
    if not introduced:
        return False, "mutation did not turn reconciliation red naming its target pair"
    return True, "watched-red installer-mapping-drift: FAIL naming harness_engineering_probe"


def stamp(root: Path, target: Path) -> tuple[bool, str]:
    """Run the real installer into `target`, returning (observed, detail)."""
    installer = root / INSTALLER
    if not installer.is_file():
        return False, f"installer not found at {INSTALLER}"
    process = subprocess.run(
        [sys.executable, str(installer)],
        cwd=target, text=True, capture_output=True, check=False,
    )
    if process.returncode != 0:
        return False, (f"installer exited {process.returncode}: "
                       f"{(process.stderr or process.stdout).strip()[:400]}")
    return True, process.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()

    failures: list[str] = []
    cno: list[str] = []
    checked = 0

    mapping_failures, mapping_cno = reconcile_mapping(root / INSTALLER, CONTRACT)
    failures.extend(mapping_failures)
    cno.extend(mapping_cno)
    checked += 1
    if not mapping_cno:
        control_ok, control_detail = mapping_red_control(
            root / INSTALLER, CONTRACT, mapping_failures)
        if not control_ok:
            cno.append(control_detail)
        else:
            checked += 1

    with tempfile.TemporaryDirectory(prefix="sssf-stamp-fixture-") as directory:
        target = Path(directory)
        observed, detail = stamp(root, target)
        if not observed:
            print("stamped substrate: CNO")
            print(f"- fresh stamp could not be observed: {detail}")
            return 1

        modules = target / "adws/adw_modules"
        prompts = target / "adws/adw_data/prompt_engineering"

        # PRESENT — the reconciled substrate reaches a stamped repo.
        present = [
            ("subprocess_supervisor.py", modules / "subprocess_supervisor.py"),
            ("pi_json_adapter.py", modules / "pi_json_adapter.py"),
        ]
        for name, path in present:
            checked += 1
            if not path.is_file():
                failures.append(f"stamped repo is missing {name}; the template module "
                                "tree is documented as carrying all low-level logic")
        # The pair is only safe together: the adapter imports the supervisor.
        checked += 1
        both = all(path.is_file() for _, path in present)
        either = any(path.is_file() for _, path in present)
        if either and not both:
            failures.append("stamped repo carries one of the supervisor/adapter pair "
                            "without the other; the adapter imports the supervisor, so "
                            "this state is broken on import")

        checked += 1
        permissions = modules / "permissions.py"
        if not permissions.is_file():
            failures.append("stamped repo is missing permissions.py")
        elif "def preserve(" not in permissions.read_text(encoding="utf-8"):
            failures.append("stamped permissions.py lacks preserve(); a stamped repo "
                            "would report an operator's clobbered work as unrecoverable")

        checked += 1
        scout = prompts / "scout/system.md"
        if not scout.is_file():
            failures.append("stamped repo is missing the scout prompt")
        elif "never into the repo" not in scout.read_text(encoding="utf-8"):
            failures.append("stamped scout prompt lacks the scratch-output notice, so a "
                            "stamped repo's agents are not told about the rollback "
                            "mechanism their permissions module now enforces")

        # PRESERVED — intentional divergence survives the stamp.
        checked += 1
        quality = modules / "quality.py"
        if not quality.is_file():
            failures.append("stamped repo is missing quality.py")
        else:
            body = quality.read_text(encoding="utf-8")
            if "_placeholder(" not in body:
                failures.append("stamped quality.py is not the placeholder scaffold; a "
                                "stamped repo must not inherit another project's "
                                "concrete commands")
            if "apps/inkwell" in body:
                failures.append("stamped quality.py carries this repository's concrete "
                                "Inkwell paths; the scaffold divergence was flattened")

        checked += 1
        roster = target / "adws/adw_sssf_config/sssf.config.yaml"
        if not roster.is_file():
            failures.append("stamped repo is missing the roster config")
        else:
            live_roster = root / "adws/adw_sssf_config/sssf.config.yaml"
            if live_roster.is_file() and roster.read_bytes() == live_roster.read_bytes():
                failures.append("stamped roster is byte-identical to this repository's "
                                "roster; the user-owned divergence was flattened")

        # Non-vacuity: the assertions above are worthless if nothing was stamped.
        checked += 1
        stamped_files = [p for p in target.rglob("*") if p.is_file()]
        if len(stamped_files) < 20:
            cno.append(f"only {len(stamped_files)} file(s) stamped; too few to conclude "
                       "anything about the stamped substrate")

    if cno:
        print("stamped substrate: CNO")
        for line in cno + failures:
            print(f"- {line}")
        return 1
    if failures:
        print("stamped substrate: FAIL")
        for line in failures:
            print(f"- {line}")
        return 1
    print("stamped substrate: PASS")
    print(f"- {checked} expectation(s) checked against a fresh disposable stamp")
    print("- present: supervisor+adapter pair, permissions.preserve, mapped scout notice")
    print("- preserved: quality.py placeholder scaffold, user-owned roster divergence")
    print(f"- {control_detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
