"""Database models."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    pseudonym_id = Column(String(32), unique=True, index=True, nullable=False)
    is_admin = Column(Integer, default=0)  # 0 = user, 1 = admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversations = relationship("Conversation", back_populates="user")


class Document(Base):
    """Document model for knowledge base."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    source_type = Column(String(50), nullable=False)  # markdown, pdf, text
    content = Column(Text, nullable=False)
    document_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """Chunk model for document segments."""

    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    chunk_metadata = Column("metadata", JSON, default=dict)  # section_heading, page_number, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="chunks")
    embeddings = relationship("Embedding", back_populates="chunk", cascade="all, delete-orphan")


class Embedding(Base):
    """Embedding model for vector storage."""

    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    vector = Column(Vector(1536))  # text-embedding-3-small dimension
    model_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chunk = relationship("Chunk", back_populates="embeddings")


class Conversation(Base):
    """Conversation model to store chat sessions."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for chat messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSON, default=dict)  # citations, safety_outcome, etc.
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")


class SafetyLog(Base):
    """Safety log for tracking safety decisions."""

    __tablename__ = "safety_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="SET NULL"))
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="SET NULL"))
    decision = Column(String(50), nullable=False)  # ok, refused, escalated
    reason_code = Column(String(100), nullable=False)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EvaluationRun(Base):
    """Evaluation run for tracking evaluation metrics."""

    __tablename__ = "evaluation_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_name = Column(String(200), nullable=False)
    run_type = Column(String(50), nullable=False)  # retrieval, answer_quality, cost
    metrics = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
