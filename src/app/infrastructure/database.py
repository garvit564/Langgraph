from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import get_settings

settings = get_settings()

# postgresql:// ko postgresql+psycopg:// me convert karte hain SQLAlchemy ke liye:
db_url = settings.database_url
if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

# Database Engine:
engine = create_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Har request ke liye DB session factory:
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Saare models (User, Conversation, Message) is Base se inherit karenge:
Base = declarative_base()


def get_db():
    """FastAPI routes me Database Session inject karne ke liye dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
