"""Docker investigation agent.

Collects container status/logs/health via the Docker SDK, has the shared
LLM summarize it into an SRE-readable sentence or two, and normalizes the
result into a single EvidenceItem. Any failure (container missing, daemon
unreachable) is caught here and turned into a `failed` AgentResult with no
evidence, rather than raising — one agent's failure must never take down
the whole investigation.
"""

import docker
from docker.errors import DockerException, NotFound

from agents.coordinator.state import AgentResult, EvidenceItem, InvestigationState, Severity
from backend.app.llm_client import summarize
from backend.app.logging_config import get_logger

logger = get_logger(__name__)

_LOG_TAIL_LINES = 100
_LOG_CHAR_CAP = 4000

_SUMMARY_PROMPT = """You are investigating a production incident. Summarize the Docker \
container evidence below in 2-3 concise sentences for an SRE, calling out anything \
abnormal (crash, restarts, unhealthy status, error patterns in logs). Do not speculate \
about root cause outside of Docker itself.

Container: {name}
Status: {status}
Health: {health}
Restart count: {restart_count}
Exit code: {exit_code}

Recent logs (tail):
{logs_tail}
"""


def _collect_container_facts(client: docker.DockerClient, target: str) -> dict:
    container = client.containers.get(target)
    container.reload()
    attrs = container.attrs
    state = attrs.get("State", {})
    logs = container.logs(tail=_LOG_TAIL_LINES, timestamps=True).decode(
        "utf-8", errors="replace"
    )
    return {
        "name": container.name,
        "status": container.status,
        "health": state.get("Health", {}).get("Status"),
        "restart_count": attrs.get("RestartCount", 0),
        "exit_code": state.get("ExitCode"),
        "started_at": state.get("StartedAt"),
        "finished_at": state.get("FinishedAt"),
        "logs_tail": logs[-_LOG_CHAR_CAP:],
    }


def _assess(facts: dict) -> tuple[Severity, float]:
    if facts["status"] in ("exited", "dead") or facts["health"] == "unhealthy":
        return Severity.CRITICAL, 0.9
    if facts["restart_count"]:
        return Severity.WARNING, 0.6
    return Severity.INFO, 0.2


def _fallback_summary(facts: dict) -> str:
    return (
        f"Container '{facts['name']}' status={facts['status']} "
        f"health={facts['health']} restarts={facts['restart_count']} "
        f"exit_code={facts['exit_code']}."
    )


def _summarize_facts(facts: dict) -> str:
    prompt = _SUMMARY_PROMPT.format(**facts)
    try:
        return summarize(prompt).strip()
    except Exception:
        logger.warning(
            "docker_agent.llm_summarization_failed",
            extra={"extra_fields": {"container": facts["name"]}},
        )
        return _fallback_summary(facts)


def docker_agent_node(state: InvestigationState) -> dict:
    target = state["target"]
    investigation_id = state["investigation_id"]
    logger.info(
        "docker_agent.started",
        extra={"extra_fields": {"investigation_id": investigation_id, "target": target}},
    )

    try:
        client = docker.from_env()
        facts = _collect_container_facts(client, target)
    except NotFound:
        error = f"container '{target}' not found"
        logger.warning(
            "docker_agent.container_not_found",
            extra={"extra_fields": {"investigation_id": investigation_id, "target": target}},
        )
        return {"evidence": [], "agent_status": {"docker": AgentResult(status="failed", error=error)}}
    except DockerException as exc:
        error = f"docker daemon unreachable: {exc}"
        logger.error(
            "docker_agent.daemon_unreachable",
            extra={"extra_fields": {"investigation_id": investigation_id, "error": str(exc)}},
        )
        return {"evidence": [], "agent_status": {"docker": AgentResult(status="failed", error=error)}}

    severity, confidence = _assess(facts)
    summary_text = _summarize_facts(facts)

    evidence = EvidenceItem(
        agent="docker",
        source_type="container_status",
        severity=severity,
        summary=summary_text,
        raw_data=facts,
        confidence_signal=confidence,
    )

    logger.info(
        "docker_agent.completed",
        extra={"extra_fields": {"investigation_id": investigation_id, "severity": severity.value}},
    )

    return {"evidence": [evidence], "agent_status": {"docker": AgentResult(status="ok")}}
