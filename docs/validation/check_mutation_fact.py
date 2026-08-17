#!/usr/bin/env python3
"""Deterministic proof for the HD-04 mutation fact and its bidirectional claims check.

Every control below builds a real repository, drives a real mutation, and asserts
the PROPERTY — normalized path plus content identity — never a count, a message,
or an exit code the implementation could be tuned to satisfy.

The pre-HD-04 gate is preserved here as `path_existence_proxy`, and the pre-HD-04
permission fingerprint as `numstat_fingerprint`. Each defect control watches the
old surface go green (or, for a truthful deletion claim, wrongly red) on the same
fixture where the reconciliation goes red, so no control can be vacuously red.

Dependency-free on purpose: this runs on a CI runner that installs nothing.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from adws.adw_modules.mutation_fact import (  # noqa: E402
    KIND_ADDED,
    KIND_DELETED,
    KIND_MODIFIED,
    OUT_OF_SCOPE_CLASSES,
    MutationObservation,
    TreeFact,
    normalize_claim,
    observe,
    reconcile,
)

# What a verdict must refuse to imply. Named here as well as in the module so a
# silent narrowing of the boundary breaks a control instead of a reader's trust.
REQUIRED_OUT_OF_SCOPE = ("gitignored", "outside the repository", "network", "process")


# ── fixture ──────────────────────────────────────────────────────────────────

class Fixture:
    """A disposable repository with a pinned identity and no ambient git config."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.env = dict(os.environ)
        # Neither the operator's global config nor the runner's system config
        # may reach these repositories: the controls assert exact blob identity,
        # and an inherited filter or rename setting would decide the answer.
        self.env.update({
            "GIT_CONFIG_GLOBAL": str(root / "absent-global-config"),
            "GIT_CONFIG_SYSTEM": str(root / "absent-system-config"),
            "GIT_AUTHOR_NAME": "hd04", "GIT_AUTHOR_EMAIL": "hd04@example.invalid",
            "GIT_COMMITTER_NAME": "hd04", "GIT_COMMITTER_EMAIL": "hd04@example.invalid",
            "GIT_AUTHOR_DATE": "2026-08-16T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-08-16T00:00:00+00:00",
        })
        self.git("init", "-q")
        self.git("config", "core.autocrlf", "false")

    def git(self, *args: str) -> str:
        result = subprocess.run(["git", *args], cwd=str(self.root), env=self.env,
                                capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
        return result.stdout

    def write(self, path: str, text: str) -> None:
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode())

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def observe(self) -> TreeFact:
        return observe(self.root)


# ── the surfaces HD-04 replaces, kept as calibration cases ───────────────────

def path_existence_proxy(root: Path, claims) -> str:
    """The pre-HD-04 `diff_matches_claims`: one direction, existence only."""
    checks = [(root / claim).exists() for claim in claims]
    if not checks:
        return "no-observation"          # HD-03 already refuses this as CNO
    return "green" if all(checks) else "red"


def numstat_fingerprint(fixture: Fixture) -> dict[str, str]:
    """The pre-HD-04 permission fingerprint: line counts, not content identity."""
    prints: dict[str, str] = {}
    for line in fixture.git("diff", "HEAD", "--numstat").splitlines():
        fields = line.split("\t")
        if len(fields) >= 3:
            prints[fields[-1].strip()] = f"{fields[0]},{fields[1]}"
    for path in fixture.git("ls-files", "--others", "--exclude-standard").splitlines():
        if path.strip():
            prints[path.strip()] = "untracked"
    return prints


# ── controls ─────────────────────────────────────────────────────────────────

