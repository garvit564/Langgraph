from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import get_settings

settings = get_settings()

# Normalize connection string for SQLAlchemy with the psycopg (v3) driver
db_url = settings.database_url
if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

# Production PostgreSQL Database Engine
engine = create_engine(
    db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Thread-safe database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative Base for ORM models
Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a scoped database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
