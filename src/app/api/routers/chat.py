import logging

from fastapi import APIRouter, HTTPException
from langgraph.errors import GraphRecursionError
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_chat_response


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Chat"],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest) -> ChatResponse:
    message = request.message
    thread_id = request.thread_id
    try:
        return generate_chat_response(message,thread_id)

    except GraphRecursionError:
        logger.warning(
            "Agent execution limit reached."
        )

        raise HTTPException(
            status_code=503,
            detail="The agent could not complete the request within its execution limit.",
        )

    except Exception:
        logger.exception(
            "Chat request failed."
        )

        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable.",
        )