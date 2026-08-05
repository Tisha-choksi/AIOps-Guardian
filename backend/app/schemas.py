from pydantic import BaseModel, Field

from agents.coordinator.state import AgentResult, EvidenceItem


class InvestigateRequest(BaseModel):
    target: str = Field(
        ..., description="Name of the resource to investigate, e.g. a Docker container name"
    )
    description: str | None = Field(
        None, description="Human-provided context, e.g. 'site returning 502'"
    )


class InvestigateResponse(BaseModel):
    investigation_id: str
    status: str
    target: str
    evidence: list[EvidenceItem]
    agent_status: dict[str, AgentResult]
