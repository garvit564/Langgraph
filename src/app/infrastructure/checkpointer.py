import logging
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Asynchronous connection pool dedicated to LangGraph state checkpointing
pool = AsyncConnectionPool(
    conninfo=settings.database_url,
    max_size=20,
    kwargs={"autocommit": True},
    open=False,
)

_checkpointer: AsyncPostgresSaver | None = None


def get_checkpointer() -> AsyncPostgresSaver:
    """Returns the persistent asynchronous PostgreSQL checkpointer for LangGraph.
    Lazily initialized within an active running asyncio event loop.
    """
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = AsyncPostgresSaver(pool)
    return _checkpointer


async def close_connection_pool() -> None:
    """Gracefully closes all open connections in the asynchronous checkpointer pool."""
    logger.info("Closing LangGraph checkpointer connection pool...")
    await pool.close()
