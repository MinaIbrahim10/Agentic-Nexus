from fastapi import HTTPException

from backend.auth import (
    authenticate_user,
    create_user,
)
from backend.db import (
    initialize_database,
)
from backend.jobs import (
    create_ingestion_job,
    list_documents,
    process_ingestion_job,
)
from backend.schemas import (
    IngestRequest,
)


DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "DemoPass123!"

DEMO_TITLE = "Agentic-Nexus Demo Knowledge"

DEMO_CONTENT = (
    "Agentic-Nexus combines local language models, "
    "FAISS vector retrieval, a NetworkX knowledge graph, "
    "Corrective RAG scoring, and a bounded query-result cache."
)


def ensure_demo_user() -> dict:
    existing = authenticate_user(
        DEMO_EMAIL,
        DEMO_PASSWORD,
    )

    if existing:
        return existing

    try:
        created = create_user(
            DEMO_EMAIL,
            DEMO_PASSWORD,
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise RuntimeError(
                "demo@example.com already exists "
                "with a different password."
            ) from exc
        raise

    return {
        "id": created["id"],
        "email": created["email"],
        "created_at": created["created_at"],
    }


def ensure_demo_document(
    user_id: str,
) -> None:
    documents = list_documents(
        user_id
    )

    if any(
        document.title == DEMO_TITLE
        for document in documents
    ):
        return

    job = create_ingestion_job(
        user_id=user_id,
        payload=IngestRequest(
            title=DEMO_TITLE,
            content=DEMO_CONTENT,
        ),
    )

    process_ingestion_job(
        job.id
    )


def main() -> None:
    initialize_database()

    user = ensure_demo_user()

    ensure_demo_document(
        user["id"]
    )

    print("DEMO SEED: PASS")
    print(f"email: {DEMO_EMAIL}")
    print(f"password: {DEMO_PASSWORD}")


if __name__ == "__main__":
    main()
