"""Admin document management routes."""
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.api.schemas import (
    DocumentListResponse,
    DocumentResponse,
    DocumentUploadRequest,
    ReindexRequest,
    ReindexResponse,
    SuccessResponse,
)
from app.core.logging import get_logger
from app.db.models import Chunk, User
from app.db.session import get_db
from app.services.document_service import DocumentService

logger = get_logger(__name__)
router = APIRouter(prefix="/admin/docs", tags=["admin"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    title: str = Form(...),
    source_type: str = Form(...),
    file: UploadFile = File(None),
    content: str = Form(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    """Upload a document (file or text content)."""
    logger.info("Document upload", admin_id=current_admin.id, source_type=source_type)

    doc_service = DocumentService(db)

    # Extract content
    if file:
        file_bytes = await file.read()
        if source_type == "pdf":
            document_content = doc_service.extract_text_from_pdf(file_bytes)
        else:
            document_content = file_bytes.decode("utf-8")
    elif content:
        document_content = content
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file or content must be provided",
        )

    # Process document
    document = doc_service.process_document(
        title=title,
        content=document_content,
        source_type=source_type,
        metadata={"uploaded_by": current_admin.id},
    )

    # Get chunk count
    num_chunks = db.query(Chunk).filter(Chunk.document_id == document.id).count()

    response = DocumentResponse.model_validate(document)
    response.num_chunks = num_chunks

    logger.info("Document uploaded", document_id=document.id, num_chunks=num_chunks)
    return response


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> DocumentListResponse:
    """List all documents."""
    logger.info("List documents", admin_id=current_admin.id, skip=skip, limit=limit)

    doc_service = DocumentService(db)
    documents = doc_service.list_documents(skip=skip, limit=limit)

    # Add chunk counts
    doc_responses = []
    for doc in documents:
        num_chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).count()
        doc_response = DocumentResponse.model_validate(doc)
        doc_response.num_chunks = num_chunks
        doc_responses.append(doc_response)

    from app.db.models import Document

    total = db.query(Document).count()

    return DocumentListResponse(documents=doc_responses, total=total)


@router.post("/reindex", response_model=ReindexResponse)
def reindex_document(
    request: ReindexRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ReindexResponse:
    """Reindex a document (regenerate chunks and embeddings)."""
    logger.info("Reindex request", admin_id=current_admin.id, document_id=request.document_id)

    doc_service = DocumentService(db)
    doc_service.reindex_document(request.document_id)

    return ReindexResponse(
        success=True,
        message="Document reindexed successfully",
        document_id=request.document_id,
    )


@router.delete("/{document_id}", response_model=SuccessResponse)
def delete_document(
    document_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> SuccessResponse:
    """Delete a document."""
    logger.info("Delete document", admin_id=current_admin.id, document_id=document_id)

    doc_service = DocumentService(db)
    doc_service.delete_document(document_id)

    return SuccessResponse(success=True, message="Document deleted successfully")
