from types import SimpleNamespace

from fastapi.testclient import (
    TestClient,
)

import backend.ai_service as ai_service
from backend.api import app


def prepare(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "NEXUS_DB_PATH",
        str(
            tmp_path
            / "llm.duckdb"
        ),
    )

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "test-secret-at-least-32-characters",
    )

    monkeypatch.setenv(
        "NEXUS_LLM_MODEL",
        "test-local-model",
    )


def token_for(
    client,
):
    password = "StrongPass123"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email":
                "llm@example.com",
            "password":
                password,
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email":
                "llm@example.com",
            "password":
                password,
        },
    )

    assert login.status_code == 200

    return login.json()[
        "access_token"
    ]


def auth(token):
    return {
        "Authorization":
            f"Bearer {token}"
    }


def test_authenticated_llm_answer_and_cost_log(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    def fake_llm(prompt):
        assert prompt == "Explain CRAG"

        return SimpleNamespace(
            content=(
                "CRAG evaluates retrieval "
                "quality before generation."
            ),
            usage_metadata={
                "input_tokens": 4,
                "output_tokens": 7,
            },
            response_metadata={},
        )

    monkeypatch.setattr(
        ai_service,
        "run_local_llm",
        fake_llm,
    )

    with TestClient(app) as client:
        token = token_for(
            client
        )

        response = client.post(
            "/api/v1/ai/answer",
            json={
                "prompt":
                    "Explain CRAG"
            },
            headers=auth(token),
        )

        assert response.status_code == 200

        body = response.json()

        assert body["provider"] == "ollama"
        assert body["model"] == "test-local-model"
        assert body["prompt_tokens"] == 4
        assert body["completion_tokens"] == 7
        assert body["cost_usd"] == 0.0
        assert body["answer"]

        usage = client.get(
            "/api/v1/usage",
            headers=auth(token),
        )

        assert usage.status_code == 200

        records = usage.json()

        assert len(records) == 1
        assert (
            records[0]["operation"]
            == "ai_answer"
        )
        assert (
            records[0]["cost_usd"]
            == 0.0
        )


def test_llm_endpoint_requires_auth(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ai/answer",
            json={
                "prompt":
                    "Explain local RAG"
            },
        )

    assert response.status_code == 401


def test_llm_prompt_validation(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        token = token_for(
            client
        )

        response = client.post(
            "/api/v1/ai/answer",
            json={"prompt": "x"},
            headers=auth(token),
        )

    assert response.status_code == 422


def test_empty_llm_response_rejected(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    monkeypatch.setattr(
        ai_service,
        "run_local_llm",
        lambda prompt: SimpleNamespace(
            content="",
            usage_metadata={},
            response_metadata={},
        ),
    )

    with TestClient(app) as client:
        token = token_for(
            client
        )

        response = client.post(
            "/api/v1/ai/answer",
            json={
                "prompt":
                    "Explain GraphRAG"
            },
            headers=auth(token),
        )

    assert response.status_code == 502


def test_llm_failure_returns_503(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    def broken_llm(prompt):
        raise ConnectionError(
            "offline"
        )

    monkeypatch.setattr(
        ai_service,
        "run_local_llm",
        broken_llm,
    )

    with TestClient(app) as client:
        token = token_for(
            client
        )

        response = client.post(
            "/api/v1/ai/answer",
            json={
                "prompt":
                    "Explain agents"
            },
            headers=auth(token),
        )

    assert response.status_code == 503
