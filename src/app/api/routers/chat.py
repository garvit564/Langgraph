import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from langgraph.errors import GraphRecursionError

from app.api.deps import get_current_user
from app.core.cancellation_manager import cancellation_manager
from app.models.chat import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ConversationBusyError, generate_chat_response

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Chat"],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Processes a conversational prompt for an authenticated user within an isolated conversation thread.
    Supports instant abort upon stop request or client cancellation.
    """
    logger.debug("Received chat request for conversation: %s from user: %s", request.conversation_id, current_user.id)
    current_task = asyncio.current_task()
    if current_task:
        cancellation_manager.register_task(request.conversation_id, current_task)

    try:
        return await generate_chat_response(
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            message=request.message,
        )

    except ConversationBusyError as e:
        logger.warning("Conversation %s is busy: %s", request.conversation_id, e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )

    except asyncio.CancelledError:
        logger.info("Chat generation was aborted immediately for conversation: %s", request.conversation_id)
        return ChatResponse(
            answer="[Generation stopped by user]"
        )

    except ValueError as e:
        logger.warning("Validation failure for chat request on conversation %s: %s", request.conversation_id, e)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except GraphRecursionError:
        logger.error("Agent exceeded maximum recursion limit on conversation: %s", request.conversation_id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The agent could not complete the request within its execution limit.",
        )

    except Exception:
        logger.exception("Unexpected exception occurred during chat request processing.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service is temporarily unavailable.",
        )

    finally:
        cancellation_manager.unregister_task(request.conversation_id)
