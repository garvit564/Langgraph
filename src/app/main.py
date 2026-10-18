from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routers.chat import router as chat_router
from app.core.config import get_settings
from app.infrastructure.checkpointer import get_checkpointer,close_connection_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("LIFESPAN STARTED")

    # Server start hone par tables automatically ban jayengi:
    checkpointer = get_checkpointer()
    checkpointer.setup()
    yield
    close_connection_pool()
    

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,

)




app.include_router(chat_router)


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
    }