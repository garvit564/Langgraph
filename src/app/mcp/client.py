"""Official LangChain MCP Client Adapter.

Connects to remote MCP servers over HTTP Server-Sent Events (SSE) using the
official `langchain-mcp-adapters` package. Dynamically converts remote MCP tools
into native LangChain BaseTools without hardcoded wrappers.
"""
import logging
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_mcp_client: MultiServerMCPClient | None = None


def get_mcp_client() -> MultiServerMCPClient:
    """Returns the singleton MultiServerMCPClient configured for remote MCP services."""
    global _mcp_client
    if _mcp_client is None:
        sse_url = f"{settings.worker_service_url.rstrip('/')}/mcp/sse"
        logger.info("Initializing official MultiServerMCPClient connecting to %s", sse_url)
        _mcp_client = MultiServerMCPClient({
            "email_worker": {
                "transport": "sse",
                "url": sse_url,
            }
        })
    return _mcp_client


async def load_remote_mcp_tools() -> list[BaseTool]:
    """Dynamically queries remote MCP servers over the official MCP protocol and returns LangChain tools."""
    try:
        client = get_mcp_client()
        tools = await client.get_tools()
        logger.info("Official MCP client dynamically discovered %d tools from remote servers: %s", len(tools), [t.name for t in tools])
        return tools
    except Exception as exc:
        logger.warning("Could not reach remote MCP Server on Port 8001 (%s). Proceeding with local tools only.", exc)
        return []
