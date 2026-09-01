from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from backend.db import connect
from backend.schemas import (
    BackgroundJobResponse,
    IngestRequest,
    KnowledgeDocumentResponse,
)


JOB_KIND_INGEST = "knowledge_ingest"


def utc_now():
    return datetime.now(
        timezone.utc
    )


def create_ingestion_job(
    user_id: str,
    payload: IngestRequest,
) -> BackgroundJobResponse:
    now = utc_now()

    job = BackgroundJobResponse(
        id=str(uuid4()),
        user_id=user_id,
        kind=JOB_KIND_INGEST,
        status="queued",
        attempts=0,
        error=None,
        created_at=now,
        updated_at=now,
    )

    with connect() as con:
        con.execute(
            """
            INSERT INTO background_jobs (
                id,
                user_id,
                kind,
                title,
                content,
                status,
                attempts,
                error,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                job.id,
                user_id,
                job.kind,
                payload.title.strip(),
                payload.content.strip(),
                job.status,
                0,
                None,
                now,
                now,
            ],
        )

    return job


def get_job(
    job_id: str,
    user_id: str,
) -> BackgroundJobResponse | None:
    with connect() as con:
        row = con.execute(
            """
            SELECT
                id,
                user_id,
                kind,
                status,
                attempts,
                error,
                created_at,
                updated_at
            FROM background_jobs
            WHERE id = ?
              AND user_id = ?
            """,
            [
                job_id,
                user_id,
            ],
        ).fetchone()

    if not row:
        return None

    return BackgroundJobResponse(
        id=row[0],
        user_id=row[1],
        kind=row[2],
        status=row[3],
        attempts=row[4],
        error=row[5],
        created_at=row[6],
        updated_at=row[7],
    )


def process_ingestion_job(
    job_id: str,
) -> None:
    now = utc_now()

    with connect() as con:
        row = con.execute(
            """
            SELECT
                user_id,
                title,
                content,
                status,
                attempts
            FROM background_jobs
            WHERE id = ?
            """,
            [job_id],
        ).fetchone()

        if not row:
            return

        user_id = row[0]
        title = row[1]
        content = row[2]
        status = row[3]
        attempts = int(row[4])

        if status == "completed":
            return

        con.execute(
            """
            UPDATE background_jobs
            SET status = ?,
                attempts = ?,
                updated_at = ?,
                error = NULL
            WHERE id = ?
            """,
            [
                "processing",
                attempts + 1,
                now,
                job_id,
            ],
        )

    try:
        normalized_content = " ".join(
            content.split()
        )

        word_count = len(
            normalized_content.split()
        )

        document_id = str(uuid4())
        completed_at = utc_now()

        with connect() as con:
            existing = con.execute(
                """
                SELECT id
                FROM knowledge_documents
                WHERE source_job_id = ?
                """,
                [job_id],
            ).fetchone()

            if not existing:
                con.execute(
                    """
                    INSERT INTO knowledge_documents (
                        id,
                        user_id,
                        source_job_id,
                        title,
                        content,
                        word_count,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        document_id,
                        user_id,
                        job_id,
                        title,
                        normalized_content,
                        word_count,
                        completed_at,
                    ],
                )

            con.execute(
                """
                UPDATE background_jobs
                SET status = ?,
                    updated_at = ?,
                    error = NULL
                WHERE id = ?
                """,
                [
                    "completed",
                    completed_at,
                    job_id,
                ],
            )

    except Exception as exc:
        failed_at = utc_now()

        with connect() as con:
            con.execute(
                """
                UPDATE background_jobs
                SET status = ?,
                    updated_at = ?,
                    error = ?
                WHERE id = ?
                """,
                [
                    "failed",
                    failed_at,
                    str(exc)[:1000],
                    job_id,
                ],
            )

        raise


def list_documents(
    user_id: str,
) -> list[KnowledgeDocumentResponse]:
    with connect() as con:
        rows = con.execute(
            """
            SELECT
                id,
                title,
                content,
                word_count,
                created_at
            FROM knowledge_documents
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            [user_id],
        ).fetchall()

    return [
        KnowledgeDocumentResponse(
            id=row[0],
            title=row[1],
            content=row[2],
            word_count=row[3],
            created_at=row[4],
        )
        for row in rows
    ]
