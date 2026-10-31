import asyncio
import logging
import uuid
from datetime import datetime, timezone
from langchain_core.messages import AIMessage, HumanMessage

from app.graph.builder import get_graph
from app.infrastructure.database import SessionLocal
from app.models.chat import Conversation, Message
from app.schemas.chat import ChatResponse

logger = logging.getLogger(__name__)


class ConversationBusyError(Exception):
    """Raised when a new message is received while an existing response is still generating."""
    pass


async def generate_chat_response(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    message: str,
) -> ChatResponse:
    """Processes a user chat message asynchronously: acquires an atomic Compare-And-Swap (CAS)
    lock, executes the LangGraph agent pipeline, supports instant abort cancellation,
    and cleanly closes conversation turns in both PostgreSQL and LangGraph checkpoint state.
    """
    logger.info("Initiating chat turn for conversation: %s", conversation_id)

    # -------------------------------------------------------------
    # PHASE 1: Short Database Transaction (~5ms)
    # Atomic CAS Lock Acquisition + User Message Persistence
    # -------------------------------------------------------------
    with SessionLocal() as db:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
        if not conv:
            logger.warning("Conversation %s not found for user: %s", conversation_id, user_id)
            raise ValueError("Conversation not found or access denied.")

        thread_id = conv.thread_id
        is_new_chat = (conv.title == "New Chat")

        # Atomic Compare-And-Swap (CAS) lock check and acquisition
        rows_updated = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
                Conversation.is_processing.is_(False),
            )
            .update(
                {
                    Conversation.is_processing: True,
                    Conversation.cancel_requested: False,
                },
                synchronize_session=False,
            )
        )

        if rows_updated == 0:
            logger.warning("Concurrent generation blocked for busy conversation: %s", conversation_id)
            raise ConversationBusyError(
                "A response is already being generated for this conversation. Please wait or click stop."
            )

        # Persist user prompt message
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=message,
        )
        db.add(user_msg)
        db.commit()
        logger.debug("Persisted user message for conversation: %s", conversation_id)

    # -------------------------------------------------------------
    # PHASE 2: Asynchronous LangGraph Execution
    # Supports instant abort cancellation via asyncio.CancelledError
    # -------------------------------------------------------------
    graph = get_graph()
    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 10,
    }

    final_message = ""
    is_error = False
    was_cancelled = False

    try:
        logger.debug("Executing LangGraph agent asynchronously (thread_id: %s)", thread_id)
        result = await graph.ainvoke(
            {
                "messages": [
                    HumanMessage(content=message)
                ]
            },
            config=config,
        )
        last_msg = result["messages"][-1]
        final_message = getattr(last_msg, "text", str(last_msg.content))
        logger.debug("LangGraph execution finished for conversation: %s", conversation_id)

    except asyncio.CancelledError:
        was_cancelled = True
        logger.info("LangGraph agent execution aborted immediately for conversation: %s", conversation_id)
        raise

    except Exception as exc:
        is_error = True
        logger.exception("Error during LangGraph execution for conversation %s: %s", conversation_id, exc)
        raise

    finally:
        # -------------------------------------------------------------
        # PHASE 3: Execution Finished / Aborted -> Handle DB Persistence & Unlock
        # Option 2: Turn is cleanly closed with [Generation stopped by user] on abort
        # -------------------------------------------------------------
        with SessionLocal() as db:
            active_conv = (
                db.query(Conversation)
                .filter(Conversation.id == conversation_id)
                .first()
            )

            if active_conv:
                stopped_text = "[Generation stopped by user]"

                if was_cancelled:
                    # 1. Persist stopped marker in PostgreSQL messages table
                    ai_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=stopped_text,
                    )
                    db.add(ai_msg)

                    update_data = {
                        "updated_at": datetime.now(timezone.utc),
                        "is_processing": False,
                        "cancel_requested": False,
                    }
                    if is_new_chat:
                        update_data["title"] = message[:40].strip()

                    db.query(Conversation).filter(Conversation.id == conversation_id).update(update_data)
                    db.commit()
                    logger.info("Recorded stop message in DB messages table and unlocked conversation: %s", conversation_id)

                    # 2. Update LangGraph checkpoint so AI knows the turn was closed
                    async def _save_stopped_checkpoint():
                        try:
                            await graph.aupdate_state(
                                config,
                                {"messages": [AIMessage(content=stopped_text)]},
                            )
                            logger.info("Updated LangGraph state with stop marker for thread: %s", thread_id)
                        except Exception as err:
                            logger.warning("Failed to update LangGraph state with stop marker: %s", err)

                    asyncio.create_task(_save_stopped_checkpoint())

                elif not is_error and final_message:
                    # Clean normal completion: persist assistant message to DB
                    ai_msg = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=final_message,
                    )
                    db.add(ai_msg)

                    update_data = {
                        "updated_at": datetime.now(timezone.utc),
                        "is_processing": False,
                        "cancel_requested": False,
                    }
                    if is_new_chat:
                        update_data["title"] = message[:40].strip()

                    db.query(Conversation).filter(Conversation.id == conversation_id).update(update_data)
                    db.commit()
                    logger.info("Saved AI response and unlocked conversation: %s", conversation_id)

                else:
                    # Unexpected error: release lock
                    db.query(Conversation).filter(Conversation.id == conversation_id).update({
                        "is_processing": False,
                        "cancel_requested": False,
                    })
                    db.commit()
                    logger.info("Reset lock immediately for conversation: %s (was_cancelled: %s, is_error: %s)", conversation_id, was_cancelled, is_error)

    return ChatResponse(
        answer=final_message
    )
