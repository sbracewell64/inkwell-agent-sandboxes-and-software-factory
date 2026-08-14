from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
import sys

DEFAULT_DB = "adws/adw_data/sssf.db"

QUERIES: dict[str, tuple[str, str]] = {
    "sessions": (
        """
        SELECT
            adw_id,
            status,
            substr(request, 1, 60),
            total_tokens,
            round(total_cost, 4)
        FROM sessions
        ORDER BY started_at DESC
        LIMIT 10
        """,
        "|",
    ),
    "phases": (
        """
        SELECT
            seq,
            name,
            kind,
            owner,
            status,
            attempt
        FROM phases
        WHERE adw_id = ?
        ORDER BY seq
        """,
        "|",
    ),
    "tail": (
        """
        SELECT
            rowid,
            type,
            name,
            started_at
        FROM events
        WHERE adw_id = ?
        ORDER BY rowid DESC
        LIMIT 25
        """,
        "|",
    ),
    "procs": (
        """
        SELECT
            kind,
            name,
            pid,
            command,
            started_at
        FROM processes
        WHERE adw_id = ?
          AND ended_at IS NULL
        ORDER BY id
        """,
        "|",
    ),
    "live-pids": (
        """
        SELECT
            kind,
            pid
        FROM processes
        WHERE adw_id = ?
          AND ended_at IS NULL
        ORDER BY
            CASE kind
                WHEN 'agent' THEN 0
                ELSE 1
            END,
            id DESC
        """,
        " ",
    ),
}


def default_db_path() -> str:
    return os.environ.get(
        "SSSF_DB",
        DEFAULT_DB,
    )


def connect_read_only(
    path: Path,
) -> sqlite3.Connection:
    resolved = (
        path
        .expanduser()
        .resolve()
    )

    if not resolved.is_file():
        raise FileNotFoundError(
            resolved
        )

    uri = (
        resolved.as_uri()
        + "?mode=ro"
    )

    conn = sqlite3.connect(
        uri,
        uri=True,
        timeout=5.0,
    )

    conn.execute(
        "PRAGMA query_only=ON;"
    )

    conn.execute(
        "PRAGMA busy_timeout=5000;"
    )

    return conn


def render_value(
    value: object,
) -> str:
    if value is None:
        return ""

    return str(value)


def emit_rows(
    rows: list[
        tuple[object, ...]
    ],
    separator: str,
) -> None:
    for row in rows:
        print(
            separator.join(
                render_value(value)
                for value in row
            )
        )


def execute_query(
    conn: sqlite3.Connection,
    command: str,
    adw_id: str | None,
) -> None:
    sql, separator = (
        QUERIES[command]
    )

    if command == "sessions":
        rows = (
            conn
            .execute(sql)
            .fetchall()
        )
    else:
        if adw_id is None:
            raise ValueError(
                f"{command} requires "
                "ADW_ID"
            )

        rows = (
            conn
            .execute(
                sql,
                (adw_id,),
            )
            .fetchall()
        )

    emit_rows(
        rows,
        separator,
    )


def build_parser(
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read SSSF observability "
            "data through Python's "
            "standard-library sqlite3."
        )
    )

    parser.add_argument(
        "--db",
        default=default_db_path(),
        help=(
            "Trace database path. "
            "Defaults to SSSF_DB or "
            "adws/adw_data/sssf.db."
        ),
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    sub.add_parser(
        "sessions",
        help=(
            "Show the ten most "
            "recent sessions."
        ),
    )

    for command, help_text in (
        (
            "phases",
            "Show phases for one ADW.",
        ),
        (
            "tail",
            "Show recent events for "
            "one ADW.",
        ),
        (
            "procs",
            "Show believed-live "
            "processes for one ADW.",
        ),
        (
            "live-pids",
            "Emit kind/pid rows for "
            "the kill recipe.",
        ),
    ):
        child = sub.add_parser(
            command,
            help=help_text,
        )

        child.add_argument(
            "adw_id",
            metavar="ADW_ID",
        )

    return parser


def main() -> int:
    args = (
        build_parser()
        .parse_args()
    )

    db_path = Path(
        args.db
    )

    try:
        conn = connect_read_only(
            db_path
        )
    except FileNotFoundError as exc:
        print(
            "obs_query: database "
            "not found: "
            f"{exc.args[0]}",
            file=sys.stderr,
        )
        return 2
    except sqlite3.Error as exc:
        print(
            "obs_query: could not "
            f"open database: {exc}",
            file=sys.stderr,
        )
        return 3

    try:
        execute_query(
            conn,
            args.command,
            getattr(
                args,
                "adw_id",
                None,
            ),
        )
    except sqlite3.Error as exc:
        print(
            "obs_query: SQLite "
            f"query failed: {exc}",
            file=sys.stderr,
        )
        return 4
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )