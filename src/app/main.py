from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routers.auth import router as auth_router
from app.api.routers.chat import router as chat_router
from app.infrastructure.checkpointer import checkpointer, close_connection_pool
from app.api.routers.conversations import router as conversations_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("LIFESPAN STARTED")
    checkpointer.setup()
    yield
    print("LIFESPAN STOPPED")
    close_connection_pool()


app = FastAPI(
    title="Agent Desk API",
    lifespan=lifespan,
)

# Routers include karein:
app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(conversations_router, prefix="/api/v1")


@app.get("/")
def home():
    return {"message": "Welcome to Agent Desk Backend!"}