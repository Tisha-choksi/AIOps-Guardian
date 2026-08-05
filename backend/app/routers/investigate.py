from uuid import uuid4

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agents.coordinator.graph import get_investigation_graph
from agents.coordinator.state import AgentResult, new_investigation_state
from backend.app.auth import verify_api_key
from backend.app.logging_config import get_logger
from backend.app.schemas import InvestigateRequest, InvestigateResponse
from database.models import Evidence, Investigation
from database.session import get_db

router = APIRouter()
logger = get_logger(__name__)


def _derive_investigation_status(agent_status: dict[str, AgentResult]) -> str:
    """Overall pipeline status from per-agent results.

    All agents ok -> completed. Some ok, some failed -> degraded (partial
    evidence, still useful). None ok -> failed. This is the "degraded but
    complete" resilience pattern: one agent failing never crashes the whole
    investigation, it just narrows the evidence available to Root Cause.
    """
    if not agent_status:
        return "failed"
    statuses = [result.status for result in agent_status.values()]
    if all(s == "ok" for s in statuses):
        return "completed"
    if not any(s == "ok" for s in statuses):
        return "failed"
    return "degraded"


@router.post(
    "/investigate",
    response_model=InvestigateResponse,
    dependencies=[Depends(verify_api_key)],
)
def investigate(payload: InvestigateRequest, db: Session = Depends(get_db)) -> InvestigateResponse:
    investigation_uuid = uuid4()
    investigation_id = str(investigation_uuid)

    initial_state = new_investigation_state(
        investigation_id=investigation_id,
        target=payload.target,
        description=payload.description or "",
    )

    graph = get_investigation_graph()
    result_state = graph.invoke(initial_state)

    evidence_items = result_state["evidence"]
    agent_status = result_state["agent_status"]
    status = _derive_investigation_status(agent_status)

    investigation = Investigation(
        id=investigation_uuid,
        target=payload.target,
        description=payload.description,
        status=status,
        agent_status={name: result.model_dump() for name, result in agent_status.items()},
    )
    db.add(investigation)

    for item in evidence_items:
        db.add(
            Evidence(
                investigation_id=investigation_uuid,
                agent=item.agent,
                source_type=item.source_type,
                severity=item.severity.value,
                summary=item.summary,
                raw_data=item.raw_data,
                confidence_signal=item.confidence_signal,
                timestamp=item.timestamp,
            )
        )

    db.commit()

    logger.info(
        "investigate.completed",
        extra={"extra_fields": {"investigation_id": investigation_id, "status": status}},
    )

    return InvestigateResponse(
        investigation_id=investigation_id,
        status=status,
        target=payload.target,
        evidence=evidence_items,
        agent_status=agent_status,
    )
