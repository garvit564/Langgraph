import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.infrastructure.database import get_db
from app.models.chat import User
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Registers a new user account and returns a signed JWT access token."""
    email_clean = payload.email.lower().strip()
    logger.info("Processing user registration attempt for: %s", email_clean)

    # 1. Check for duplicate registered email
    existing_user = db.query(User).filter(User.email == email_clean).first()
    if existing_user:
        logger.warning("Registration rejected: email already registered (%s)", email_clean)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered. Please login.",
        )

    # 2. Hash password and persist user record
    new_user = User(
        email=email_clean,
        hashed_password=hash_password(payload.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info("New user registered successfully: %s (%s)", new_user.id, new_user.email)

    # 3. Generate access token
    token = create_access_token(user_id=str(new_user.id), email=new_user.email)

    return TokenResponse(
        access_token=token,
        user_id=new_user.id,
        email=new_user.email,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticates user credentials and returns a signed JWT access token."""
    email_clean = payload.email.lower().strip()
    logger.info("Processing login attempt for: %s", email_clean)

    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("Login failed: invalid credentials provided for: %s", email_clean)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token(user_id=str(user.id), email=user.email)
    logger.info("User logged in successfully: %s (%s)", user.id, user.email)

    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
    )


@router.get("/me", response_model=UserOut)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile information."""
    return current_user
