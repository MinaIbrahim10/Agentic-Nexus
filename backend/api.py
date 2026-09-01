from contextlib import (
    asynccontextmanager,
)

from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
)

from backend.auth import (
    authenticate_user,
    create_access_token,
    create_user,
    get_current_user,
)
from backend.db import (
    database_is_ready,
    initialize_database,
)
from backend.schemas import (
    BackgroundJobResponse,
    IngestRequest,
    KnowledgeDocumentResponse,
    LoginRequest,
    QueryCreate,
    QueryRun,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from backend.service import (
    create_query_run,
    get_query_run,
)

from backend.jobs import (
    create_ingestion_job,
    get_job,
    list_documents,
    process_ingestion_job,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    initialize_database()
    yield


app = FastAPI(
    title="Agentic-Nexus API",
    version="1.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "database": (
            "ok"
            if database_is_ready()
            else "unavailable"
        ),
    }


@app.post(
    "/api/v1/auth/register",
    response_model=UserResponse,
    status_code=201,
)
def register(
    payload: RegisterRequest,
):
    user = create_user(
        payload.email,
        payload.password,
    )

    return UserResponse(
        id=user["id"],
        email=user["email"],
        created_at=user["created_at"],
    )


@app.post(
    "/api/v1/auth/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
):
    user = authenticate_user(
        payload.email,
        payload.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
        )

    return TokenResponse(
        access_token=(
            create_access_token(
                user
            )
        )
    )


@app.get(
    "/api/v1/auth/me",
    response_model=UserResponse,
)
def me(
    user: dict = Depends(
        get_current_user
    ),
):
    return UserResponse(
        **user
    )


@app.post(
    "/api/v1/queries",
    response_model=QueryRun,
    status_code=201,
)
def submit_query(
    payload: QueryCreate,
    user: dict = Depends(
        get_current_user
    ),
):
    return create_query_run(
        payload,
        user["id"],
    )


@app.get(
    "/api/v1/queries/{query_id}",
    response_model=QueryRun,
)
def read_query(
    query_id: str,
    user: dict = Depends(
        get_current_user
    ),
):
    record = get_query_run(
        query_id,
        user["id"],
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Query run not found",
        )

    return record


@app.post(
    "/api/v1/ingest",
    response_model=BackgroundJobResponse,
    status_code=202,
)
def ingest_document(
    payload: IngestRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(
        get_current_user
    ),
):
    job = create_ingestion_job(
        user["id"],
        payload,
    )

    background_tasks.add_task(
        process_ingestion_job,
        job.id,
    )

    return job


@app.get(
    "/api/v1/jobs/{job_id}",
    response_model=BackgroundJobResponse,
)
def read_job(
    job_id: str,
    user: dict = Depends(
        get_current_user
    ),
):
    job = get_job(
        job_id,
        user["id"],
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Background job not found",
        )

    return job


@app.get(
    "/api/v1/documents",
    response_model=list[KnowledgeDocumentResponse],
)
def read_documents(
    user: dict = Depends(
        get_current_user
    ),
):
    return list_documents(
        user["id"]
    )
