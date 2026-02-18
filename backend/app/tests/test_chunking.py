"""Test chunking functionality."""
import pytest

from app.rag.chunking import chunk_document, chunk_markdown, chunk_text


def test_chunk_text_simple():
    """Test simple text chunking."""
    content = "This is a test. " * 100  # 1600 chars
    chunks = chunk_text(content, chunk_size=500, chunk_overlap=50)

    assert len(chunks) > 0
    assert all(isinstance(chunk.text, str) for chunk in chunks)
    assert all(chunk.index >= 0 for chunk in chunks)


def test_chunk_markdown_with_headings():
    """Test markdown chunking respects headings."""
    content = """# Heading 1

Content under heading 1.

## Heading 2

Content under heading 2.

### Heading 3

Content under heading 3.
"""
    chunks = chunk_markdown(content, chunk_size=1000, chunk_overlap=100)

    assert len(chunks) > 0
    # Check that section headings are captured in metadata
    headings = [chunk.metadata.section_heading for chunk in chunks if chunk.metadata.section_heading]
    assert len(headings) > 0


def test_chunk_document_dispatcher():
    """Test chunk_document dispatches to correct chunker."""
    markdown_content = "# Test\n\nContent"
    text_content = "Plain text content"

    markdown_chunks = chunk_document(markdown_content, "markdown")
    text_chunks = chunk_document(text_content, "text")

    assert len(markdown_chunks) > 0
    assert len(text_chunks) > 0


def test_chunk_overlap():
    """Test that chunk overlap works correctly."""
    content = "A" * 1000
    chunks = chunk_text(content, chunk_size=300, chunk_overlap=50)

    assert len(chunks) >= 3
    # Verify chunks have correct indices
    for i, chunk in enumerate(chunks):
        assert chunk.index == i
