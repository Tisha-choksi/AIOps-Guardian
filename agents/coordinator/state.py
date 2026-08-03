"""The contract every agent in the graph must honor.

Every specialized agent (Docker, Kubernetes, Linux, ...) reads target/
description from InvestigationState and returns a partial state update
containing only `evidence` (as EvidenceItem objects) and `agent_status`.
Downstream consumers (Root Cause Agent, the API layer, persistence) only
ever see this normalized shape — never an agent's raw SDK objects.
"""

import operator
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, Field


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class EvidenceItem(BaseModel):
    agent: str
    source_type: str
    severity: Severity
    summary: str
    raw_data: dict = Field(default_factory=dict)
    confidence_signal: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentResult(BaseModel):
    status: Literal["ok", "degraded", "failed"]
    error: str | None = None


def _merge_agent_status(
    left: dict[str, AgentResult], right: dict[str, AgentResult]
) -> dict[str, AgentResult]:
    return {**left, **right}


class InvestigationState(TypedDict):
    investigation_id: str
    target: str
    description: str
    evidence: Annotated[list[EvidenceItem], operator.add]
    agent_status: Annotated[dict[str, AgentResult], _merge_agent_status]


def new_investigation_state(
    investigation_id: str, target: str, description: str
) -> InvestigationState:
    return InvestigationState(
        investigation_id=investigation_id,
        target=target,
        description=description,
        evidence=[],
        agent_status={},
    )
