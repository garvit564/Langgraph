from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.app.graph.nodes import agent, summarize_conversation
from src.app.graph.state import AgentState
from src.app.infrastructure.checkpointer import get_checkpointer
from src.app.infrastructure.tools.registry import get_tools


def should_continue(state: AgentState):
    messages = state["messages"]
    last_message = messages[-1]
    
    # 1. Pehle tool calls check karein:
    if getattr(last_message, "tool_calls", None):
        return "tools"

    # 2. Agar messages 6 se zyada ho gaye hain, toh summarize karne bhejo:
    if len(messages) > 6:
        return "summarize_conversation"

    return END


def build_graph():
    graph_builder = StateGraph(AgentState)
    tools = get_tools()

    # Nodes
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", ToolNode(tools))
    graph_builder.add_node("summarize_conversation", summarize_conversation)

    # Entry point
    graph_builder.add_edge(START, "agent")

    # Conditional Routing
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "summarize_conversation": "summarize_conversation",
            END: END,
        },
    )

    # Edges
    graph_builder.add_edge("tools", "agent")
    graph_builder.add_edge("summarize_conversation", END)

    # Postgres Persistent Checkpointer
    checkpointer = get_checkpointer()
    return graph_builder.compile(checkpointer=checkpointer)


graph = build_graph()


def get_graph():
    return graph