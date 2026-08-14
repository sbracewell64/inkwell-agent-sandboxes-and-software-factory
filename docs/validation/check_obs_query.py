from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

HELPER = (
    ROOT
    / "tools"
    / "obs_query.py"
)

OBS_JUST = (
    ROOT
    / "just"
    / "obs.just"
)

FIXTURE_ADW = "fixture-adw"

EXPECTED = {
    "sessions": (
        "fixture-adw|running|"
        "Fixture request for "
        "B3-004 observability|"
        "123|0.4567"
    ),
    "phases": (
        "1|plan|agent|planner|"
        "success|1"
    ),
    "tail": (
        "1|phase.start|plan|"
        "2026-08-14T12:00:01Z"
    ),
    "procs": (
        "agent|builder|43210|"
        "pi fixture|"
        "2026-08-14T12:00:02Z"
    ),
    "live-pids": (
        "agent 43210"
    ),
}


def run(
    args: list[str],
    *,
    env: dict[str, str]
    | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def create_fixture(
    path: Path,
) -> None:
    conn = sqlite3.connect(
        path
    )

    conn.executescript(
        """
        CREATE TABLE sessions (
            adw_id TEXT PRIMARY KEY,
            status TEXT,
            request TEXT,
            total_tokens INTEGER,
            total_cost REAL,
            started_at TEXT
        );

        CREATE TABLE phases (
            id INTEGER PRIMARY KEY,
            adw_id TEXT,
            seq INTEGER,
            name TEXT,
            kind TEXT,
            owner TEXT,
            status TEXT,
            attempt INTEGER
        );

        CREATE TABLE events (
            event_id TEXT PRIMARY KEY,
            adw_id TEXT,
            type TEXT,
            name TEXT,
            started_at TEXT
        );

        CREATE TABLE processes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            adw_id TEXT,
            kind TEXT,
            name TEXT,
            pid INTEGER,
            command TEXT,
            started_at TEXT,
            ended_at TEXT
        );
        """
    )

    conn.execute(
        """
        INSERT INTO sessions
        (
            adw_id,
            status,
            request,
            total_tokens,
            total_cost,
            started_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            FIXTURE_ADW,
            "running",
            (
                "Fixture request for "
                "B3-004 observability"
            ),
            123,
            0.4567,
            "2026-08-14T12:00:00Z",
        ),
    )

    conn.execute(
        """
        INSERT INTO phases
        (
            adw_id,
            seq,
            name,
            kind,
            owner,
            status,
            attempt
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            FIXTURE_ADW,
            1,
            "plan",
            "agent",
            "planner",
            "success",
            1,
        ),
    )

    conn.execute(
        """
        INSERT INTO events
        (
            event_id,
            adw_id,
            type,
            name,
            started_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "evt-fixture",
            FIXTURE_ADW,
            "phase.start",
            "plan",
            "2026-08-14T12:00:01Z",
        ),
    )

    conn.execute(
        """
        INSERT INTO processes
        (
            adw_id,
            kind,
            name,
            pid,
            command,
            started_at,
            ended_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            FIXTURE_ADW,
            "agent",
            "builder",
            43210,
            "pi fixture",
            "2026-08-14T12:00:02Z",
            None,
        ),
    )

    conn.execute(
        """
        INSERT INTO processes
        (
            adw_id,
            kind,
            name,
            pid,
            command,
            started_at,
            ended_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            FIXTURE_ADW,
            "adw",
            "",
            43100,
            "python fixture",
            "2026-08-14T11:59:59Z",
            "2026-08-14T12:00:03Z",
        ),
    )

    conn.commit()
    conn.close()


def expect(
    errors: list[str],
    label: str,
    proc: subprocess.CompletedProcess[str],
    expected: str,
) -> None:
    actual = (
        proc.stdout
        .strip()
    )

    if proc.returncode != 0:
        errors.append(
            f"{label}: exit "
            f"{proc.returncode}: "
            f"{actual}"
        )
    elif actual != expected:
        errors.append(
            f"{label}: expected "
            f"{expected!r}, "
            f"got {actual!r}"
        )


parser = argparse.ArgumentParser(
    description=(
        "Validate B3-004 "
        "sqlite-free observability."
    )
)

parser.add_argument(
    "--require-no-external-sqlite3",
    action="store_true",
    help=(
        "Fail if an external "
        "sqlite3 executable "
        "is available."
    ),
)

args = parser.parse_args()

errors: list[str] = []

if not HELPER.is_file():
    errors.append(
        "missing tools/obs_query.py"
    )

if not OBS_JUST.is_file():
    errors.append(
        "missing just/obs.just"
    )
else:
    text = OBS_JUST.read_text(
        encoding="utf-8"
    )

    if (
        "tools/obs_query.py"
        not in text
    ):
        errors.append(
            "just/obs.just does not "
            "use obs_query.py"
        )

    if (
        'env_var_or_default("SSSF_DB", '
        '"adws/adw_data/sssf.db")'
        not in text
    ):
        errors.append(
            "just/obs.just is "
            "missing SSSF_DB override"
        )

    if (
        "sqlite3 "
        "adws/adw_data/sssf.db"
        in text
    ):
        errors.append(
            "just/obs.just still "
            "invokes sqlite3 CLI"
        )

if (
    args.require_no_external_sqlite3
):
    resolved = shutil.which(
        "sqlite3"
    )

    if resolved:
        errors.append(
            "external sqlite3 "
            "unexpectedly resolves "
            f"to {resolved}"
        )

if not errors:
    with tempfile.TemporaryDirectory(
        prefix="sssf-b3-004-"
    ) as temp_dir:
        temp = Path(
            temp_dir
        )

        fixture = (
            temp
            / "fixture.db"
        )

        create_fixture(
            fixture
        )

        for command, extra in (
            (
                "sessions",
                [],
            ),
            (
                "phases",
                [FIXTURE_ADW],
            ),
            (
                "tail",
                [FIXTURE_ADW],
            ),
            (
                "procs",
                [FIXTURE_ADW],
            ),
            (
                "live-pids",
                [FIXTURE_ADW],
            ),
        ):
            proc = run(
                [
                    sys.executable,
                    str(HELPER),
                    "--db",
                    str(fixture),
                    command,
                    *extra,
                ]
            )

            expect(
                errors,
                f"direct {command}",
                proc,
                EXPECTED[command],
            )

        injection = run(
            [
                sys.executable,
                str(HELPER),
                "--db",
                str(fixture),
                "phases",
                (
                    "fixture-adw' "
                    "OR 1=1 --"
                ),
            ]
        )

        expect(
            errors,
            "parameterized ADW_ID",
            injection,
            "",
        )

        env = os.environ.copy()

        env["SSSF_DB"] = (
            fixture.as_posix()
        )

        for command, just_args in (
            (
                "sessions",
                [
                    "just",
                    "obs",
                    "sessions",
                ],
            ),
            (
                "phases",
                [
                    "just",
                    "obs",
                    "phases",
                    FIXTURE_ADW,
                ],
            ),
            (
                "tail",
                [
                    "just",
                    "obs",
                    "tail",
                    FIXTURE_ADW,
                ],
            ),
            (
                "procs",
                [
                    "just",
                    "obs",
                    "procs",
                    FIXTURE_ADW,
                ],
            ),
        ):
            proc = run(
                just_args,
                env=env,
            )

            expect(
                errors,
                (
                    "just obs "
                    f"{command}"
                ),
                proc,
                EXPECTED[command],
            )

        missing = (
            temp
            / "missing.db"
        )

        missing_proc = run(
            [
                sys.executable,
                str(HELPER),
                "--db",
                str(missing),
                "sessions",
            ]
        )

        if (
            missing_proc.returncode
            == 0
        ):
            errors.append(
                "missing database "
                "query succeeded"
            )

        if missing.exists():
            errors.append(
                "missing database "
                "query created a DB"
            )

        if (
            "database not found"
            not in missing_proc.stdout
        ):
            errors.append(
                "missing database "
                "failure is not explicit"
            )

if errors:
    print(
        "B3-004 sqlite-free "
        "observability: FAIL"
    )

    for error in errors:
        print(
            f"- {error}"
        )

    raise SystemExit(1)

print(
    "B3-004 sqlite-free "
    "observability: PASS"
)

print(
    "stdlib sqlite3 serves "
    "sessions/phases/tail/procs"
)

print(
    "ADW_ID queries are "
    "parameterized"
)

print(
    "missing databases fail "
    "read-only without creation"
)

if (
    args.require_no_external_sqlite3
):
    print(
        "external sqlite3 CLI "
        "is absent"
    )