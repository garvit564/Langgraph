from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from app.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Plain password ko secure bcrypt hash me convert karta hai."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """User ke typed password ko database ke hash se match karta hai."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str, email: str) -> str:
    """JWT Bearer token generate karta hai jo 7 days tak valid rahega."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Token verify karke payload return karta hai, invalid hone par None deta hai."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None