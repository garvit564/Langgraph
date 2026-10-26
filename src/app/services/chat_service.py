import uuid
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.graph.builder import get_graph
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatResponse


def generate_chat_response(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    message: str,
    db: Session,
) -> ChatResponse:
    # 1. Check karein ki conversation database me hai aur isi user ki hai:
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        raise ValueError("Conversation not found or access denied.")

    # 2. User Message ko Database me save karein:
    user_msg = Message(
        conversation_id=conv.id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    db.commit()

    # 3. LangGraph ko us conversation ke thread_id ke sath run karein:
    graph = get_graph()
    config = {
        "configurable": {
            "thread_id": conv.thread_id,
        },
        "recursion_limit": 10,
    }

    result = graph.invoke(
        {
            "messages": [
                HumanMessage(content=message)
            ]
        },
        config=config,
    )

    final_message = result["messages"][-1].text

    # 4. AI ka Reply Database me save karein:
    ai_msg = Message(
        conversation_id=conv.id,
        role="assistant",
        content=final_message,
    )
    db.add(ai_msg)

    # 5. Agar naya chat tha to title update karein:
    if conv.title == "New Chat":
        conv.title = message[:40].strip()

    conv.updated_at = datetime.now(timezone.utc)
    db.commit()

    return ChatResponse(
        answer=final_message
    )