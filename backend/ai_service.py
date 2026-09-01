import os
from datetime import (
    datetime,
    timezone,
)
from uuid import uuid4

from fastapi import HTTPException
from langchain_ollama import ChatOllama

from backend.db import connect
from backend.schemas import (
    AIAnswerResponse,
    AIUsageResponse,
)


DEFAULT_MODEL = "gemma4:e4b-it"
PROVIDER = "ollama"


def get_model_name() -> str:
    return os.getenv(
        "NEXUS_LLM_MODEL",
        DEFAULT_MODEL,
    )


def run_local_llm(
    prompt: str,
):
    model = ChatOllama(
        model=get_model_name(),
        temperature=0,
        keep_alive="15m",
        num_ctx=8192,
    )

    return model.invoke(prompt)


def extract_usage(
    response,
) -> tuple[int, int]:
    usage = getattr(
        response,
        "usage_metadata",
        None,
    ) or {}

    prompt_tokens = int(
        usage.get(
            "input_tokens",
            0,
        )
        or 0
    )

    completion_tokens = int(
        usage.get(
            "output_tokens",
            0,
        )
        or 0
    )

    metadata = getattr(
        response,
        "response_metadata",
        None,
    ) or {}

    if prompt_tokens == 0:
        prompt_tokens = int(
            metadata.get(
                "prompt_eval_count",
                0,
            )
            or 0
        )

    if completion_tokens == 0:
        completion_tokens = int(
            metadata.get(
                "eval_count",
                0,
            )
            or 0
        )

    return (
        prompt_tokens,
        completion_tokens,
    )


def record_usage(
    user_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    with connect() as con:
        con.execute(
            """
            INSERT INTO ai_usage (
                id,
                user_id,
                operation,
                provider,
                model,
                prompt_tokens,
                completion_tokens,
                cost_usd,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                str(uuid4()),
                user_id,
                "ai_answer",
                PROVIDER,
                model,
                prompt_tokens,
                completion_tokens,
                0.0,
                datetime.now(
                    timezone.utc
                ),
            ],
        )


def answer_prompt(
    user_id: str,
    prompt: str,
) -> AIAnswerResponse:
    clean_prompt = prompt.strip()

    try:
        response = run_local_llm(
            clean_prompt
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Local LLM unavailable: "
                + type(exc).__name__
            ),
        )

    content = getattr(
        response,
        "content",
        None,
    )

    if not isinstance(
        content,
        str,
    ) or not content.strip():
        raise HTTPException(
            status_code=502,
            detail="LLM returned an invalid empty response",
        )

    (
        prompt_tokens,
        completion_tokens,
    ) = extract_usage(
        response
    )

    model = get_model_name()

    record_usage(
        user_id=user_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
    )

    return AIAnswerResponse(
        answer=content.strip(),
        provider=PROVIDER,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=0.0,
    )


def list_usage(
    user_id: str,
) -> list[AIUsageResponse]:
    with connect() as con:
        rows = con.execute(
            """
            SELECT
                id,
                operation,
                provider,
                model,
                prompt_tokens,
                completion_tokens,
                cost_usd,
                created_at
            FROM ai_usage
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            [user_id],
        ).fetchall()

    return [
        AIUsageResponse(
            id=row[0],
            operation=row[1],
            provider=row[2],
            model=row[3],
            prompt_tokens=row[4],
            completion_tokens=row[5],
            cost_usd=row[6],
            created_at=row[7],
        )
        for row in rows
    ]
