import sys
from os.path import abspath, dirname, join
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# 1. src directory ko dynamically resolve karke Python path me add karein:
src_path = abspath(join(dirname(__file__), "..", "src"))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from app.core.config import get_settings  
from app.infrastructure.database import Base
import app.models.chat  # Saare models ko register karne ke liye

# Alembic Config object:
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. Target Metadata set karein:
target_metadata = Base.metadata


# 3. LangGraph ki checkpoint tables ko ignore karne ka filter:
def include_object(object, name, type_, reflected, compare_to):
    # LangGraph ki tables ko Alembic touch nahi karega:
    if type_ == "table" and name.startswith("checkpoint"):
        return False
    return True


def run_migrations_offline() -> None:
    """Offline mode me migration chalane ke liye."""
    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online mode me database se connect karke migration chalane ke liye."""
    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("postgresql://") and "+psycopg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()