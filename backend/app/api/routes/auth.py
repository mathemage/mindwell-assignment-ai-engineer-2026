"""Authentication routes."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import LoginRequest, LoginResponse, UserResponse
from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    hash_password,
    pseudonymize_user_id,
    verify_password,
)
from app.db.models import User
from app.db.session import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Login endpoint (MVP - simple email/password)."""
    logger.info("Login attempt", email=request.email)

    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        logger.warning("Login failed", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    hashed_password = user.hashed_password
    if not isinstance(hashed_password, str) or not verify_password(
        request.password, hashed_password
    ):
        logger.warning("Login failed", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    settings = get_settings()
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    logger.info("Login successful", user_id=user.id)
    return LoginResponse(access_token=access_token, user_id=user.id)


@router.post("/register", response_model=UserResponse)
def register(request: LoginRequest, db: Session = Depends(get_db)) -> UserResponse:
    """Register a new user (MVP)."""
    logger.info("Registration attempt", email=request.email)

    # Check if user exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = hash_password(request.password)
    pseudonym = pseudonymize_user_id(request.email)

    user = User(
        email=request.email,
        hashed_password=hashed_password,
        pseudonym_id=pseudonym,
        is_admin=0,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Registration successful", user_id=user.id)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Get current user information."""
    logger.info("Get current user", user_id=current_user.id)
    return UserResponse.model_validate(current_user)
