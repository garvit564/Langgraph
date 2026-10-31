from langchain_core.tools import BaseTool

from app.infrastructure.tools.search import web_search
from app.infrastructure.tools.weather import get_current_weather


def get_tools() -> list[BaseTool]:
    """Returns the list of enabled external tools for the agent."""
    return [
        web_search,
        get_current_weather,
    ]
