"""HD-11 — hold the source-custody authority document to what the code does.

`docs/architecture/REPOSITORY_OWNERSHIP.md` is the normative record of who owns
the SSSF source and where a sandbox run gets its code. The executable owners are
the FILL/SETUP/HARVEST recipes and the durable run-record schema. This validator
refuses to let the document drift away from them.

It asserts properties, not vocabulary:

- shell-recipe rows are accepted only when a bounded structural recognizer sees
  the operative assignment or conditional and its refusing exit path;
- the required row set is derived from the code (the persisted provenance field
  names come out of `fill.just` and the run-record schema), so renaming a field
  in the code turns the document red until the document is corrected, and
  naming a field the code does not have is red the other way round;
- no claim about what FILL clones may name a repository, by URL literal or by
  the upstream owner's name, because the recipe derives its source from the host
  checkout's `origin` and never names one.

Offline and deterministic: file bytes only. No network, no git, no subprocess.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[2]

DOC = "docs/architecture/REPOSITORY_OWNERSHIP.md"
FILL = "just/sandbox/lifecycle/fill.just"
SETUP = "just/sandbox/lifecycle/setup.just"
HARVEST = "just/sandbox/manage/harvest.just"
RECORD = "sandbox_mount/host/run_record.py"
OWNERSHIP = "docs/validation/check_repository_ownership.py"
INCREMENT = "docs/increments/B2-002_SANDBOX_SOURCE_CONTRACT.md"
RUN_RECORD = "docs/evidence/B2-002_SOURCE_PROOF_RUN_RECORD.json"
VALIDATOR = "docs/validation/check_source_custody_authority.py"

# The document must point a reader at the executable authority, the proving
# increment, its tracked run record, and the control that keeps this true.
REQUIRED_POINTERS = (FILL, SETUP, HARVEST, RECORD, INCREMENT, RUN_RECORD, VALIDATOR)

SOURCE_FILES = (DOC, FILL, SETUP, HARVEST, RECORD, OWNERSHIP, VALIDATOR)

# A claim about what gets cloned or where the sandbox source comes from.
CLONE_CLAIM = re.compile(r"\bclon(?:e|es|ed|ing)\b|\bsandbox source\b", re.IGNORECASE)

# A concrete repository: a real GitHub owner (alphanumerics and hyphens only) and
# a repository name. `https://github.com/*)` and `https://github.com/...` are
# deliberately excluded — they are the restriction, not a named repository.
CONCRETE_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9][A-Za-z0-9-]*)/([A-Za-z0-9._-]+)"
)

# A backticked repository path the document asks the reader to open.
CITED_PATH = re.compile(r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|py|just|json|yml|sh))`")

BACKTICKED = re.compile(r"`([^`]+)`")


class Unobservable(Exception):
    """A required input could not be read or parsed at all."""


@dataclass(frozen=True)
class Facts:
    """What the code itself says, extracted from its bytes."""

    canonical: str
    upstream: str
    canonical_owner: str
    upstream_owner: str
    persisted: tuple[tuple[str, str], ...]
    schema_fields: tuple[str, ...]


@dataclass(frozen=True)
class Coverage:
    verified: tuple[str, ...]
    unchecked: tuple[str, ...]


@dataclass(frozen=True)
class Assessment:
    facts: Facts | None
    bad: tuple[str, ...]
    cno: tuple[str, ...]
    coverage: Coverage | None
    coverage_reason: str | None


def read(root: Path, rel: str) -> str:
    target = root / rel
    try:
        return target.read_text(encoding="utf-8")
    except OSError as exc:
        raise Unobservable(f"{rel}: could not be read: {exc}") from exc


def string_constants(source: str, rel: str) -> set[str]:
    """Every string literal in a Python module, with implicit concatenation folded."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise Unobservable(f"{rel}: could not be parsed: {exc}") from exc
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def assigned_literal(source: str, rel: str, name: str):
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise Unobservable(f"{rel}: could not be parsed: {exc}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        ):
            try:
                return ast.literal_eval(node.value)
            except ValueError as exc:
                raise Unobservable(f"{rel}: {name} is not a literal: {exc}") from exc
    raise Unobservable(f"{rel}: no assignment to {name}")


def owner_of(url: str, rel: str) -> str:
    match = CONCRETE_URL.search(url)
    if not match:
        raise Unobservable(f"{rel}: {url!r} is not a concrete GitHub repository URL")
    return match.group(1)


def code_facts(root: Path) -> Facts:
    """Read the contract out of the code. Anything unreadable is could-not-observe."""
    ownership = read(root, OWNERSHIP)
    canonical = assigned_literal(ownership, OWNERSHIP, "CANONICAL")
    upstream = assigned_literal(ownership, OWNERSHIP, "UPSTREAM")
    if not isinstance(canonical, str) or not isinstance(upstream, str):
        raise Unobservable(f"{OWNERSHIP}: CANONICAL/UPSTREAM are not strings")

    record = read(root, RECORD)
    fields = assigned_literal(record, RECORD, "FIELDS")
    if not isinstance(fields, tuple) or not all(isinstance(f, str) for f in fields):
        raise Unobservable(f"{RECORD}: FIELDS is not a tuple of names")

    # The provenance the recipe actually persists, in the order it persists it.
    fill = operative_recipe_text(read(root, FILL))
    marker = '"$RR" set {{RUN_ID}}'
    start = fill.find(marker)
    if start < 0:
        raise Unobservable(f"{FILL}: no run-record write ({marker})")
    end = fill.find("\n\n", start)
    region = fill[start:] if end < 0 else fill[start:end]
    persisted = tuple(re.findall(r'(\w+)="\$(\w+)"', region))
    if not persisted:
        raise Unobservable(f"{FILL}: run-record write persists no named fields")

    return Facts(
        canonical=canonical,
        upstream=upstream,
        canonical_owner=owner_of(canonical, OWNERSHIP),
        upstream_owner=owner_of(upstream, OWNERSHIP),
        persisted=persisted,
        schema_fields=tuple(fields),
    )


def required_rows(facts: Facts) -> dict[str, tuple[str, str]]:
    """Contract element -> (file that owns it, exact token that must be in it)."""
    rows: dict[str, tuple[str, str]] = {
        "origin-derivation": (FILL, "git remote get-url origin"),
        "public-clone-restriction": (FILL, "https://github.com/*)"),
        "exact-pin-shape": (FILL, "^[0-9a-f]{40}$"),
        "default-pin-is-host-head": (FILL, 'PIN="$(git rev-parse HEAD)"'),
        "dirty-host-refusal": (FILL, 'if [ -n "$(git status --porcelain)" ]; then'),
        "guest-run-branch": (FILL, 'branch="sbx/$run_id"'),
        "fill-head-gate": (FILL, 'if [ "$HEAD_SHA" != "$INTENDED" ]; then'),
        "setup-origin-recheck": (SETUP, '[ "$origin" = "$want_repo" ]'),
        "setup-head-recheck": (SETUP, 'case "$head" in'),
        "setup-clean-tree-recheck": (SETUP, 'if [ -n "$porcelain" ]; then'),
        "harvest-run-branch": (HARVEST, 'BRANCH="sbx/$RUN_ID"'),
        "harvest-ref-namespace": (HARVEST, 'DEST="refs/sandbox/$RUN_ID"'),
        "canonical-remote-url": (OWNERSHIP, facts.canonical),
        "upstream-remote-url": (OWNERSHIP, facts.upstream),
        # The two remote roles are claims about enforcement, not vocabulary, so
        # the document has to cite the assertions that enforce them.
        "origin-is-canonical": (
            OWNERSHIP,
            'run("git", "remote", "get-url", "origin") != CANONICAL',
        ),
        "upstream-push-disabled": (OWNERSHIP, '"--push", "upstream"'),
    }
    for field, variable in facts.persisted:
        slug = field.replace("_", "-")
        rows[f"persisted-{slug}"] = (FILL, f'{field}="${variable}"')
        rows[f"schema-{slug}"] = (RECORD, f'"{field}",')
    return rows


def token_present(root: Path, rel: str, token: str) -> bool:
    """The reader must find the token by opening the cited file."""
    try:
        text = read(root, rel)
    except Unobservable:
        return False
    if rel.endswith(".just"):
        return token in operative_recipe_text(text)
    if token in text:
        return True
    if rel.endswith(".py"):
        # Adjacent string literals are one value to the reader and to Python.
        try:
            return token in string_constants(text, rel)
        except Unobservable:
            return False
    return False


def operative_recipe_text(source: str) -> str:
    lines = []
    for line in source.splitlines():
        line = re.sub(r"(^|\s)#.*$", r"\1", line)
        stripped = line.lstrip()
        if re.match(r"if\s+(?:false|\[\s+(?:1\s+=\s+0|0\s+=\s+1)\s+\])\s*;\s*then\s*$", stripped):
            break
        lines.append(line)
    return "\n".join(lines)


STRUCTURAL_PATTERNS: dict[str, str] = {
    "origin-derivation": r'REPO="\$\(git remote get-url origin 2>/dev/null \|\| true\)"',
    "public-clone-restriction": r'case "\$REPO" in\s+https://github\.com/\*\) ;;\s+\*\).*?exit 1\s+;;\s+esac',
    "exact-pin-shape": r'if ! \[\[ "\$PIN" =~ \^\[0-9a-f\]\{40\}\$ \]\]; then.*?exit 1\s+fi',
    "default-pin-is-host-head": r'else\s+.*?PIN="\$\(git rev-parse HEAD\)"\s+fi',
    "dirty-host-refusal": r'if \[ -n "\$\(git status --porcelain\)" \]; then.*?exit 1\s+fi',
    "guest-run-branch": r'branch="sbx/\$run_id".*?git -C app switch --quiet -c "\$branch"',
    "fill-head-gate": r'if \[ "\$HEAD_SHA" != "\$INTENDED" \]; then.*?exit 1\s+fi',
    "setup-origin-recheck": r'\[ "\$origin" = "\$want_repo" \] \|\| \{.*?exit 1\s+\}',
    "setup-head-recheck": r'case "\$head" in\s+"\$want"\*\) ;;\s+\*\).*?exit 1\s+;;\s+esac',
    "setup-clean-tree-recheck": r'porcelain="\$\(git status --porcelain\)"\s+if \[ -n "\$porcelain" \]; then.*?exit 1\s+fi',
    "harvest-run-branch": r'BRANCH="sbx/\$RUN_ID".*?"refs/heads/\$BRANCH:\$DEST"',
    "harvest-ref-namespace": r'DEST="refs/sandbox/\$RUN_ID".*?"refs/heads/\$BRANCH:\$DEST"',
}


def structural_coverage(root: Path, expected: dict[str, tuple[str, str]]) -> Coverage:
    verified: list[str] = []
    unchecked: list[str] = []
    cache: dict[str, str] = {}
    for element, (rel, _) in expected.items():
        if rel.endswith(".just"):
            pattern = STRUCTURAL_PATTERNS.get(element)
            if element.startswith("persisted-"):
                _, token = expected[element]
                pattern = (
                    r'"\$RR" set \{\{RUN_ID\}\}\s+\\\n'
                    r'(?:\s+\w+="\$\w+"\s+\\\n)*\s+'
                    + re.escape(token)
                )
            if pattern is None:
                unchecked.append(f"{element}: no bounded structural recognizer")
                continue
            text = cache.setdefault(rel, operative_recipe_text(read(root, rel)))
            if re.search(pattern, text, re.DOTALL):
                verified.append(element)
            else:
                unchecked.append(
                    f"{element}: operative structure not recognized in `{rel}`"
                )
        else:
            verified.append(element)
    return Coverage(tuple(sorted(verified)), tuple(sorted(unchecked)))


def claims(text: str) -> list[str]:
    """Assertions the document makes.

    A bullet, a table row, or a paragraph is one claim. A claim whose text ends
    in a colon also carries the block it introduces, because that is how this
    repository writes a named value — and it is exactly how the pre-HD-11
    document attributed a hard-coded upstream URL to FILL across a blank line.
    """
    lines = text.split("\n")
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if stripped.startswith(("-", "*", "|")):
            blocks.append(stripped)
            index += 1
            continue
        run = [stripped]
        index += 1
        while index < len(lines):
            following = lines[index].strip()
            if not following or following.startswith(("-", "*", "|", "#")):
                break
            run.append(following)
            index += 1
        blocks.append(" ".join(run))

    out: list[str] = []
    for position, block in enumerate(blocks):
        if block.endswith(":") and position + 1 < len(blocks):
            out.append(f"{block} {blocks[position + 1]}")
        else:
            out.append(block)
    return out


def table_rows(text: str) -> tuple[dict[str, tuple[str, str]], tuple[str, ...]]:
    rows: dict[str, tuple[str, str]] = {}
    duplicates: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3:
            continue
        element = cells[0].strip("`")
        if not re.fullmatch(r"[a-z][a-z0-9-]*", element):
            continue  # header and separator rows
        if element in rows:
            duplicates.append(element)
        else:
            rows[element] = (cells[1].strip("`"), cells[2].strip("`"))
    return rows, tuple(sorted(set(duplicates)))


def document_errors(root: Path, facts: Facts) -> list[str]:
    """Everything the document gets wrong about the code. Empty means agreement."""
    errors: list[str] = []
    doc = read(root, DOC)
    statements = claims(doc)
    if not statements:
        raise Unobservable(f"{DOC}: no claims could be parsed")

    # 1. No claim about cloning may name a repository. FILL derives its source.
    clone_claims = [claim for claim in statements if CLONE_CLAIM.search(claim)]
    if not clone_claims:
        errors.append(
            "document makes no claim about what the sandbox clones; "
            "the source-custody record must state the current behavior"
        )
    for claim in clone_claims:
        named = CONCRETE_URL.search(claim)
        if named:
            errors.append(
                "hard-coded clone authority: a clone claim names the repository "
                f"{named.group(0)!r} — FILL derives its source from the host "
                f"checkout's origin and names none: {claim[:120]!r}"
            )
        if re.search(rf"\b{re.escape(facts.upstream_owner)}\b", claim, re.IGNORECASE):
            errors.append(
                "hard-coded clone authority: a clone claim attributes the sandbox "
                f"source to upstream owner {facts.upstream_owner!r}: {claim[:120]!r}"
            )

    # 2. Repository URLs in the document must be the ones the code declares.
    seen_urls = {match.group(0) for match in CONCRETE_URL.finditer(doc)}
    if not seen_urls:
        errors.append("document declares no repository URL for the canonical remote")
    canonical_seen = False
    for url in sorted(seen_urls):
        owner = CONCRETE_URL.match(url).group(1)
        if owner == facts.canonical_owner:
            if url.rstrip("/") != facts.canonical:
                errors.append(
                    f"canonical URL divergence: document says {url!r}, "
                    f"code declares {facts.canonical!r}"
                )
            else:
                canonical_seen = True
        elif owner == facts.upstream_owner:
            if url.rstrip("/") != facts.upstream:
                errors.append(
                    f"upstream URL divergence: document says {url!r}, "
                    f"code declares {facts.upstream!r}"
                )
        else:
            errors.append(
                f"document names repository {url!r}, which is neither the "
                "canonical nor the upstream remote the code declares"
            )
    if not canonical_seen:
        errors.append(
            f"document never states the canonical repository {facts.canonical!r}"
        )

    # 3. Remote roles, each backed by what the ownership validator enforces.
    role_checks = (
        (
            "`origin`",
            ("canonical", "writable"),
            "origin is the operator-owned canonical writable remote",
        ),
        (
            "`upstream`",
            ("reference-only",),
            "upstream is reference-only",
        ),
    )
    for remote, needles, description in role_checks:
        if not any(
            remote in claim and all(n in claim.lower() for n in needles)
            for claim in statements
        ):
            errors.append(f"document does not declare that {description}")

    # 4. Every pointer a reader needs, and every citation must be followable.
    for pointer in REQUIRED_POINTERS:
        if f"`{pointer}`" not in doc:
            errors.append(f"missing pointer: document never cites `{pointer}`")
    for cited in sorted({match.group(1) for match in CITED_PATH.finditer(doc)}):
        if not (root / cited).is_file():
            errors.append(
                f"citation cannot be followed: `{cited}` does not exist in the "
                "repository"
            )

    # 5. The published contract table must match the code element for element.
    expected = required_rows(facts)
    published, duplicates = table_rows(doc)
    for element in duplicates:
        errors.append(f"duplicate contract-table row: {element}")
    for element in sorted(set(expected) - set(published)):
        path, token = expected[element]
        errors.append(
            f"contract table omits {element}: `{path}` owns `{token}`"
        )
    for element in sorted(set(published) - set(expected)):
        errors.append(
            f"contract table publishes {element}, which the code does not define"
        )
    for element in sorted(set(expected) & set(published)):
        want_path, want_token = expected[element]
        got_path, got_token = published[element]
        if got_path != want_path:
            errors.append(
                f"{element}: document cites `{got_path}`, code authority is "
                f"`{want_path}`"
            )
        if got_token != want_token:
            errors.append(
                f"{element}: document publishes token {got_token!r}, code says "
                f"{want_token!r}"
            )
        elif not want_path.endswith(".just") and not token_present(root, want_path, want_token):
            errors.append(
                f"{element}: token {want_token!r} does not occur in `{want_path}`"
            )

    # 6. The persisted provenance names must be the schema's own names.
    for field, _ in facts.persisted:
        if field not in facts.schema_fields:
            errors.append(
                f"code disagreement: FILL persists {field!r}, which is not in the "
                f"run-record schema {RECORD}"
            )
        if f"`{field}`" not in doc:
            errors.append(f"document never names persisted field `{field}`")
    for name in BACKTICKED.findall(doc):
        if re.fullmatch(r"(?:source|commit)_[a-z_]+", name) and name not in {
            field for field, _ in facts.persisted
        }:
            errors.append(
                f"document names provenance field `{name}`, which FILL does not "
                "persist"
            )

    # 7. The derivation itself, stated in prose rather than only tabulated.
    if not any(
        "git remote get-url origin" in claim
        and not claim.startswith("|")
        and CLONE_CLAIM.search(claim)
        for claim in statements
    ):
        errors.append(
            "document does not state in prose that FILL resolves the sandbox "
            "source with `git remote get-url origin`"
        )

    return errors


def assess(root: Path) -> Assessment:
    bad: list[str] = []
    cno: list[str] = []
    try:
        facts = code_facts(root)
    except Unobservable as exc:
        reason = str(exc)
        return Assessment(None, (), (reason,), None, reason)

    coverage: Coverage | None = None
    coverage_reason: str | None = None
    try:
        coverage = structural_coverage(root, required_rows(facts))
        cno.extend(coverage.unchecked)
    except Unobservable as exc:
        coverage_reason = str(exc)
        cno.append(coverage_reason)

    try:
        bad.extend(document_errors(root, facts))
    except Unobservable as exc:
        cno.append(str(exc))

    return Assessment(
        facts,
        tuple(bad),
        tuple(cno),
        coverage,
        coverage_reason,
    )


def evaluate(root: Path) -> tuple[list[str], list[str]]:
    """(observed-bad, could-not-observe). Neither list empty is ever a pass."""
    result = assess(root)
    return list(result.bad), list(result.cno)


def coverage_lines(result: Assessment) -> list[str]:
    if result.coverage is None:
        reason = result.coverage_reason or "required code facts were not established"
        return [f"coverage: could-not-establish: {reason}"]
    return [
        "structurally verified: "
        + (", ".join(result.coverage.verified) or "none"),
        "unchecked: " + ("; ".join(result.coverage.unchecked) or "none"),
    ]


def exit_code(result: Assessment) -> int:
    if (
        result.facts is None
        or result.bad
        or result.cno
        or result.coverage is None
        or result.coverage.unchecked
    ):
        return 1
    return 0


# ── watched-red controls ────────────────────────────────────────────────────
#
# Each control mutates one thing in a throwaway copy of the repository and
# requires this validator to go red for the stated reason. The unmutated copy
# must stay green, so none of them is vacuously red.


def build_fixture(root: Path, destination: Path) -> None:
    doc = read(root, DOC)
    wanted = set(SOURCE_FILES) | set(REQUIRED_POINTERS)
    wanted |= {match.group(1) for match in CITED_PATH.finditer(doc)}
    for rel in sorted(wanted):
        source = root / rel
        if not source.is_file():
            continue
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def rewrite(root: Path, rel: str, old: str, new: str) -> bool:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return False
    path.write_text(text.replace(old, new), encoding="utf-8")
    return True


def append(root: Path, rel: str, extra: str) -> bool:
    path = root / rel
    path.write_text(path.read_text(encoding="utf-8") + extra, encoding="utf-8")
    return True


def watched_red_errors(root: Path, facts: Facts) -> list[str]:
    errors: list[str] = []

    def control(name: str, marker: str, mutate) -> None:
        with tempfile.TemporaryDirectory(prefix="sssf-hd11-") as raw:
            fixture = Path(raw) / "repo"
            build_fixture(root, fixture)
            if not mutate(fixture):
                errors.append(f"{name}: control could not be applied")
                return
            result = assess(fixture)
            bad, cno = list(result.bad), list(result.cno)
            if exit_code(result) == 0:
                errors.append(f"{name}: did not go red")
                return
            if not any(marker in line for line in bad + cno):
                errors.append(
                    f"{name}: went red for the wrong reason: {(bad + cno)[:2]!r}"
                )

    def early_cno_control(name: str, mutate) -> None:
        with tempfile.TemporaryDirectory(prefix="sssf-hd11-") as raw:
            fixture = Path(raw) / "repo"
            build_fixture(root, fixture)
            if not mutate(fixture):
                errors.append(f"{name}: control could not be applied")
                return
            result = assess(fixture)
            rendered = coverage_lines(result)
            if exit_code(result) == 0:
                errors.append(f"{name}: early could-not-observe returned success")
            elif not result.cno or result.coverage is not None:
                errors.append(f"{name}: did not produce early could-not-observe")
            elif any(
                line in {"unchecked: none", "structurally verified: none"}
                for line in rendered
            ):
                errors.append(f"{name}: falsely reported empty complete coverage")
            elif not any("coverage: could-not-establish:" in line for line in rendered):
                errors.append(f"{name}: omitted coverage-not-established reason")

    # Non-vacuity: the shipped document passes an unmutated copy of itself.
    with tempfile.TemporaryDirectory(prefix="sssf-hd11-") as raw:
        fixture = Path(raw) / "repo"
        build_fixture(root, fixture)
        result = assess(fixture)
        if exit_code(result) != 0:
            errors.append(
                "unmutated fixture verdict is not zero: "
                f"{(result.bad + result.cno)[:3]!r}"
            )

    control(
        "hard-coded-upstream-control",
        "hard-coded clone authority",
        lambda fixture: append(
            fixture,
            DOC,
            "\n## Stale baseline\n\nThe current `fill` lifecycle recipe clones a "
            f"hard-coded public repository:\n\n`{facts.upstream}`\n",
        ),
    )

    control(
        "missing-fill-pointer-control",
        f"missing pointer: document never cites `{FILL}`",
        lambda fixture: rewrite(fixture, DOC, f"`{FILL}`", "the FILL recipe"),
    )

    control(
        "missing-b2-002-pointer-control",
        f"missing pointer: document never cites `{INCREMENT}`",
        lambda fixture: rewrite(fixture, DOC, f"`{INCREMENT}`", "the B2-002 record"),
    )

    control(
        "canonical-url-divergence-control",
        "canonical URL divergence",
        lambda fixture: rewrite(
            fixture, DOC, facts.canonical, facts.canonical.replace(".git", "-v2.git")
        ),
    )

    control(
        "document-sha-field-divergence-control",
        "code says 'source_sha=",
        lambda fixture: rewrite(fixture, DOC, "source_sha", "pin_sha"),
    )

    control(
        "code-sha-field-divergence-control",
        "contract table omits persisted-pin-sha",
        lambda fixture: rewrite(fixture, FILL, 'source_sha="$PIN"', 'pin_sha="$PIN"'),
    )

    control(
        "unfollowable-citation-control",
        "citation cannot be followed",
        lambda fixture: rewrite(fixture, DOC, f"`{FILL}`", "`fill.just`"),
    )

    control(
        "code-token-drift-control",
        "harvest-ref-namespace: operative structure not recognized",
        lambda fixture: rewrite(
            fixture, HARVEST, 'DEST="refs/sandbox/$RUN_ID"', 'DEST="refs/runs/$RUN_ID"'
        ),
    )

    control(
        "comment-only-token-control",
        "harvest-ref-namespace: operative structure not recognized",
        lambda fixture: rewrite(
            fixture,
            HARVEST,
            'DEST="refs/sandbox/$RUN_ID"',
            'DEST="refs/runs/$RUN_ID"\n    # DEST="refs/sandbox/$RUN_ID"',
        ),
    )

    control(
        "inline-comment-only-token-control",
        "harvest-ref-namespace: operative structure not recognized",
        lambda fixture: rewrite(
            fixture,
            HARVEST,
            'DEST="refs/sandbox/$RUN_ID"',
            'DEST="refs/runs/$RUN_ID"  # DEST="refs/sandbox/$RUN_ID"',
        ),
    )

    control(
        "dead-branch-token-control",
        "harvest-ref-namespace: operative structure not recognized",
        lambda fixture: rewrite(
            fixture,
            HARVEST,
            'DEST="refs/sandbox/$RUN_ID"',
            'DEST="refs/runs/$RUN_ID"\n    if false; then\n'
            '        if true; then echo nested; fi\n'
            '        DEST="refs/sandbox/$RUN_ID"\n    fi',
        ),
    )

    control(
        "duplicate-row-control",
        "duplicate contract-table row: origin-derivation",
        lambda fixture: append(
            fixture,
            DOC,
            f"\n| origin-derivation | `{FILL}` | `git remote get-url origin` |\n",
        ),
    )

    control(
        "unchecked-row-control",
        "fill-head-gate: operative structure not recognized",
        lambda fixture: rewrite(
            fixture,
            FILL,
            'if [ "$HEAD_SHA" != "$INTENDED" ]; then',
            'if test "$HEAD_SHA" != "$INTENDED"; then',
        ),
    )

    early_cno_control(
        "missing-code-authority-coverage-control",
        lambda fixture: (fixture / OWNERSHIP).unlink() is None,
    )

    early_cno_control(
        "missing-operative-run-record-write-coverage-control",
        lambda fixture: rewrite(
            fixture,
            FILL,
            '"$RR" set {{RUN_ID}}',
            '"$RR" record {{RUN_ID}}',
        ),
    )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root to check; defaults to this checkout",
    )
    args = parser.parse_args()
    root = args.root.resolve()

    result = assess(root)
    facts = result.facts
    bad = list(result.bad)
    cno = list(result.cno)
    status = exit_code(result)

    if status == 0 and facts is not None:
        bad.extend(watched_red_errors(root, facts))
        if bad:
            status = 1

    if status != 0:
        print("HD-11 source custody authority: FAIL")
        for line in coverage_lines(result):
            print(line)
        for error in bad:
            print(f"- observed-bad: {error}")
        for error in cno:
            print(f"- could-not-observe: {error}")
        return status

    print("HD-11 source custody authority: PASS")
    print(f"document: {DOC}")
    print("structurally verified: " + ", ".join(result.coverage.verified))
    print("unchecked: none")
    print(
        f"{len(required_rows(facts))} contract elements reconciled against "
        "FILL, SETUP, HARVEST, the run-record schema, and the ownership validator"
    )
    print(
        "persisted provenance derived from the code: "
        + ", ".join(field for field, _ in facts.persisted)
    )
    print(
        "watched-red: hard-coded upstream, missing FILL pointer, missing B2-002 "
        "pointer, canonical URL divergence"
    )
    print(
        "watched-red: document and code SHA field-name divergence, unfollowable "
        "citation, code token drift, full-line and inline comment-only tokens"
    )
    print(
        "watched-red: nested dead-region token, duplicate row, unchecked row, "
        "early code-authority CNO, absent operative write, genuine operative "
        "non-vacuity"
    )
    return status


if __name__ == "__main__":
    raise SystemExit(main())
