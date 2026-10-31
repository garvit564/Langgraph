import logging
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt with a generated salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed bcrypt password."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    """Generates a signed JWT access token containing subject and expiration claims."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    logger.debug("Creating JWT access token for user_id: %s", user_id)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decodes and validates a JWT access token, returning the payload or None if invalid."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        logger.warning("JWT token decoding failed: %s", exc)
        return None
