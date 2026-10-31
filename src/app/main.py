import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Windows requires SelectorEventLoop for async psycopg / psycopg_pool compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.api.routers.auth import router as auth_router
from app.api.routers.chat import router as chat_router
from app.api.routers.conversations import router as conversations_router
from app.graph.builder import get_graph
from app.infrastructure.checkpointer import close_connection_pool, get_checkpointer, pool
from app.infrastructure.database import SessionLocal
from app.models.chat import Conversation

# Configure root logger format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages application startup and shutdown lifecycle events."""
    logger.info("Initializing application resources on startup...")

    # 1. Open async connection pool and initialize LangGraph checkpointer tables
    await pool.open()
    checkpointer = get_checkpointer()
    await checkpointer.setup()
    get_graph()  # Pre-compile the graph with the checkpointer in the active event loop
    logger.info("LangGraph asynchronous PostgreSQL checkpointer and workflow initialized.")

    # 2. Self-Healing: Reset any stuck conversation processing locks after a crash or restart
    with SessionLocal() as db:
        updated_count = (
            db.query(Conversation)
            .filter(Conversation.is_processing == True)
            .update({
                "is_processing": False,
                "cancel_requested": False,
            })
        )
        db.commit()
        if updated_count > 0:
            logger.info("Unlocked %d stuck conversations on startup.", updated_count)

    yield

    logger.info("Shutting down application resources...")
    await close_connection_pool()
    logger.info("PostgreSQL connection pools closed cleanly.")


app = FastAPI(
    title="Agent Desk API",
    version="1.0.0",
    description="Production-grade AI Assistant Backend with LangGraph and PostgreSQL",
    lifespan=lifespan,
)

# Register API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint to verify backend service availability."""
    return {"status": "healthy", "service": "Agent Desk Backend"}
