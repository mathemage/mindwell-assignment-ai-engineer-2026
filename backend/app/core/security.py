"""Security utilities including auth and PII detection."""

import re
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.errors import AuthenticationError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return str(pwd_context.hash(password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bool(pwd_context.verify(plain_password, hashed_password))


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    settings = get_settings()
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return str(encoded_jwt)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT access token."""
    settings = get_settings()
    try:
        decoded_payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if not isinstance(decoded_payload, dict):
            raise AuthenticationError("Invalid authentication token payload")
        return {str(key): value for key, value in decoded_payload.items()}
    except JWTError as e:
        raise AuthenticationError("Invalid authentication token") from e


# PII Detection Patterns
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})(?!\w)"
)
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")


def detect_pii(text: str) -> dict[str, list[str]]:
    """Detect PII in text.

    Returns:
        Dictionary with detected PII types and values.
    """
    pii_found: dict[str, list[str]] = {
        "emails": [],
        "phones": [],
        "ssns": [],
    }

    # Email detection
    emails = EMAIL_PATTERN.findall(text)
    if emails:
        pii_found["emails"] = emails

    # Phone detection
    phones = PHONE_PATTERN.findall(text)
    if phones:
        pii_found["phones"] = ["-".join(phone) for phone in phones]

    # SSN detection
    ssns = SSN_PATTERN.findall(text)
    if ssns:
        pii_found["ssns"] = ssns

    return pii_found


def redact_pii(text: str) -> tuple[str, dict[str, list[str]]]:
    """Redact PII from text.

    Returns:
        Tuple of (redacted_text, detected_pii)
    """
    detected_pii = detect_pii(text)
    redacted_text = text

    # Redact emails
    redacted_text = EMAIL_PATTERN.sub("[EMAIL_REDACTED]", redacted_text)

    # Redact phones
    redacted_text = PHONE_PATTERN.sub("[PHONE_REDACTED]", redacted_text)

    # Redact SSNs
    redacted_text = SSN_PATTERN.sub("[SSN_REDACTED]", redacted_text)

    return redacted_text, detected_pii


def pseudonymize_user_id(user_id: str) -> str:
    """Create a pseudonymized user identifier."""
    import hashlib

    return hashlib.sha256(user_id.encode()).hexdigest()[:16]
