from fastapi.testclient import (
    TestClient,
)

from backend.api import app


def prepare(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "NEXUS_DB_PATH",
        str(
            tmp_path
            / "jobs.duckdb"
        ),
    )

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "test-secret-at-least-32-characters",
    )


def create_user_token(
    client,
    email,
):
    password = "StrongPass123"

    register = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert login.status_code == 200

    return login.json()[
        "access_token"
    ]


def headers(token):
    return {
        "Authorization":
            f"Bearer {token}"
    }


def test_ingestion_runs_in_background(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        token = create_user_token(
            client,
            "jobs@example.com",
        )

        response = client.post(
            "/api/v1/ingest",
            json={
                "title":
                    "Corrective RAG",
                "content":
                    "Corrective RAG evaluates retrieval quality before generation and can trigger a fallback.",
            },
            headers=headers(token),
        )

        assert response.status_code == 202
        assert (
            response.json()["status"]
            == "queued"
        )

        job_id = response.json()[
            "id"
        ]

        job = client.get(
            f"/api/v1/jobs/{job_id}",
            headers=headers(token),
        )

        assert job.status_code == 200
        assert (
            job.json()["status"]
            == "completed"
        )
        assert (
            job.json()["attempts"]
            == 1
        )

        documents = client.get(
            "/api/v1/documents",
            headers=headers(token),
        )

        assert documents.status_code == 200

        body = documents.json()

        assert len(body) == 1
        assert (
            body[0]["title"]
            == "Corrective RAG"
        )
        assert (
            body[0]["word_count"]
            > 0
        )


def test_ingestion_requires_auth(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ingest",
            json={
                "title":
                    "Private document",
                "content":
                    "This content must not be accepted without authentication.",
            },
        )

    assert response.status_code == 401


def test_job_is_user_scoped(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        first = create_user_token(
            client,
            "first-job@example.com",
        )

        created = client.post(
            "/api/v1/ingest",
            json={
                "title":
                    "Owned knowledge",
                "content":
                    "This document belongs only to the first authenticated user.",
            },
            headers=headers(first),
        )

        assert created.status_code == 202

        job_id = created.json()[
            "id"
        ]

        second = create_user_token(
            client,
            "second-job@example.com",
        )

        foreign = client.get(
            f"/api/v1/jobs/{job_id}",
            headers=headers(second),
        )

    assert foreign.status_code == 404


def test_ingestion_validation(
    tmp_path,
    monkeypatch,
):
    prepare(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        token = create_user_token(
            client,
            "validation-job@example.com",
        )

        response = client.post(
            "/api/v1/ingest",
            json={
                "title": "x",
                "content": "tiny",
            },
            headers=headers(token),
        )

    assert response.status_code == 422
