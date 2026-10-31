import logging
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> dict:
    """Search the web for current information, recent news,
    documentation, and facts that require online research.
    """
    logger.info("Executing web search for query: '%s'", query)
    settings = get_settings()

    search_tool = TavilySearch(
        max_results=5,
        topic="general",
        tavily_api_key=settings.tavily_api_key,
    )

    result = search_tool.invoke({"query": query})
    logger.debug("Web search completed for query: '%s'", query)
    return result
