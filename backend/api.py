from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from backend.db import (
    database_is_ready,
    initialize_database,
)
from backend.schemas import (
    QueryCreate,
    QueryRun,
)
from backend.service import (
    create_query_run,
    get_query_run,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    initialize_database()
    yield


app = FastAPI(
    title="Agentic-Nexus API",
    version="1.0.0",
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
    "/api/v1/queries",
    response_model=QueryRun,
    status_code=201,
)
def submit_query(
    payload: QueryCreate,
):
    return create_query_run(
        payload
    )


@app.get(
    "/api/v1/queries/{query_id}",
    response_model=QueryRun,
)
def read_query(
    query_id: str,
):
    record = get_query_run(
        query_id
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Query run not found",
        )

    return record
