from fastapi.testclient import (
    TestClient,
)

from backend.api import app


def auth_headers(
    client,
):
    client.post(
        "/api/v1/auth/register",
        json={
            "email":
                "api@example.com",
            "password":
                "StrongPass123",
        },
    )

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email":
                "api@example.com",
            "password":
                "StrongPass123",
        },
    )

    token = login.json()[
        "access_token"
    ]

    return {
        "Authorization":
            f"Bearer {token}"
    }


def test_health_and_persistent_query(
    tmp_path,
    monkeypatch,
):
    database = (
        tmp_path
        / "nexus-test.duckdb"
    )

    monkeypatch.setenv(
        "NEXUS_DB_PATH",
        str(database),
    )

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "test-secret-at-least-32-characters",
    )

    with TestClient(app) as client:
        health = client.get(
            "/health"
        )

        assert health.status_code == 200

        headers = auth_headers(
            client
        )

        created = client.post(
            "/api/v1/queries",
            json={
                "query":
                    "Explain corrective RAG"
            },
            headers=headers,
        )

        assert created.status_code == 201

        query_id = created.json()[
            "id"
        ]

        fetched = client.get(
            f"/api/v1/queries/{query_id}",
            headers=headers,
        )

        assert fetched.status_code == 200
        assert (
            fetched.json()["query"]
            == "Explain corrective RAG"
        )

    assert database.exists()


def test_query_validation(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "NEXUS_DB_PATH",
        str(
            tmp_path
            / "validation.duckdb"
        ),
    )

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "test-secret-at-least-32-characters",
    )

    with TestClient(app) as client:
        headers = auth_headers(
            client
        )

        response = client.post(
            "/api/v1/queries",
            json={"query": "x"},
            headers=headers,
        )

    assert response.status_code == 422


def test_missing_query_returns_404(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "NEXUS_DB_PATH",
        str(
            tmp_path
            / "missing.duckdb"
        ),
    )

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "test-secret-at-least-32-characters",
    )

    with TestClient(app) as client:
        headers = auth_headers(
            client
        )

        response = client.get(
            "/api/v1/queries/not-found",
            headers=headers,
        )

    assert response.status_code == 404
