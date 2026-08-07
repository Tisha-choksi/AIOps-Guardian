"""Unit tests for the Docker Agent using a fake Docker client - no daemon required."""

from docker.errors import DockerException, NotFound

from agents.coordinator.state import Severity, new_investigation_state
from agents.docker import agent as docker_agent_module


class FakeContainer:
    def __init__(self, name, status, restart_count=0, health=None, exit_code=0, logs=b"ok\n"):
        self.name = name
        self.status = status
        self._logs = logs
        self.attrs = {
            "RestartCount": restart_count,
            "State": {
                "Health": {"Status": health} if health else {},
                "ExitCode": exit_code,
                "StartedAt": "2026-08-03T00:00:00Z",
                "FinishedAt": "2026-08-03T00:05:00Z",
            },
        }

    def reload(self):
        pass

    def logs(self, tail=100, timestamps=True):
        return self._logs


class FakeContainers:
    def __init__(self, container=None, raise_not_found=False):
        self._container = container
        self._raise_not_found = raise_not_found

    def get(self, name):
        if self._raise_not_found:
            raise NotFound("container not found")
        return self._container


class FakeDockerClient:
    def __init__(self, containers):
        self.containers = containers


def _state(target="sample-app"):
    return new_investigation_state(investigation_id="inv-1", target=target, description="test")


def test_healthy_container_produces_info_evidence(monkeypatch):
    container = FakeContainer("sample-app", status="running", health="healthy")
    monkeypatch.setattr(
        docker_agent_module.docker, "from_env", lambda: FakeDockerClient(FakeContainers(container))
    )
    monkeypatch.setattr(docker_agent_module, "summarize", lambda prompt: "Container is healthy.")

    result = docker_agent_module.docker_agent_node(_state())

    assert result["agent_status"]["docker"].status == "ok"
    assert len(result["evidence"]) == 1
    evidence = result["evidence"][0]
    assert evidence.severity == Severity.INFO
    assert evidence.agent == "docker"
    assert evidence.summary == "Container is healthy."


def test_crashed_container_produces_critical_evidence(monkeypatch):
    container = FakeContainer(
        "sample-app", status="exited", restart_count=5, exit_code=1, logs=b"FATAL: db connection refused\n"
    )
    monkeypatch.setattr(
        docker_agent_module.docker, "from_env", lambda: FakeDockerClient(FakeContainers(container))
    )
    monkeypatch.setattr(docker_agent_module, "summarize", lambda prompt: "Container crashed repeatedly.")

    result = docker_agent_module.docker_agent_node(_state())

    evidence = result["evidence"][0]
    assert evidence.severity == Severity.CRITICAL
    assert evidence.confidence_signal > 0.5
    assert result["agent_status"]["docker"].status == "ok"


def test_container_not_found_returns_failed_status_and_no_evidence(monkeypatch):
    monkeypatch.setattr(
        docker_agent_module.docker,
        "from_env",
        lambda: FakeDockerClient(FakeContainers(raise_not_found=True)),
    )

    result = docker_agent_module.docker_agent_node(_state(target="does-not-exist"))

    assert result["evidence"] == []
    assert result["agent_status"]["docker"].status == "failed"
    assert "not found" in result["agent_status"]["docker"].error


def test_daemon_unreachable_returns_failed_status(monkeypatch):
    def _raise_daemon_error():
        raise DockerException("Cannot connect to the Docker daemon")

    monkeypatch.setattr(docker_agent_module.docker, "from_env", _raise_daemon_error)

    result = docker_agent_module.docker_agent_node(_state())

    assert result["evidence"] == []
    assert result["agent_status"]["docker"].status == "failed"


def test_llm_failure_falls_back_to_raw_summary(monkeypatch):
    container = FakeContainer("sample-app", status="running", health="healthy")
    monkeypatch.setattr(
        docker_agent_module.docker, "from_env", lambda: FakeDockerClient(FakeContainers(container))
    )

    def _raise(prompt):
        raise RuntimeError("ollama unavailable")

    monkeypatch.setattr(docker_agent_module, "summarize", _raise)

    result = docker_agent_module.docker_agent_node(_state())

    assert result["agent_status"]["docker"].status == "ok"
    assert "sample-app" in result["evidence"][0].summary
