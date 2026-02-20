"""Authentication and authorization dependencies."""
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AuthenticationError
from app.core.logging import get_logger
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db

logger = get_logger(__name__)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if user_id is None:
            raise AuthenticationError("Invalid token payload")

        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise AuthenticationError("User not found")

        return user

    except (AuthenticationError, ValueError, TypeError) as e:
        logger.warning("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error("Unexpected error during authentication", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Get current admin user."""
    if current_user.is_admin != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
