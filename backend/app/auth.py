import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.security import decode_access_token
from database.models import User
from database.session import get_db


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """Dependency guarding service-to-service endpoints (e.g. /investigate).

    JWT-based dashboard-user auth is a later phase; this is intentionally
    the only auth mechanism needed while there is no dashboard yet.
    """
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


def get_current_user(
    authorization: str | None = Header(None), db: Session = Depends(get_db)
) -> User:
    """Dependency guarding dashboard endpoints (e.g. GET /investigations).

    Expects `Authorization: Bearer <jwt>`. Raises 401 on any missing/invalid/
    expired token or unknown user.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = authorization.split(" ", 1)[1]
    subject = decode_access_token(token)
    user = _load_user(db, subject) if subject else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


def _load_user(db: Session, subject: str) -> User | None:
    try:
        user_id = uuid.UUID(subject)
    except ValueError:
        return None
    return db.get(User, user_id)


def verify_service_or_dashboard(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> None:
    """Guards /investigate: accepts either the service API key (webhooks,
    scripts) or a valid dashboard JWT (the frontend triggering a run on a
    logged-in user's behalf). Either is sufficient.
    """
    if x_api_key is not None and x_api_key == settings.api_key:
        return

    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
        subject = decode_access_token(token)
        if subject is not None and _load_user(db, subject) is not None:
            return

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
