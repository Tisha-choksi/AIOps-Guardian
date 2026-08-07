"""Unit tests for the /investigate route: auth + request/response shape.

Uses a stub DB session (no real Postgres) and a mocked Docker client/LLM -
this is about the FastAPI wiring, not persistence correctness (covered by
the integration test against a real Postgres).
"""

from fastapi.testclient import TestClient

import agents.docker.agent as docker_agent_module
from backend.app.config import settings
from backend.app.main import app
from database.session import get_db
from tests.unit.test_docker_agent import FakeContainer, FakeContainers, FakeDockerClient


class FakeSession:
    def __init__(self):
        self.added = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

    def close(self):
        pass


def _fake_get_db():
    yield FakeSession()


def test_investigate_happy_path(monkeypatch):
    app.dependency_overrides[get_db] = _fake_get_db
    try:
        container = FakeContainer("sample-app", status="running", health="healthy")
        monkeypatch.setattr(
            docker_agent_module.docker,
            "from_env",
            lambda: FakeDockerClient(FakeContainers(container)),
        )
        monkeypatch.setattr(docker_agent_module, "summarize", lambda p: "All good.")

        client = TestClient(app)
        response = client.post(
            "/investigate",
            json={"target": "sample-app", "description": "check"},
            headers={"X-API-Key": settings.api_key},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "completed"
        assert body["target"] == "sample-app"
        assert body["evidence"][0]["severity"] == "info"
        assert body["agent_status"]["docker"]["status"] == "ok"
    finally:
        app.dependency_overrides.clear()


def test_investigate_rejects_missing_api_key():
    client = TestClient(app)
    response = client.post("/investigate", json={"target": "sample-app"})
    assert response.status_code in (401, 422)


def test_investigate_rejects_wrong_api_key():
    client = TestClient(app)
    response = client.post(
        "/investigate",
        json={"target": "sample-app"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401
