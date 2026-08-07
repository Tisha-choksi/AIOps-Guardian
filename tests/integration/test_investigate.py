"""Real-infra integration test: requires a running Docker daemon AND a
Postgres reachable at settings.database_url with migrations applied
(`alembic upgrade head`). Skips itself if either is unavailable, rather
than failing CI environments that don't have Docker/Postgres wired up.

Run explicitly with:
    docker compose -f docker/docker-compose.core.yml up -d
    alembic upgrade head
    pytest tests/integration -m integration
"""

import uuid

import docker
import pytest
import sqlalchemy
from fastapi.testclient import TestClient

from backend.app.config import settings
from backend.app.main import app
from database.session import engine

pytestmark = pytest.mark.integration

TEST_CONTAINER_NAME = f"aiops-test-target-{uuid.uuid4().hex[:8]}"


def _docker_available() -> bool:
    try:
        docker.from_env().ping()
        return True
    except Exception:
        return False


def _database_available() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1 FROM investigations LIMIT 1"))
        return True
    except Exception:
        return False


@pytest.fixture
def broken_container():
    if not _docker_available():
        pytest.skip("Docker daemon not reachable")

    client = docker.from_env()
    container = client.containers.run(
        "busybox:latest",
        command="sleep 30",
        name=TEST_CONTAINER_NAME,
        detach=True,
    )
    container.stop()  # simulate a down/crashed container

    yield TEST_CONTAINER_NAME

    try:
        container.remove(force=True)
    except docker.errors.NotFound:
        pass


def test_investigate_detects_stopped_container(broken_container):
    if not _database_available():
        pytest.skip("Postgres not reachable / migrations not applied")

    client = TestClient(app)
    response = client.post(
        "/investigate",
        json={"target": broken_container, "description": "site returning 502"},
        headers={"X-API-Key": settings.api_key},
    )

    assert response.status_code == 200
    body = response.json()

    assert body["status"] in ("completed", "degraded")
    assert body["agent_status"]["docker"]["status"] == "ok"
    assert len(body["evidence"]) == 1
    assert body["evidence"][0]["severity"] == "critical"
