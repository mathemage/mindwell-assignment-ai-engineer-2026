"""Document processing service."""
from typing import Any

from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.core.errors import DocumentProcessingError
from app.core.logging import get_logger
from app.db.models import Chunk as ChunkModel
from app.db.models import Document, Embedding
from app.rag.chunking import chunk_document
from app.rag.embeddings import EmbeddingGenerator

logger = get_logger(__name__)


class DocumentService:
    """Service for document management."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.embedding_generator = EmbeddingGenerator()

    def process_document(
        self, title: str, content: str, source_type: str, metadata: dict[str, Any] | None = None
    ) -> Document:
        """Process and store a document."""
        try:
            logger.info("Processing document", title=title, source_type=source_type)

            # Create document
            document = Document(
                title=title,
                content=content,
                source_type=source_type,
                metadata=metadata or {},
            )
            self.db.add(document)
            self.db.flush()

            # Chunk the document
            chunks = chunk_document(content, source_type)
            logger.info("Document chunked", num_chunks=len(chunks))

            # Store chunks and generate embeddings
            for chunk in chunks:
                chunk_model = ChunkModel(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    metadata=chunk.metadata.to_dict(),
                )
                self.db.add(chunk_model)
                self.db.flush()

                # Generate and store embedding
                embedding_vector = self.embedding_generator.generate_embedding(chunk.text)
                embedding = Embedding(
                    chunk_id=chunk_model.id,
                    vector=embedding_vector,
                    model_name=self.embedding_generator.model,
                )
                self.db.add(embedding)

            self.db.commit()
            logger.info("Document processed successfully", document_id=document.id)
            return document

        except Exception as e:
            self.db.rollback()
            logger.error("Document processing failed", error=str(e))
            raise DocumentProcessingError(f"Failed to process document: {str(e)}") from e

    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            import io

            logger.info("Extracting text from PDF")
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)

            full_text = "\n\n".join(text_parts)
            logger.info("PDF text extracted", num_pages=len(reader.pages), text_length=len(full_text))
            return full_text

        except Exception as e:
            logger.error("PDF extraction failed", error=str(e))
            raise DocumentProcessingError(f"Failed to extract text from PDF: {str(e)}") from e

    def reindex_document(self, document_id: int) -> None:
        """Reindex a document (regenerate chunks and embeddings)."""
        try:
            logger.info("Reindexing document", document_id=document_id)

            document = self.db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise DocumentProcessingError(f"Document {document_id} not found")

            # Delete existing chunks and embeddings (cascade will handle embeddings)
            self.db.query(ChunkModel).filter(ChunkModel.document_id == document_id).delete()
            self.db.flush()

            # Rechunk and reembed
            chunks = chunk_document(document.content, document.source_type)

            for chunk in chunks:
                chunk_model = ChunkModel(
                    document_id=document.id,
                    chunk_index=chunk.index,
                    text=chunk.text,
                    metadata=chunk.metadata.to_dict(),
                )
                self.db.add(chunk_model)
                self.db.flush()

                embedding_vector = self.embedding_generator.generate_embedding(chunk.text)
                embedding = Embedding(
                    chunk_id=chunk_model.id,
                    vector=embedding_vector,
                    model_name=self.embedding_generator.model,
                )
                self.db.add(embedding)

            self.db.commit()
            logger.info("Document reindexed successfully", document_id=document_id)

        except Exception as e:
            self.db.rollback()
            logger.error("Document reindexing failed", error=str(e))
            raise DocumentProcessingError(f"Failed to reindex document: {str(e)}") from e

    def list_documents(self, skip: int = 0, limit: int = 100) -> list[Document]:
        """List documents."""
        return self.db.query(Document).offset(skip).limit(limit).all()

    def get_document(self, document_id: int) -> Document | None:
        """Get a document by ID."""
        return self.db.query(Document).filter(Document.id == document_id).first()

    def delete_document(self, document_id: int) -> None:
        """Delete a document."""
        document = self.get_document(document_id)
        if document:
            self.db.delete(document)
            self.db.commit()
            logger.info("Document deleted", document_id=document_id)
