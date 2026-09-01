from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from backend.db import connect
from backend.schemas import (
    QueryCreate,
    QueryRun,
)


def create_query_run(
    payload: QueryCreate,
    user_id: str,
) -> QueryRun:
    record = QueryRun(
        id=str(uuid4()),
        user_id=user_id,
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
                user_id,
                query,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                record.id,
                record.user_id,
                record.query,
                record.status,
                record.created_at,
            ],
        )

    return record


def get_query_run(
    query_id: str,
    user_id: str,
) -> QueryRun | None:
    with connect() as con:
        row = con.execute(
            """
            SELECT
                id,
                user_id,
                query,
                status,
                created_at
            FROM query_runs
            WHERE id = ?
              AND user_id = ?
            """,
            [
                query_id,
                user_id,
            ],
        ).fetchone()

    if not row:
        return None

    return QueryRun(
        id=row[0],
        user_id=row[1],
        query=row[2],
        status=row[3],
        created_at=row[4],
    )
