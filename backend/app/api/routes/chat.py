"""Chat API routes."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.schemas import ChatRequest, ChatResponse, Citation
from app.core.logging import get_logger
from app.db.models import User
from app.db.session import get_db
from app.services.chat_service import ChatService

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    """Process a chat message."""
    logger.info("Chat request", user_id=current_user.id, message_length=len(request.message))

    chat_service = ChatService(db)
    response_data = chat_service.process_message(current_user.id, request.message)

    # Convert to response model
    citations = [Citation(**citation) for citation in response_data.get("citations", [])]

    return ChatResponse(
        answer=response_data["answer"],
        citations=citations,
        safety_outcome=response_data.get("safety_outcome", "ok"),
        safety_reason=response_data.get("safety_reason", "safe"),
    )
