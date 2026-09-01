from datetime import datetime, timezone
from uuid import uuid4

from backend.db import connect
from backend.schemas import QueryCreate, QueryRun


def create_query_run(
    payload: QueryCreate,
) -> QueryRun:
    record = QueryRun(
        id=str(uuid4()),
        query=payload.query.strip(),
        status="accepted",
        created_at=datetime.now(
            timezone.utc
        ),
    )

    with connect() as con:
        con.execute(
            """
            INSERT INTO query_runs (
                id,
                query,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                record.id,
                record.query,
                record.status,
                record.created_at,
            ],
        )

    return record


def get_query_run(
    query_id: str,
) -> QueryRun | None:
    with connect() as con:
        row = con.execute(
            """
            SELECT
                id,
                query,
                status,
                created_at
            FROM query_runs
            WHERE id = ?
            """,
            [query_id],
        ).fetchone()

    if not row:
        return None

    return QueryRun(
        id=row[0],
        query=row[1],
        status=row[2],
        created_at=row[3],
    )
