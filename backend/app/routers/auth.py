from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.logging_config import get_logger
from backend.app.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.app.security import create_access_token, hash_password, verify_password
from database.models import User
from database.session import get_db

router = APIRouter(prefix="/auth")
logger = get_logger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("auth.user_registered", extra={"extra_fields": {"user_id": str(user.id)}})
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    logger.info("auth.user_logged_in", extra={"extra_fields": {"user_id": str(user.id)}})
    return TokenResponse(access_token=create_access_token(str(user.id)))
