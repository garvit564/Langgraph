from langchain_core.messages import HumanMessage

from app.graph.builder import get_graph
from app.schemas.chat import ChatResponse


def generate_chat_response(message: str,thread_id:str) -> ChatResponse:
    graph = get_graph()

    config = {
        "configurable":{
            "thread_id":thread_id,
        },
        "recursion_limit":10
    }

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content=message)
            ]
        },
        config=config
    )

    final_message = result["messages"][-1].text

    return ChatResponse(
        answer=final_message
    )