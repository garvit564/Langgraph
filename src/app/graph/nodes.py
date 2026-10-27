from datetime import datetime
from langchain_core.messages import (
    HumanMessage,
    RemoveMessage,
    SystemMessage,
)
from app.graph.state import AgentState
from app.infrastructure.llm import get_llm
from app.infrastructure.tools.registry import get_tools

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


def agent(state: AgentState) -> dict:
    llm = get_llm()
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)

    # 1. Agar summary bani hui hai to prompt me recap inject karein:
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

    # 2. LLM Call:
    response = llm_with_tools.invoke(
        [
            SystemMessage(content=full_system_prompt),
            *state["messages"],
        ]
    )

    if response.tool_calls:
        for call in response.tool_calls:
            print(f"\n🔧 [TOOL CALLED] -> Name: {call['name']} | Arguments: {call['args']}")
    else:
        print("\n⚡ [NO TOOL CALLED] -> Agent is answering directly without tools.")

    return {
        "messages": [response],
    }


# File ke top imports ko clean karein (src. hata kar):
from app.graph.state import AgentState
from app.infrastructure.llm import get_llm
from app.infrastructure.tools.registry import get_tools


# Aur summarize_conversation function ko safe banayein:
def summarize_conversation(state: AgentState) -> dict:
    llm = get_llm()
    messages = state["messages"]

    # Recent 4 messages chhod kar baaki purane summarize karne hain:
    keep_count = 4
    cutoff = len(messages) - keep_count
    split_idx = cutoff

    # Safe cut jo HumanMessage se shuru ho:
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

    # -------------------------------------------------------------
    # RESILIENCE: Try-Except Block
    # Agar Summarizer LLM fail ho, to user request crash nahi hogi!
    # -------------------------------------------------------------
    try:
        response = llm.invoke(
            [
                *messages_to_summarize,
                HumanMessage(content=prompt),
            ]
        )

        new_summary = response.text
        print(f"\n📝 [SUMMARY UPDATED] ->\n{new_summary}\n")

        # Jo summarize ho gaye unhe active messages se delete karo:
        delete_messages = [RemoveMessage(id=m.id) for m in messages_to_summarize]

        return {
            "summary": new_summary,
            "messages": delete_messages,
        }
    except Exception as e:
        # Soft-fail: Log warning print karein lekin graph ko crash hone se bachayein
        print(f"\n⚠️ [SUMMARIZER WARNING] Summary update failed: {str(e)}. Continuing turn safely.")
        return {}




    
# def final_answer(state: AgentState) -> dict:
#     llm = get_llm()

#     structured_llm = llm.with_structured_output(ChatResponse)
#     last_agent_message = state["messages"][-1].content
#     response: ChatResponse = structured_llm.invoke(
#         [
#             SystemMessage(content=FINAL_SYSTEM_PROMPT),
#             # *state["messages"],
#             HumanMessage(content=f"Please format the following answer into the required JSON schema:\n\n{last_agent_message}")
#         ]
#     )

#     return {
#         "structured_response": response,
#         # "messages": [
#         #     AIMessage(content=response.model_dump_json())
#         # ],
#     }