import os
from pathlib import Path

import duckdb


def get_database_path() -> Path:
    path = Path(
        os.getenv(
            "NEXUS_DB_PATH",
            "data/agentic_nexus.duckdb",
        )
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def connect():
    return duckdb.connect(
        str(get_database_path())
    )


def initialize_database() -> None:
    with connect() as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS query_runs (
                id VARCHAR PRIMARY KEY,
                query TEXT NOT NULL,
                status VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )


def database_is_ready() -> bool:
    with connect() as con:
        result = con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = 'query_runs'
            """
        ).fetchone()

    return bool(
        result
        and result[0] == 1
    )
