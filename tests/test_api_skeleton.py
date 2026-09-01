from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import app


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

    with TestClient(app) as client:
        health = client.get(
            "/health"
        )

        assert health.status_code == 200
        assert health.json() == {
            "status": "ok",
            "database": "ok",
        }

        created = client.post(
            "/api/v1/queries",
            json={
                "query":
                    "Explain corrective RAG"
            },
        )

        assert created.status_code == 201

        query_id = created.json()["id"]

        fetched = client.get(
            f"/api/v1/queries/{query_id}"
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

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/queries",
            json={"query": "x"},
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

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/queries/not-found"
        )

    assert response.status_code == 404
