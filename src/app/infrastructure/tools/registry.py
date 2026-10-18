from langchain_core.tools import BaseTool

from src.app.infrastructure.tools.search import web_search
from src.app.infrastructure.tools.weather import get_current_weather


def get_tools() -> list[BaseTool]:
    return [
        web_search,
        get_current_weather,
    ]