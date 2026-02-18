"""Chat service for managing conversations."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.agents.orchestrator import ChatOrchestrator
from app.core.logging import get_logger
from app.core.security import pseudonymize_user_id, redact_pii
from app.db.models import Conversation, Message, SafetyLog

logger = get_logger(__name__)


class ChatService:
    """Service for chat operations."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.orchestrator = ChatOrchestrator(db)

    def process_message(self, user_id: int, message: str) -> dict[str, Any]:
        """Process a chat message."""
        logger.info("Processing chat message", user_id=user_id, message_length=len(message))

        # Get or create conversation
        conversation = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .first()
        )

        if not conversation:
            conversation = Conversation(user_id=user_id)
            self.db.add(conversation)
            self.db.flush()

        # Redact PII from user message
        redacted_message, pii_detected = redact_pii(message)

        if pii_detected.get("emails") or pii_detected.get("phones") or pii_detected.get("ssns"):
            logger.warning("PII detected in message", pii_types=list(pii_detected.keys()))

        # Store user message
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=redacted_message,
            metadata={"pii_detected": pii_detected},
        )
        self.db.add(user_message)
        self.db.flush()

        # Process through agent pipeline
        response_data = self.orchestrator.process_query(message)

        # Store assistant response
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_data["answer"],
            metadata={
                "citations": response_data.get("citations", []),
                "safety_outcome": response_data.get("safety_outcome", "ok"),
                "safety_reason": response_data.get("safety_reason", "safe"),
            },
        )
        self.db.add(assistant_message)

        # Log safety decision
        safety_log = SafetyLog(
            conversation_id=conversation.id,
            message_id=user_message.id,
            decision=response_data.get("safety_outcome", "ok"),
            reason_code=response_data.get("safety_reason", "safe"),
            details={"query_length": len(message)},
        )
        self.db.add(safety_log)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(
            "Chat message processed",
            conversation_id=conversation.id,
            safety_outcome=response_data.get("safety_outcome"),
        )

        return response_data

    def get_conversation_history(
        self, user_id: int, conversation_id: int | None = None, limit: int = 50
    ) -> list[Message]:
        """Get conversation history."""
        if conversation_id:
            return (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )
        else:
            # Get latest conversation for user
            conversation = (
                self.db.query(Conversation)
                .filter(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
                .first()
            )
            if not conversation:
                return []

            return (
                self.db.query(Message)
                .filter(Message.conversation_id == conversation.id)
                .order_by(Message.created_at.desc())
                .limit(limit)
                .all()
            )
