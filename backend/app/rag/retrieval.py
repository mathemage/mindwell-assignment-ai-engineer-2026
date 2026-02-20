"""Vector-based retrieval using pgvector."""
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.errors import RetrievalError
from app.core.logging import get_logger
from app.db.models import Chunk, Document, Embedding
from app.rag.embeddings import generate_query_embedding

logger = get_logger(__name__)


class RetrievalResult:
    """Result from vector search."""

    def __init__(
        self,
        chunk_id: int,
        document_id: int,
        document_title: str,
        chunk_text: str,
        chunk_index: int,
        similarity_score: float,
        metadata: dict[str, Any],
    ) -> None:
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.document_title = document_title
        self.chunk_text = chunk_text
        self.chunk_index = chunk_index
        self.similarity_score = similarity_score
        self.metadata = metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "document_title": self.document_title,
            "chunk_text": self.chunk_text,
            "chunk_index": self.chunk_index,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata,
        }

    def get_citation(self) -> str:
        """Generate citation string."""
        section = self.metadata.get("section_heading", "")
        if section:
            return f"{self.document_title} - {section}"
        return f"{self.document_title} (chunk {self.chunk_index})"


def retrieve_relevant_chunks(
    db: Session, query: str, top_k: int | None = None, similarity_threshold: float | None = None
) -> list[RetrievalResult]:
    """Retrieve relevant chunks using vector similarity search."""
    settings = get_settings()
    top_k = top_k or settings.top_k_retrieval
    similarity_threshold = similarity_threshold or settings.similarity_threshold

    try:
        logger.info("Starting retrieval", query_length=len(query), top_k=top_k)

        # Generate query embedding
        query_embedding = generate_query_embedding(query)

        # Perform vector similarity search using cosine similarity
        # Using 1 - cosine_distance for similarity score
        # Format embedding as PostgreSQL array literal
        embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
        
        query_sql = text(
            """
            SELECT
                e.id as embedding_id,
                e.chunk_id,
                c.document_id,
                c.chunk_index,
                c.text,
                c.metadata,
                d.title as document_title,
                1 - (e.vector <=> CAST(:query_embedding AS vector)) as similarity
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN documents d ON c.document_id = d.id
            WHERE 1 - (e.vector <=> CAST(:query_embedding AS vector)) > :threshold
            ORDER BY e.vector <=> CAST(:query_embedding AS vector)
            LIMIT :limit
            """
        )

        result = db.execute(
            query_sql,
            {
                "query_embedding": embedding_str,
                "threshold": similarity_threshold,
                "limit": top_k,
            },
        )

        results = []
        for row in result:
            retrieval_result = RetrievalResult(
                chunk_id=row.chunk_id,
                document_id=row.document_id,
                document_title=row.document_title,
                chunk_text=row.text,
                chunk_index=row.chunk_index,
                similarity_score=float(row.similarity),
                metadata=row.metadata or {},
            )
            results.append(retrieval_result)

        logger.info("Retrieval complete", num_results=len(results))
        return results

    except Exception as e:
        logger.error("Retrieval failed", error=str(e))
        raise RetrievalError(f"Failed to retrieve chunks: {str(e)}") from e


def format_context_for_llm(results: list[RetrievalResult]) -> str:
    """Format retrieval results as context for LLM."""
    if not results:
        return ""

    context_parts = []
    for i, result in enumerate(results, 1):
        citation = result.get_citation()
        context_parts.append(f"[Source {i}: {citation}]\n{result.chunk_text}\n")

    return "\n".join(context_parts)
