import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.infrastructure.database import get_db
from app.models.chat import User
from app.schemas.conversation import ConversationCreate, ConversationOut, MessageOut
from app.services.conversation_service import (
    create_new_conversation,
    delete_conversation_by_id,
    get_messages_by_conversation_id,
    list_conversations_for_user,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: ConversationCreate | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Nayi conversation create karne ke liye service ko call karta hai."""
    title = payload.title if payload else None
    return create_new_conversation(db=db, user_id=current_user.id, title=title)


@router.get("", response_model=list[ConversationOut])
def list_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User ki conversations list karne ke liye service ko call karta hai."""
    return list_conversations_for_user(db=db, user_id=current_user.id)


@router.get("/{conversation_id}/messages", response_model=list[MessageOut])
def get_conversation_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Messages fetch karne ke liye service ko call karta hai."""
    try:
        return get_messages_by_conversation_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
def delete_conversation(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Conversation delete karne ke liye service ko call karta hai."""
    try:
        delete_conversation_by_id(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
        return {"message": "Conversation deleted successfully."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )