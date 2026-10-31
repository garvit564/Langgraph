import logging
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.infrastructure.database import get_db
from app.models.chat import User

logger = logging.getLogger(__name__)

# Bearer token security scheme for OpenAPI / Swagger UI
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency to extract and validate the JWT Bearer token, returning the authenticated User."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload or "sub" not in payload:
        logger.warning("Authentication failed: invalid or expired access token provided.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        logger.warning("Authentication failed: invalid UUID format in token subject: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_uuid).first()

    if not user:
        logger.warning("Authentication failed: user record not found for user_id: %s", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.debug("Successfully authenticated user: %s (%s)", user.id, user.email)
    return user
