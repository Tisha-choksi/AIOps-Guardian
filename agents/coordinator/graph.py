"""LangGraph wiring: Coordinator -> Docker Agent -> END.

Phase 2 adds parallel fan-out (Coordinator -> [Docker, Kubernetes, ...] ->
join -> Root Cause -> Report). The coordinator node is intentionally a thin
pass-through today; it becomes the fan-out/dispatch point once more agents
exist.
"""

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agents.coordinator.state import InvestigationState
from agents.docker.agent import docker_agent_node
from backend.app.logging_config import get_logger

logger = get_logger(__name__)


def coordinator_node(state: InvestigationState) -> dict:
    logger.info(
        "coordinator.investigation_started",
        extra={
            "extra_fields": {
                "investigation_id": state["investigation_id"],
                "target": state["target"],
            }
        },
    )
    return {}


def build_investigation_graph() -> CompiledStateGraph:
    graph = StateGraph(InvestigationState)

    graph.add_node("coordinator", coordinator_node)
    graph.add_node("docker_agent", docker_agent_node)

    graph.set_entry_point("coordinator")
    graph.add_edge("coordinator", "docker_agent")
    graph.add_edge("docker_agent", END)

    return graph.compile()


_compiled_graph: CompiledStateGraph | None = None


def get_investigation_graph() -> CompiledStateGraph:
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_investigation_graph()
    return _compiled_graph