def control_honest_exact_set(fixture: Fixture) -> list[str]:
    """An honest, exact claim set agrees — so nothing below is vacuously red."""
    fixture.write("kept.py", "one\n")
    fixture.write("edited.py", "before\n")
    fixture.write("removed.py", "gone soon\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("edited.py", "after\n")
    fixture.write("created.py", "new\n")
    (fixture.root / "removed.py").unlink()
    result = reconcile(MutationObservation.between(before, fixture.observe()),
                       ["edited.py", "created.py", "removed.py"])

    errors = []
    if result.discrepancies:
        errors.append(f"honest exact set reported {result.discrepancies} discrepancy(ies)")
    if {m.path for m in result.agreed} != {"edited.py", "created.py", "removed.py"}:
        errors.append(f"agreement did not cover the exact set: {result.agreed}")
    if {m.kind for m in result.agreed} != {KIND_MODIFIED, KIND_ADDED, KIND_DELETED}:
        errors.append(f"mutation kinds did not resolve: {[m.kind for m in result.agreed]}")
    if not result.complete:
        errors.append(f"an honest set was reported incomplete: {result.unobservable}")
    return errors


def control_unchanged_claimed_path_fails(fixture: Fixture) -> list[str]:
    """A claim on an existing file nobody touched must not pass."""
    fixture.write("touched.py", "one\n")
    fixture.write("untouched.py", "still here\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("touched.py", "two\n")
    result = reconcile(MutationObservation.between(before, fixture.observe()),
                       ["touched.py", "untouched.py"])

    errors = []
    if [m.path for m in result.unmatched] != ["untouched.py"]:
        errors.append(f"an unchanged claimed path was not refused: {result.unmatched}")
    if result.unclaimed:
        errors.append(f"unexpected unclaimed paths: {result.unclaimed}")
    proxy = path_existence_proxy(fixture.root, ["touched.py", "untouched.py"])
    if proxy != "green":
        errors.append(f"watched-red lost: the path-existence proxy was {proxy}, not green")
    return errors


def control_omitted_changed_path_fails(fixture: Fixture) -> list[str]:
    """A real change left out of the claim set must not pass."""
    fixture.write("a.py", "one\n")
    fixture.write("b.py", "one\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("a.py", "two\n")
    fixture.write("b.py", "two\n")
    result = reconcile(MutationObservation.between(before, fixture.observe()), ["a.py"])

    errors = []
    if [m.path for m in result.unclaimed] != ["b.py"]:
        errors.append(f"an omitted changed path was not caught: {result.unclaimed}")
    proxy = path_existence_proxy(fixture.root, ["a.py"])
    if proxy != "green":
        errors.append(f"watched-red lost: the path-existence proxy was {proxy}, not green")
    return errors


def control_extra_actual_path_fails(fixture: Fixture) -> list[str]:
    """A path the agent introduced outside its claim set must not pass."""
    fixture.write("a.py", "one\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("a.py", "two\n")
    fixture.write("scratch.tmp", "left behind\n")
    result = reconcile(MutationObservation.between(before, fixture.observe()), ["a.py"])

    errors = []
    if [m.path for m in result.unclaimed] != ["scratch.tmp"]:
        errors.append(f"an extra actual path was not caught: {result.unclaimed}")
    if [m.kind for m in result.unclaimed] != [KIND_ADDED]:
        errors.append(f"the extra path did not resolve as an addition: {result.unclaimed}")
    proxy = path_existence_proxy(fixture.root, ["a.py"])
    if proxy != "green":
        errors.append(f"watched-red lost: the path-existence proxy was {proxy}, not green")
    return errors


def control_empty_claim_over_real_change_fails(fixture: Fixture) -> list[str]:
    """`changed_files=[]` while the tree moved is a concealed change, not silence."""
    fixture.write("a.py", "one\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("a.py", "two\n")
    result = reconcile(MutationObservation.between(before, fixture.observe()), [])

    errors = []
    if [m.path for m in result.unclaimed] != ["a.py"]:
        errors.append(f"an empty claim over a real change was not caught: {result.unclaimed}")
    # HD-03 already refused the empty declaration as could-not-observe rather
    # than a green. HD-04 upgrades it: the change is now positively named.
    proxy = path_existence_proxy(fixture.root, [])
    if proxy != "no-observation":
        errors.append(f"the empty-claim proxy calibration changed: {proxy}")
    return errors


def control_already_dirty_content_change_is_detected(fixture: Fixture) -> list[str]:
    """An edit on an already-dirty file, invisible to the line-count fingerprint."""
    fixture.write("dirty.py", "keep\noriginal\n")
    fixture.commit("baseline")
    fixture.write("dirty.py", "keep\noperator edit\n")     # dirty before the phase
    before = fixture.observe()
    before_prints = numstat_fingerprint(fixture)

    fixture.write("dirty.py", "keep\nagent edit\n")        # same shape, other bytes
    after = fixture.observe()
    after_prints = numstat_fingerprint(fixture)
    observation = MutationObservation.between(before, after)

    errors = []
    if before_prints != after_prints:
        errors.append("watched-red lost: the line-count fingerprint moved, so this "
                      "fixture no longer demonstrates the proxy's blind spot")
    mutations = [m for m in observation.mutations if m.path == "dirty.py"]
    if len(mutations) != 1 or mutations[0].kind != KIND_MODIFIED:
        errors.append(f"an already-dirty content change was missed: {observation.mutations}")
    elif mutations[0].before_oid == mutations[0].after_oid:
        errors.append("content identity did not move on an observed modification")
    if reconcile(observation, []).discrepancies != 1:
        errors.append("the already-dirty change was not reconciled as a discrepancy")
    return errors


def control_rename_is_deterministic(fixture: Fixture) -> list[str]:
    """A rename resolves from content identity, not from a similarity score."""
    fixture.write("old/name.py", "content\n")
    fixture.commit("baseline")
    before = fixture.observe()
    (fixture.root / "new").mkdir()
    (fixture.root / "old/name.py").rename(fixture.root / "new/name.py")

    errors = []
    # git's own rename detection is a configurable heuristic. The fact must not
    # move when that configuration does.
    observations = []
    for setting in ("true", "false"):
        fixture.git("config", "diff.renames", setting)
        observations.append(MutationObservation.between(before, fixture.observe()).mutations)
    if observations[0] != observations[1]:
        errors.append("the rename fact changed with diff.renames: "
                      f"{observations[0]} vs {observations[1]}")

    mutations = {m.path: m for m in observations[0]}
    if set(mutations) != {"old/name.py", "new/name.py"}:
        errors.append(f"a rename did not resolve to both paths: {sorted(mutations)}")
        return errors
    if mutations["old/name.py"].kind != KIND_DELETED or mutations["new/name.py"].kind != KIND_ADDED:
        errors.append(f"rename kinds did not resolve: {mutations}")
    if (mutations["old/name.py"].rename_peer != "new/name.py"
            or mutations["new/name.py"].rename_peer != "old/name.py"):
        errors.append(f"the rename pair was not linked by content identity: {mutations}")

    observation = MutationObservation.between(before, fixture.observe())
    if reconcile(observation, ["new/name.py"]).discrepancies != 1:
        errors.append("claiming only a rename's destination was not caught")
    if reconcile(observation, ["new/name.py", "old/name.py"]).discrepancies != 0:
        errors.append("claiming both halves of a rename did not agree")
    return errors


def control_ambiguous_rename_resolves_the_same_way_every_time(fixture: Fixture) -> list[str]:
    """Two deletions carrying identical bytes must not make the answer a coin flip."""
    fixture.write("a.py", "identical\n")
    fixture.write("b.py", "identical\n")
    fixture.commit("baseline")
    before = fixture.observe()
    (fixture.root / "a.py").unlink()
    (fixture.root / "b.py").unlink()
    fixture.write("c.py", "identical\n")

    errors = []
    rounds = [MutationObservation.between(before, fixture.observe()).mutations
              for _ in range(3)]
    if any(round_ != rounds[0] for round_ in rounds):
        errors.append(f"an ambiguous rename pairing was not stable: {rounds}")
    peers = {m.path: m.rename_peer for m in rounds[0]}
    if peers.get("c.py") != "a.py" or peers.get("a.py") != "c.py":
        errors.append(f"ambiguous pairing did not follow path order: {peers}")
    if peers.get("b.py") is not None:
        errors.append(f"a second candidate was paired to the same addition: {peers}")
    # Whatever the pairing, no path may fall out of the required claim set.
    observation = MutationObservation.between(before, fixture.observe())
    if reconcile(observation, ["a.py", "b.py", "c.py"]).discrepancies != 0:
        errors.append("claiming every path of an ambiguous rename did not agree")
    if reconcile(observation, ["c.py", "a.py"]).discrepancies != 1:
        errors.append("an ambiguous rename let an unclaimed deletion through")
    return errors


def control_deletion_is_deterministic(fixture: Fixture) -> list[str]:
    """A deleted path is a mutation, and claiming it truthfully must pass."""
    fixture.write("doomed.py", "content\n")
    fixture.write("kept.py", "content\n")
    fixture.commit("baseline")
    before = fixture.observe()
    (fixture.root / "doomed.py").unlink()
    observation = MutationObservation.between(before, fixture.observe())

    errors = []
    mutations = {m.path: m for m in observation.mutations}
    if set(mutations) != {"doomed.py"} or mutations["doomed.py"].kind != KIND_DELETED:
        errors.append(f"a deletion did not resolve: {observation.mutations}")
    elif mutations["doomed.py"].after_oid is not None:
        errors.append("a deleted path kept a content identity")
    if reconcile(observation, ["doomed.py"]).discrepancies != 0:
        errors.append("a truthful deletion claim was refused")
    if reconcile(observation, []).discrepancies != 1:
        errors.append("an unclaimed deletion was not caught")
    # The old gate had the deletion case exactly backwards: it demanded the
    # claimed path still EXIST, so an honest deletion claim went red.
    proxy = path_existence_proxy(fixture.root, ["doomed.py"])
    if proxy != "red":
        errors.append(f"watched-red lost: the path-existence proxy was {proxy} on a "
                      "truthful deletion claim, so it no longer shows the old defect")
    return errors


def control_untracked_is_deterministic(fixture: Fixture) -> list[str]:
    """An untracked, non-ignored file is an addition; an ignored one is outside."""
    fixture.write(".gitignore", "ignored/\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("fresh.py", "new\n")
    fixture.write("ignored/secret.log", "invisible\n")
    observation = MutationObservation.between(before, fixture.observe())

    errors = []
    if [m.path for m in observation.mutations] != ["fresh.py"]:
        errors.append(f"untracked resolution is not exact: {observation.mutations}")
    elif observation.mutations[0].kind != KIND_ADDED:
        errors.append(f"an untracked file did not resolve as an addition: {observation.mutations}")
    if reconcile(observation, ["fresh.py"]).discrepancies != 0:
        errors.append("a truthful untracked claim was refused")
    if reconcile(observation, ["ignored/secret.log"]).discrepancies != 2:
        errors.append("claiming an ignored path did not read as unmatched plus unclaimed")
    return errors


def control_boundary_is_stated_and_real(fixture: Fixture) -> list[str]:
    """The verdict names its universe, and the boundary it names is the real one."""
    fixture.write(".gitignore", "*.log\n")
    fixture.write("a.py", "one\n")
    fixture.commit("baseline")
    before = fixture.observe()

    fixture.write("a.py", "two\n")
    fixture.write("out-of-fact.log", "an ignored write really did happen\n")
    result = reconcile(MutationObservation.between(before, fixture.observe()), ["a.py"])

    errors = []
    if result.discrepancies:
        errors.append(f"the ignored write leaked into the fact: {result.unclaimed}")
    stated = " ".join(result.out_of_scope_classes).lower()
    missing = [phrase for phrase in REQUIRED_OUT_OF_SCOPE if phrase not in stated]
    if missing:
        errors.append(f"the verdict does not state it excludes {missing}")
    if not result.observed_classes:
        errors.append("the verdict states no observed universe at all")
    # The point of the control: agreement here is bounded agreement. The write
    # is genuinely on disk and genuinely absent from the fact.
    if not (fixture.root / "out-of-fact.log").exists():
        errors.append("the out-of-scope fixture write did not happen")
    return errors


def control_incomplete_universe_is_not_negative(fixture: Fixture) -> list[str]:
    """An unreadable candidate forces could-not-observe, never a clean negative."""
    fixture.write("swapped", "a file, for now\n")
    fixture.commit("baseline")
    before = fixture.observe()

    # A tracked path replaced by a directory: git still names it as changed, it
    # still exists on disk, and its working-tree content cannot be hashed.
    (fixture.root / "swapped").unlink()
    (fixture.root / "swapped").mkdir()
    (fixture.root / "swapped" / "inside.txt").write_bytes(b"x\n")
    after = fixture.observe()

    errors = []
    if "swapped" not in after.unobservable:
        errors.append(f"an unreadable candidate was not named: {after.unobservable}")
    result = reconcile(MutationObservation.between(before, after), [])
    if result.complete:
        errors.append("a universe with an unreadable candidate reported complete")
    if not result.unobservable:
        errors.append("the reconciliation dropped the unreadable candidate")

    # ...and the same rule holds for a fact whose hole came from anywhere else.
    injected = MutationObservation.between(
        before, replace(after, unobservable={"<any>": "could not be read"}))
    if reconcile(injected, []).complete:
        errors.append("an injected observation hole did not make the result incomplete")
    return errors


def control_claims_are_normalized_before_comparison(fixture: Fixture) -> list[str]:
    """A path written differently is the same path; one written elsewhere is not."""
    fixture.write("pkg/mod.py", "one\n")
    fixture.commit("baseline")
    before = fixture.observe()
    fixture.write("pkg/mod.py", "two\n")
    observation = MutationObservation.between(before, fixture.observe())

    errors = []
    for spelling in ("pkg/mod.py", "./pkg/mod.py", "pkg\\mod.py",
                     str(fixture.root / "pkg" / "mod.py")):
        result = reconcile(observation, [spelling])
        if result.discrepancies:
            errors.append(f"claim spelling {spelling!r} did not place: {result.unmatched}")

    outside = reconcile(observation, ["pkg/mod.py", str(Path(fixture.root).parent / "elsewhere.py")])
    if len(outside.unmatched) != 1 or "outside" not in outside.unmatched[0].problem:
        errors.append(f"an out-of-repository claim was not refused: {outside.unmatched}")
    placed, problem = normalize_claim("   ", str(fixture.root))
    if placed is not None or not problem:
        errors.append("an empty claim was placed instead of refused")
    return errors


def control_no_repository_is_not_a_pass(fixture: Fixture) -> list[str]:
    """With nothing to measure against, the answer is a hole, not an agreement."""
    errors = []
    with tempfile.TemporaryDirectory(prefix="sssf-hd04-bare-") as directory:
        fact = observe(Path(directory))
        if fact.repo_root is not None or not fact.unobservable:
            errors.append(f"a non-repository produced a usable fact: {fact}")
        result = reconcile(MutationObservation.between(fact, fact), ["anything.py"])
        if result.complete:
            errors.append("a non-repository reconciliation reported a complete universe")
        if len(result.unmatched) != 1:
            errors.append(f"a claim with no repository was not refused: {result.unmatched}")
    return errors


# ── the wiring the controls above cannot reach without pydantic ──────────────

def control_one_fact_two_consumers(_: Fixture) -> list[str]:
    """The claim gate and the permission check must read ONE observation.

    Asserted on the source rather than by running an agent: the point is that
    neither consumer takes its own snapshot, and that is a property of the call
    graph, not of any particular run.
    """
    import ast

    errors = []
    agents_src = (ROOT / "adws/adw_modules/agents.py").read_text(encoding="utf-8")
    gates_src = (ROOT / "adws/adw_modules/gates.py").read_text(encoding="utf-8")
    permissions_src = (ROOT / "adws/adw_modules/permissions.py").read_text(encoding="utf-8")
    for name, source in (("agents", agents_src), ("gates", gates_src),
                         ("permissions", permissions_src)):
        try:
            ast.parse(source)
        except SyntaxError as error:
            errors.append(f"{name}.py did not parse: {error}")
            return errors

    if "run.mutation = mutation_fact.MutationObservation.between(" not in agents_src:
        errors.append("agents.py does not publish one mutation observation per attempt")
    if "after=run.mutation.after" not in agents_src:
        errors.append("agents.py does not hand the published fact to the permission check")
    if "mutation_fact.observation_of(run)" not in gates_src:
        errors.append("the claim gate does not read the published fact")
    if "def diff_matches_claims" in gates_src and "hash-object" in gates_src:
        errors.append("the claim gate computes its own fact instead of reading one")
    if "after = snapshot(run) if after is None else after" not in permissions_src:
        errors.append("permissions.enforce does not prefer the handed-in fact")
    return errors


CONTROLS = (
    control_honest_exact_set,
    control_unchanged_claimed_path_fails,
    control_omitted_changed_path_fails,
    control_extra_actual_path_fails,
    control_empty_claim_over_real_change_fails,
    control_already_dirty_content_change_is_detected,
    control_rename_is_deterministic,
    control_ambiguous_rename_resolves_the_same_way_every_time,
    control_deletion_is_deterministic,
    control_untracked_is_deterministic,
    control_boundary_is_stated_and_real,
    control_incomplete_universe_is_not_negative,
    control_claims_are_normalized_before_comparison,
    control_no_repository_is_not_a_pass,
    control_one_fact_two_consumers,
)


def main() -> int:
    if shutil.which("git") is None:
        print("FAIL: could-not-observe: git is unavailable, so no mutation fact "
              "control could run")
        return 1
    if not CONTROLS:
        print("FAIL: could-not-observe: zero controls discovered")
        return 1

    errors: list[str] = []
    executed = 0
    for control in CONTROLS:
        with tempfile.TemporaryDirectory(prefix="sssf-hd04-") as directory:
            try:
                found = control(Fixture(Path(directory).resolve()))
            except Exception as error:                     # noqa: BLE001 - reported
                found = [f"raised {type(error).__name__}: {error}"]
            executed += 1
            status = "PASS" if not found else "FAIL"
            print(f"{control.__name__}: {status}")
            errors.extend(f"{control.__name__}: {problem}" for problem in found)

    if executed != len(CONTROLS):
        errors.append(f"could-not-observe: {executed} of {len(CONTROLS)} controls ran")

    print(f"controls executed: {executed}")
    print("observed universe: tracked content identity vs HEAD, untracked non-ignored files")
    print(f"stated out of scope: {', '.join(OUT_OF_SCOPE_CLASSES)}")
    if errors:
        print("HD-04 mutation fact reconciliation: FAIL")
        for problem in errors:
            print(f"  - {problem}")
        return 1
    print("HD-04 mutation fact reconciliation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
