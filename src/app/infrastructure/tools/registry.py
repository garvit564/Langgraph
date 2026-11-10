"""Tool registry for the LangGraph agent.

Provides built-in external tools alongside dynamically discovered tools from
remote MCP servers via the official langchain-mcp-adapters client.
"""
import logging
from langchain_core.tools import BaseTool

from app.infrastructure.tools.weather import get_current_weather
from app.mcp.client import load_remote_mcp_tools

logger = logging.getLogger(__name__)

_tools_cache: list[BaseTool] | None = None


async def init_tools() -> list[BaseTool]:
    """Initializes and caches agent tools during application startup,
    discovering any remote tools from MCP microservices over standard SSE.
    """
    global _tools_cache
    # Local in-process tools
    base_tools: list[BaseTool] = [
        get_current_weather,
    ]

    # Remote tools dynamically fetched from Server 2 (send_email, web_search, etc.)
    mcp_tools = await load_remote_mcp_tools()
    _tools_cache = base_tools + mcp_tools
    logger.info("Agent tool registry initialized with %d total tools: %s", len(_tools_cache), [t.name for t in _tools_cache])
    return _tools_cache


def get_tools() -> list[BaseTool]:
    """Returns the current list of agent tools.
    Falls back to built-in tools if invoked before lifespan initialization.
    """
    global _tools_cache
    if _tools_cache is None:
        return [get_current_weather]
    return _tools_cache
