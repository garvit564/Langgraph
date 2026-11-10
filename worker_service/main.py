import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from worker_service.celery_app import celery_app
from worker_service.config import get_worker_settings
from worker_service.mcp_server import tools_mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_worker_settings()

app = FastAPI(
    title="Agent Desk MCP & Worker Microservice",
    version="1.0.0",
    description="Dedicated Model Context Protocol (MCP) Server on Port 8001 providing tools (send_email, web_search)",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Official Model Context Protocol (MCP) Server SSE Endpoint
# Serves:
# - GET  /mcp/sse      (SSE connection stream)
# - POST /mcp/messages (JSON-RPC tools/list and tools/call)
app.mount("/mcp", tools_mcp.sse_app())


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify worker service and broker availability."""
    try:
        with celery_app.connection_for_read() as conn:
            conn.ensure_connection(max_retries=1)
        broker_status = "connected"
    except Exception as exc:
        broker_status = f"disconnected: {exc}"

    return {
        "status": "healthy",
        "service": "Agent Desk MCP Microservice",
        "port": settings.port,
        "mcp_endpoint": "/mcp/sse",
        "broker": broker_status,
    }
