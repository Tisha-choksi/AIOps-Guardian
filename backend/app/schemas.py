from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from agents.coordinator.state import AgentResult, EvidenceItem


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class InvestigationSummary(BaseModel):
    investigation_id: str
    target: str
    description: str | None
    status: str
    created_at: datetime


class InvestigationDetail(InvestigationSummary):
    evidence: list[EvidenceItem]
    agent_status: dict[str, AgentResult]


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
