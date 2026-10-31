import logging
from datetime import datetime
from langchain_core.messages import (
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)
from app.graph.state import AgentState
from app.infrastructure.llm import get_llm
from app.infrastructure.tools.registry import get_tools

logger = logging.getLogger(__name__)
current_date = datetime.now().strftime("%d %B %Y")

AGENT_SYSTEM_PROMPT = f"""You are an intelligent, friendly, and structured AI assistant.
Today's date is {current_date}.

Capabilities:
- web_search: For latest news, current facts, and research.
- get_current_weather: For live weather.

Behavior Guidelines:
1. Be natural, polite, and conversational. For casual chats or greetings, respond warmly and directly.
2. For informational, technical, or research questions:
   - Use clear headings and bullet points.
   - Use markdown code blocks for code snippets.
3. Trust and use tool results when available.
4. Only call tools when external or live information is strictly needed. Never use tools for casual chat or questions about the user already known in context.
"""


async def agent(state: AgentState) -> dict:
    """Core agent node: Injects past conversation recap, binds external tools, and asynchronously invokes the LLM."""
    llm = get_llm()
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)

    # 1. Inject past conversation summary into the system prompt if present
    existing_summary = state.get("summary", "")
    if existing_summary:
        full_system_prompt = (
            f"{AGENT_SYSTEM_PROMPT}\n\n"
            f"--- RECAP OF PREVIOUS CONVERSATION ---\n"
            f"{existing_summary}\n"
            f"--------------------------------------\n"
            f"IMPORTANT: The recap above contains facts and context from earlier in the conversation (such as the user's name, preferences, or previous topics). "
            f"Always use this context to answer questions about the user or past conversation directly and naturally."
        )
    else:
        full_system_prompt = AGENT_SYSTEM_PROMPT

    # 2. Asynchronously invoke the LLM with system instructions and current message history
    response = await llm_with_tools.ainvoke(
        [
            SystemMessage(content=full_system_prompt),
            *state["messages"],
        ]
    )

    if response.tool_calls:
        for call in response.tool_calls:
            logger.info("Tool called by agent: %s with args: %s", call["name"], call["args"])
    else:
        logger.info("Agent responded directly without calling any tools.")

    return {
        "messages": [response],
    }


async def summarize_conversation(state: AgentState) -> dict:
    """Summarizer node: Periodically compresses older messages into an ongoing summary to keep context within limits."""
    llm = get_llm()
    messages = state["messages"]

    # Retain the most recent 4 messages; compress older ones into the running recap
    keep_count = 4
    cutoff = len(messages) - keep_count
    split_idx = cutoff

    # Find a safe cutoff starting at a HumanMessage boundary
    for i in range(cutoff, len(messages)):
        if messages[i].type == "human":
            split_idx = i
            break

    messages_to_summarize = messages[:split_idx]
    if not messages_to_summarize:
        return {}

    existing_summary = state.get("summary", "")
    if existing_summary:
        prompt = (
            f"Existing summary of conversation so far:\n{existing_summary}\n\n"
            "Update the summary by adding key points, user facts, and topics from these new messages above:"
        )
    else:
        prompt = "Create a short summary of this conversation, capturing the user's name, preferences, and key facts:"

    try:
        response = await llm.ainvoke(
            [
                *messages_to_summarize,
                HumanMessage(content=prompt),
            ]
        )

        new_summary = response.text
        logger.info("Conversation summary successfully updated: %s", new_summary[:100] + "..." if len(new_summary) > 100 else new_summary)

        # Remove summarized messages from active state to reclaim context window tokens
        delete_messages = [RemoveMessage(id=m.id) for m in messages_to_summarize]

        return {
            "summary": new_summary,
            "messages": delete_messages,
        }
    except Exception as e:
        # Graceful degradation: log warning and continue without failing the main conversation turn
        logger.warning("Conversation summarization failed gracefully: %s. Continuing execution.", e)
        return {}
