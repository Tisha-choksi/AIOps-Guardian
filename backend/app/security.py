"""Password hashing + JWT helpers for dashboard-user auth.

Kept separate from auth.py: this module has no FastAPI dependencies (pure
crypto/token functions), auth.py wires them into request-level dependencies.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from backend.app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str | None:
    """Returns the subject (user id) if the token is valid, else None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError:
        return None
    return payload.get("sub")
