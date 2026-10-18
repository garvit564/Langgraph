from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from src.app.core.config import get_settings


@tool
def web_search(query: str) -> dict:
    """Search the web for current information, recent news,
    documentation, and facts that require online research.
    """

    settings = get_settings()

    search_tool = TavilySearch(
        max_results=5,
        topic="general",
        tavily_api_key=settings.tavily_api_key,
    )

    return search_tool.invoke({"query": query})