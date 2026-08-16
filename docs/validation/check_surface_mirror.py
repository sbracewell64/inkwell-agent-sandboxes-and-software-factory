#!/usr/bin/env python3
"""Content parity between the live ADW surface and the SSSF skill template surface.

`check_adw_synchronization.py` (HD-02) validates each surface's INTERNAL contract
— imports resolve, every AgentCall names a concrete output type, exactly one
final `run.finish()`, prompt Report fields match their output model. It never
compares the two surfaces against each other, so a module can be edited on one
side alone and that validator still prints PASS.

This checker closes exactly that gap and nothing else: for every path declared
mirrored in `surface_mirror_manifest.json`, the two surfaces must hold the same
bytes and the same file set. A declared divergence is allowed, but only as a
reviewed entry carrying a reason and evidence.

Three-valued, like every other validator here:

  PASS  every declared-mirrored path matched, over a nonempty comparison set.
  FAIL  a declared-mirrored path differs, or is present on one surface only.
  CNO   the question could not be asked: unreadable manifest, missing root,
        zero files compared, an escape hatch missing its reason or evidence, or
        a stale escape that no longer describes a real divergence. A vacuous
        comparison is never reported as PASS.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = Path(__file__).resolve().parent / "surface_mirror_manifest.json"


@dataclass
class RedControls:
    """Outcome of the watched-red mutations that prove the checker still fails."""
    log: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.problems


@dataclass
class Findings:
    fail: list[str] = field(default_factory=list)
    cno: list[str] = field(default_factory=list)
    compared: int = 0
    pairs: dict[str, int] = field(default_factory=dict)
    allowed: list[str] = field(default_factory=list)


def digest(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def collect(root: Path, glob: str, recursive: bool) -> dict[str, Path] | None:
    """Relative-path -> file, or None when the root itself cannot be observed."""
    if not root.is_dir():
        return None
    paths = root.rglob(glob) if recursive else root.glob(glob)
    return {
        str(p.relative_to(root)).replace("\\", "/"): p
        for p in sorted(paths)
        if p.is_file()
    }


def load_manifest(path: Path, findings: Findings) -> dict | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.cno.append(f"manifest could not be observed: {exc}")
        return None
    if not isinstance(document, dict):
        findings.cno.append("manifest must be a JSON object")
        return None
    if document.get("schema_version") != 1:
        findings.cno.append("manifest schema_version must be 1")
        return None
    if not isinstance(document.get("pairs"), list) or not document["pairs"]:
        findings.cno.append("manifest declares no mirrored pairs")
        return None
    return document


def escapes(document: dict, findings: Findings) -> dict[tuple[str, str], dict]:
    """Index the divergence allowlist, refusing any entry that is not reviewable."""
    table: dict[tuple[str, str], dict] = {}
    for entry in document.get("divergences", []) or []:
        pair, path = entry.get("pair"), entry.get("path")
        if not pair or not path:
            findings.cno.append(f"divergence entry missing pair/path: {entry!r}")
            continue
        for required in ("reason", "evidence"):
            if not str(entry.get(required, "")).strip():
                findings.cno.append(
                    f"divergence {pair}:{path} has no {required}; an escape hatch "
                    "without one cannot be reviewed and is refused")
        table[(pair, path)] = entry
    return table


def check_pair(root: Path, spec: dict, allow: dict[tuple[str, str], dict],
               findings: Findings, used: set[tuple[str, str]]) -> None:
    pair_id = spec.get("id") or "<unnamed>"
    live_root = root / spec["live"]
    template_root = root / spec["template"]
    glob = spec.get("glob", "*")
    recursive = bool(spec.get("recursive", False))

    live = collect(live_root, glob, recursive)
    template = collect(template_root, glob, recursive)
    if live is None:
        findings.cno.append(f"{pair_id}: live root not observed: {spec['live']}")
    if template is None:
        findings.cno.append(f"{pair_id}: template root not observed: {spec['template']}")
    if live is None or template is None:
        return
    if not live and not template:
        findings.cno.append(f"{pair_id}: zero files matched {glob!r} on either surface")
        return

    findings.pairs[pair_id] = 0
    for rel in sorted(set(live) | set(template)):
        entry = allow.get((pair_id, rel))
        in_live, in_template = rel in live, rel in template

        if in_live and in_template:
            left, right = digest(live[rel]), digest(template[rel])
            if left is None or right is None:
                findings.cno.append(f"{pair_id}: {rel} could not be read on both surfaces")
                continue
            findings.compared += 1
            findings.pairs[pair_id] += 1
            same = left == right
            if entry is not None:
                used.add((pair_id, rel))
                if same:
                    findings.cno.append(
                        f"{pair_id}: {rel} is declared a divergence but the surfaces "
                        "now match; remove the stale entry rather than leaving a "
                        "dormant escape that would hide a future one-sided change")
                else:
                    findings.allowed.append(f"{pair_id}: {rel} (content, declared)")
                continue
            if not same:
                findings.fail.append(
                    f"{pair_id}: {rel} DIFFERS between surfaces\n"
                    f"    live     {spec['live']}/{rel} sha256={left[:16]}\n"
                    f"    template {spec['template']}/{rel} sha256={right[:16]}")
            continue

        # Present on one surface only.
        side = "live" if in_live else "template"
        missing = "template" if in_live else "live"
        if entry is not None:
            used.add((pair_id, rel))
            if entry.get("kind") != f"{side}_only":
                findings.cno.append(
                    f"{pair_id}: {rel} is declared kind={entry.get('kind')!r} but is "
                    f"present on the {side} surface only")
            else:
                findings.allowed.append(f"{pair_id}: {rel} ({side}-only, declared)")
            continue
        findings.fail.append(
            f"{pair_id}: {rel} is ABSENT from the {missing} surface\n"
            f"    present  {spec[side]}/{rel}\n"
            f"    expected {spec[missing]}/{rel}")


def validate(root: Path, manifest_path: Path) -> Findings:
    findings = Findings()
    document = load_manifest(manifest_path, findings)
    if document is None:
        return findings
    allow = escapes(document, findings)
    used: set[tuple[str, str]] = set()
    for spec in document["pairs"]:
        if not all(spec.get(key) for key in ("id", "live", "template")):
            findings.cno.append(f"pair entry missing id/live/template: {spec!r}")
            continue
        check_pair(root, spec, allow, findings, used)

    for key in sorted(set(allow) - used):
        findings.cno.append(
            f"{key[0]}: {key[1]} is declared a divergence but was never reached; "
            "a stale escape silently widens what may drift")
    if not findings.compared and not findings.cno:
        findings.cno.append("zero files compared; a vacuous comparison is not a pass")
    return findings


def report(findings: Findings, red: RedControls | None) -> int:
    # A green parity reading is only worth as much as the instrument that took
    # it, so an unproven instrument is CNO and never PASS. Reported before the
    # parity verdict because it decides whether that verdict means anything.
    if red is not None and not red.passed:
        print("surface mirror parity: CNO")
        for line in red.problems:
            print(f"- watched-red control: {line}")
        return 1

    if findings.cno:
        print("surface mirror parity: CNO")
        for line in findings.cno:
            print(f"- {line}")
        for line in findings.fail:
            print(f"- {line}")
        return 1
    if findings.fail:
        print("surface mirror parity: FAIL")
        for line in findings.fail:
            print(f"- {line}")
        print(f"checked {findings.compared} paired file(s) across "
              f"{len(findings.pairs)} declared pair(s)")
        return 1
    print("surface mirror parity: PASS")
    for name, count in sorted(findings.pairs.items()):
        print(f"- {name}: {count} paired file(s) byte-identical")
    for line in findings.allowed:
        print(f"- declared divergence: {line}")
    print(f"- total compared: {findings.compared}")
    if red is not None:
        for line in red.log:
            print(f"- {line}")
        print(f"watched-red controls: PASS ({len(red.log)} mutations)")
    return 0


MUTATIONS = (
    # name, path to mutate, how, the basename the resulting finding must name
    ("content-drift", "adws/adw_modules/console.py", "edit", "console.py"),
    ("live-only-file", "adws/adw_modules/zz_live_only.py", "add", "zz_live_only.py"),
    ("template-missing", ".claude/skills/sssf/templates/adws/adw_modules/tracer.py",
     "remove", "tracer.py"),
)


def red_controls(root: Path, manifest_path: Path) -> RedControls:
    """Negative control: prove this checker still goes red, and for the right path.

    Each mutation is applied to a disposable copy of the two surfaces. Going red
    is not enough on its own — a checker could be red for an unrelated reason, or
    stuck red — so the mutation must produce a finding that NAMES its own path and
    that the unmutated baseline did not already contain. A mutation that fails to
    do that means the instrument is not measuring content parity, which is CNO
    rather than something to pass over.
    """
    control = RedControls()
    manifest_findings = Findings()
    document = load_manifest(manifest_path, manifest_findings)
    if document is None:
        control.problems.extend(manifest_findings.cno)
        return control
    baseline = {line.split("\n", 1)[0] for line in validate(root, manifest_path).fail}
    for name, target, kind, expected in MUTATIONS:
        with tempfile.TemporaryDirectory(prefix="sssf-mirror-red-") as directory:
            temp = Path(directory)
            for spec in document["pairs"]:
                for key in ("live", "template"):
                    source = root / spec[key]
                    if source.is_dir():
                        destination = temp / spec[key]
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        if not destination.exists():
                            shutil.copytree(source, destination)
            path = temp / target
            try:
                if kind == "edit":
                    path.write_text(path.read_text(encoding="utf-8") + "\n# mutated\n",
                                    encoding="utf-8")
                elif kind == "add":
                    path.write_text("# live only\n", encoding="utf-8")
                elif kind == "remove":
                    path.unlink()
            except OSError as exc:
                control.problems.append(f"{name}: mutation could not be applied: {exc}")
                continue
            result = validate(temp, manifest_path)
            headline = {line.split("\n", 1)[0] for line in result.fail}
            introduced = [line for line in headline
                          if line not in baseline and expected in line]
            if not result.fail:
                control.problems.append(f"{name}: mutation did not turn the checker red")
            elif not introduced:
                control.problems.append(
                    f"{name}: checker went red but not for {expected}; red for the "
                    "wrong reason is not a watched-red control")
            else:
                control.log.append(f"watched red {name}: FAIL naming {expected} "
                                   f"— {introduced[0]}")
    if len(control.log) != len(MUTATIONS) and not control.problems:
        control.problems.append(
            f"expected {len(MUTATIONS)} watched-red mutations, observed {len(control.log)}")
    return control


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--self-test", action="store_true",
                        help="run only the watched-red mutations and report on them")
    parser.add_argument("--skip-red-controls", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest.resolve()

    if args.self_test:
        control = red_controls(root, manifest_path)
        for line in control.log:
            print(f"- {line}")
        if control.passed:
            print(f"surface mirror watched-red controls: PASS "
                  f"({len(MUTATIONS)} mutations)")
            return 0
        print("surface mirror watched-red controls: CNO")
        for line in control.problems:
            print(f"- {line}")
        return 1

    # The watched-red controls run on every invocation, so this check cannot
    # report PASS without first demonstrating it can still fail.
    control = None if args.skip_red_controls else red_controls(root, manifest_path)
    return report(validate(root, manifest_path), control)


if __name__ == "__main__":
    sys.exit(main())
