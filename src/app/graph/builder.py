import logging
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.graph.nodes import agent, summarize_conversation
from app.graph.state import AgentState
from app.infrastructure.checkpointer import get_checkpointer
from app.infrastructure.tools.registry import get_tools

logger = logging.getLogger(__name__)


def should_continue(state: AgentState) -> str:
    """Conditional edge router: Directs flow to tools, summarization, or graph completion."""
    messages = state["messages"]
    last_message = messages[-1]

    # 1. Route to tool execution if the model generated tool calls
    if getattr(last_message, "tool_calls", None):
        logger.debug("Routing flow to 'tools' node.")
        return "tools"

    # 2. Trigger periodic summarization if message history exceeds the threshold
    if len(messages) > 6:
        logger.debug("Message count exceeds threshold (%d messages). Routing to 'summarize_conversation'.", len(messages))
        return "summarize_conversation"

    logger.debug("No tool calls and within message limit. Routing to END.")
    return END


def build_graph():
    """Constructs and compiles the StateGraph workflow with persistent PostgreSQL checkpointer."""
    logger.info("Compiling LangGraph StateGraph agent workflow...")
    graph_builder = StateGraph(AgentState)
    tools = get_tools()

    # Workflow Nodes
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_node("summarize_conversation", summarize_conversation)

    # Workflow Entry Point
    graph_builder.add_edge(START, "agent")

    # Conditional Routing Edges
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "summarize_conversation": "summarize_conversation",
            END: END,
        },
    )

    # Re-entrant and Exit Edges
    graph_builder.add_edge("tools", "agent")
    graph_builder.add_edge("summarize_conversation", END)

    # Bind persistent asynchronous PostgreSQL checkpointer
    checkpointer = get_checkpointer()
    compiled = graph_builder.compile(checkpointer=checkpointer)
    logger.info("LangGraph workflow compiled successfully with asynchronous checkpointer.")
    return compiled


_graph = None


def get_graph():
    """Returns the compiled LangGraph agent workflow instance.
    Lazily compiles within an active asyncio event loop.
    """
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
