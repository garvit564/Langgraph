import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from langgraph.errors import GraphRecursionError

from app.api.deps import get_current_user
from app.infrastructure.database import get_db
from app.models.chat import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import generate_chat_response

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Chat"],
)


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
   
) -> ChatResponse:
    """Logged-in user ke liye conversation_id ke context me chat message process karta hai."""
    try:
        return generate_chat_response(
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            message=request.message,
            
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except GraphRecursionError:
        logger.warning("Agent execution limit reached.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The agent could not complete the request within its execution limit.",
        )

    except Exception:
        logger.exception("Chat request failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI service is temporarily unavailable.",
        )