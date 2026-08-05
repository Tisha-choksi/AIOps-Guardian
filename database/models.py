import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Incident(Base):
    """A real-world problem a human/alert reports (e.g. 'website down').

    One incident can have multiple investigations run against it (retries,
    follow-ups). Populated starting Phase 2 — unused but present now so the
    schema doesn't need a breaking migration later.
    """

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    investigations: Mapped[list["Investigation"]] = relationship(back_populates="incident")


class Investigation(Base):
    """A single run of the agent pipeline against a target."""

    __tablename__ = "investigations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("incidents.id"), nullable=True
    )
    target: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    agent_status: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incident: Mapped["Incident | None"] = relationship(back_populates="investigations")
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="investigation", cascade="all, delete-orphan"
    )
    report: Mapped["Report | None"] = relationship(
        back_populates="investigation", cascade="all, delete-orphan", uselist=False
    )


class Evidence(Base):
    """One piece of evidence produced by a single agent."""

    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("investigations.id"))

    agent: Mapped[str] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(16))
    summary: Mapped[str] = mapped_column(Text)
    raw_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    confidence_signal: Mapped[float] = mapped_column(Float)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    investigation: Mapped["Investigation"] = relationship(back_populates="evidence")


class Report(Base):
    """The final root-cause report for an investigation.

    Populated starting Phase 2 (Root Cause / Incident Report agents) — the
    table exists now so Investigation's schema is stable going forward.
    """

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("investigations.id"), unique=True
    )

    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[dict] = mapped_column(JSONB, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    investigation: Mapped["Investigation"] = relationship(back_populates="report")
