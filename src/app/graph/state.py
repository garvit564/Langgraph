from typing import Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict):
    """LangGraph state representation maintaining message history and running conversation recap."""
    messages: Annotated[list[BaseMessage], add_messages]
    summary: str
