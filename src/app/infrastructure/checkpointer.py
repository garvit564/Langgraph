from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver

from app.core.config import get_settings

settings = get_settings()

# 1. Database Connection Pool:
pool = ConnectionPool(
    conninfo=settings.database_url,
    max_size=20,
    kwargs={"autocommit": True},
)

# 2. Postgres Checkpointer:
checkpointer = PostgresSaver(pool)


def get_checkpointer() -> PostgresSaver:
    return checkpointer

def close_connection_pool():
    pool.close()