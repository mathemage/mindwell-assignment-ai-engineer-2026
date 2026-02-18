"""Embedding generation for text chunks."""
from typing import Any

import openai
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.core.errors import EmbeddingError
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        try:
            logger.info("Generating embedding", text_length=len(text), model=self.model)

            response = self.client.embeddings.create(input=text, model=self.model)

            embedding = response.data[0].embedding
            logger.info("Embedding generated", embedding_dim=len(embedding))
            return embedding

        except Exception as e:
            logger.error("Embedding generation failed", error=str(e))
            raise EmbeddingError(f"Failed to generate embedding: {str(e)}") from e

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        logger.info("Generating batch embeddings", batch_size=len(texts))

        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)

        return embeddings


def generate_query_embedding(query: str) -> list[float]:
    """Generate embedding for a search query."""
    generator = EmbeddingGenerator()
    return generator.generate_embedding(query)
