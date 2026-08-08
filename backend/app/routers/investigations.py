import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.auth import get_current_user
from backend.app.schemas import InvestigationDetail, InvestigationSummary
from database.models import Investigation
from database.session import get_db

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/investigations", response_model=list[InvestigationSummary])
def list_investigations(db: Session = Depends(get_db)) -> list[InvestigationSummary]:
    rows = db.execute(
        select(Investigation).order_by(Investigation.created_at.desc())
    ).scalars().all()
    return [
        InvestigationSummary(
            investigation_id=str(row.id),
            target=row.target,
            description=row.description,
            status=row.status,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/investigations/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(investigation_id: str, db: Session = Depends(get_db)) -> InvestigationDetail:
    try:
        row = db.get(Investigation, uuid.UUID(investigation_id))
    except ValueError:
        row = None
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found")

    return InvestigationDetail(
        investigation_id=str(row.id),
        target=row.target,
        description=row.description,
        status=row.status,
        created_at=row.created_at,
        evidence=[
            {
                "agent": e.agent,
                "source_type": e.source_type,
                "severity": e.severity,
                "summary": e.summary,
                "raw_data": e.raw_data,
                "confidence_signal": e.confidence_signal,
                "timestamp": e.timestamp,
            }
            for e in row.evidence
        ],
        agent_status=row.agent_status,
    )
