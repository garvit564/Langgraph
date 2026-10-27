import uuid
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage

from app.graph.builder import get_graph
from app.infrastructure.database import SessionLocal
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatResponse


def generate_chat_response(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    message: str,
) -> ChatResponse:
    # -------------------------------------------------------------
    # PHASE 1: Short DB Operation (~5ms)
    # -------------------------------------------------------------
    with SessionLocal() as db:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if not conv:
            raise ValueError("Conversation not found or access denied.")

        thread_id = conv.thread_id
        is_new_chat = (conv.title == "New Chat")

        # User message save karein:
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=message,
        )
        db.add(user_msg)
        db.commit()
    # YAHAN DB CONNECTION TURANT RELEASE HO GAYA! Pool me wapas chala gaya!

    # -------------------------------------------------------------
    # PHASE 2: LLM Network I/O (3 to 8 seconds)
    # Is pure time me 0 DATABASE CONNECTIONS hold hain!
    # -------------------------------------------------------------
    graph = get_graph()
    config = {
        "configurable": {
            "thread_id": thread_id,
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

    # -------------------------------------------------------------
    # PHASE 3: Short DB Operation to save AI Reply (~5ms)
    # -------------------------------------------------------------
    with SessionLocal() as db:
        ai_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=final_message,
        )
        db.add(ai_msg)

        # Title aur Updated timestamp update karein:
        update_data = {"updated_at": datetime.now(timezone.utc)}
        if is_new_chat:
            update_data["title"] = message[:40].strip()

        db.query(Conversation).filter(Conversation.id == conversation_id).update(update_data)
        db.commit()
    # YAHAN BHI DB CONNECTION RELEASE!

    return ChatResponse(
        answer=final_message
    )