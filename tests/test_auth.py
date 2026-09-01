from fastapi.testclient import (
    TestClient,
)

from backend.api import app


def setup_database(
    tmp_path,
    monkeypatch,
):
    path = (
        tmp_path
        / "auth.duckdb"
    )

    monkeypatch.setenv(
        "NEXUS_DB_PATH",
        str(path),
    )

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "test-secret-at-least-32-characters",
    )


def register_and_login(
    client,
    email="mina@example.com",
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


def test_register_login_and_me(
    tmp_path,
    monkeypatch,
):
    setup_database(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        token = register_and_login(
            client
        )

        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization":
                    f"Bearer {token}"
            },
        )

    assert response.status_code == 200
    assert (
        response.json()["email"]
        == "mina@example.com"
    )


def test_protected_route_requires_token(
    tmp_path,
    monkeypatch,
):
    setup_database(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/queries",
            json={
                "query":
                    "Explain hybrid RAG"
            },
        )

    assert response.status_code == 401


def test_invalid_token_is_rejected(
    tmp_path,
    monkeypatch,
):
    setup_database(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/auth/me",
            headers={
                "Authorization":
                    "Bearer invalid-token"
            },
        )

    assert response.status_code == 401


def test_user_cannot_read_another_users_query(
    tmp_path,
    monkeypatch,
):
    setup_database(
        tmp_path,
        monkeypatch,
    )

    with TestClient(app) as client:
        first = register_and_login(
            client,
            "first@example.com",
        )

        created = client.post(
            "/api/v1/queries",
            json={
                "query":
                    "Explain CRAG"
            },
            headers={
                "Authorization":
                    f"Bearer {first}"
            },
        )

        assert created.status_code == 201

        query_id = created.json()[
            "id"
        ]

        second = register_and_login(
            client,
            "second@example.com",
        )

        forbidden = client.get(
            f"/api/v1/queries/{query_id}",
            headers={
                "Authorization":
                    f"Bearer {second}"
            },
        )

    assert forbidden.status_code == 404


def test_duplicate_email_returns_409(
    tmp_path,
    monkeypatch,
):
    setup_database(
        tmp_path,
        monkeypatch,
    )

    payload = {
        "email": "dup@example.com",
        "password": "StrongPass123",
    }

    with TestClient(app) as client:
        first = client.post(
            "/api/v1/auth/register",
            json=payload,
        )

        second = client.post(
            "/api/v1/auth/register",
            json=payload,
        )

    assert first.status_code == 201
    assert second.status_code == 409


def test_jwt_secret_must_be_configured(
    monkeypatch,
):
    import pytest

    from backend.auth import (
        jwt_secret,
    )

    monkeypatch.delenv(
        "NEXUS_JWT_SECRET",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="NEXUS_JWT_SECRET is required",
    ):
        jwt_secret()

    monkeypatch.setenv(
        "NEXUS_JWT_SECRET",
        "too-short",
    )

    with pytest.raises(
        RuntimeError,
        match="at least 32 characters",
    ):
        jwt_secret()
