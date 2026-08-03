from fastapi import Header, HTTPException, status

from backend.app.config import settings


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
