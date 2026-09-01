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
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR PRIMARY KEY,
                email VARCHAR UNIQUE NOT NULL,
                password_hash VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )

        con.execute(
            """
            CREATE TABLE IF NOT EXISTS query_runs (
                id VARCHAR PRIMARY KEY,
                user_id VARCHAR NOT NULL,
                query TEXT NOT NULL,
                status VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
            """
        )


def database_is_ready() -> bool:
    required = {
        "users",
        "query_runs",
    }

    with connect() as con:
        rows = con.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            """
        ).fetchall()

    existing = {
        row[0]
        for row in rows
    }

    return required.issubset(
        existing
    )
