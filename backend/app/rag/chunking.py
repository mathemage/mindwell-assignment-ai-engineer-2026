"""Chunking strategies for different document types."""
import re
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChunkMetadata:
    """Metadata for a chunk."""

    def __init__(
        self,
        section_heading: str | None = None,
        page_number: int | None = None,
        start_char: int | None = None,
        end_char: int | None = None,
    ) -> None:
        self.section_heading = section_heading
        self.page_number = page_number
        self.start_char = start_char
        self.end_char = end_char

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            k: v
            for k, v in {
                "section_heading": self.section_heading,
                "page_number": self.page_number,
                "start_char": self.start_char,
                "end_char": self.end_char,
            }.items()
            if v is not None
        }


class Chunk:
    """A text chunk with metadata."""

    def __init__(self, text: str, index: int, metadata: ChunkMetadata) -> None:
        self.text = text
        self.index = index
        self.metadata = metadata


def chunk_markdown(content: str, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Chunk markdown content by headings."""
    logger.info("Chunking markdown content", content_length=len(content))

    # Split by headings
    heading_pattern = r"^(#{1,6})\s+(.+)$"
    lines = content.split("\n")

    chunks: list[Chunk] = []
    current_section = ""
    current_heading = None
    chunk_index = 0

    for line in lines:
        match = re.match(heading_pattern, line, re.MULTILINE)
        if match:
            # Save previous section if it exists
            if current_section.strip():
                section_chunks = _split_by_size(
                    current_section.strip(), chunk_size, chunk_overlap
                )
                for text in section_chunks:
                    metadata = ChunkMetadata(section_heading=current_heading)
                    chunks.append(Chunk(text, chunk_index, metadata))
                    chunk_index += 1

            # Start new section
            current_heading = match.group(2)
            current_section = line + "\n"
        else:
            current_section += line + "\n"

    # Add final section
    if current_section.strip():
        section_chunks = _split_by_size(current_section.strip(), chunk_size, chunk_overlap)
        for text in section_chunks:
            metadata = ChunkMetadata(section_heading=current_heading)
            chunks.append(Chunk(text, chunk_index, metadata))
            chunk_index += 1

    logger.info("Markdown chunking complete", num_chunks=len(chunks))
    return chunks


def chunk_text(content: str, chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Chunk plain text by size."""
    logger.info("Chunking text content", content_length=len(content))

    text_chunks = _split_by_size(content, chunk_size, chunk_overlap)
    chunks = [
        Chunk(text, index, ChunkMetadata())
        for index, text in enumerate(text_chunks)
    ]

    logger.info("Text chunking complete", num_chunks=len(chunks))
    return chunks


def _split_by_size(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into chunks of approximately chunk_size with overlap."""
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < text_len:
            # Look for sentence ending within next 100 chars
            search_end = min(end + 100, text_len)
            sentence_end = max(
                text.rfind(". ", end, search_end),
                text.rfind("! ", end, search_end),
                text.rfind("? ", end, search_end),
            )
            if sentence_end > end:
                end = sentence_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap if end < text_len else text_len

    return chunks


def chunk_document(
    content: str, source_type: str, chunk_size: int | None = None, chunk_overlap: int | None = None
) -> list[Chunk]:
    """Chunk a document based on its type."""
    settings = get_settings()
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap

    if source_type == "markdown":
        return chunk_markdown(content, chunk_size, chunk_overlap)
    else:
        return chunk_text(content, chunk_size, chunk_overlap)
