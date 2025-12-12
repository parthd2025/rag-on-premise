"""
Document ingestion routes
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional
import uuid
from pathlib import Path
from datetime import datetime
from api.models.schemas import IngestResponse
from api.services.document_processor import document_processor
from api.services.embedding_service import embedding_service
from api.services.vector_store import vector_store
from api.utils.config import settings
from api.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file size and type"""
    # Check file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.allowed_extensions:
        allowed = ", ".join(settings.allowed_extensions)
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {allowed}"
        )
    
    # Note: File size validation happens after reading content
    # because UploadFile doesn't expose size before reading


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    document_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """Upload and ingest a document"""
    try:
        # Validate file type
        validate_file(file)
        
        # Generate document ID if not provided
        doc_id = document_id or str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        file_size = len(content)
        if file_size > settings.max_file_size_bytes:
            max_mb = settings.max_file_size_mb
            actual_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File size ({actual_mb:.2f} MB) exceeds maximum allowed size ({max_mb} MB)"
            )
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save uploaded file
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(file.filename).suffix
        saved_path = upload_dir / f"{doc_id}{file_extension}"
        
        with open(saved_path, "wb") as f:
            f.write(content)
        
        logger.info("File uploaded", document_id=doc_id, filename=file.filename)
        
        # Process document
        chunks, doc_metadata = document_processor.process_document(saved_path)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No text extracted from document")
        
        # Generate embeddings
        logger.info("Generating embeddings", num_chunks=len(chunks))
        embeddings = embedding_service.embed_texts(chunks)
        
        # Prepare metadata
        full_metadata = {
            **doc_metadata,
            "upload_date": datetime.now().isoformat(),
            "original_filename": file.filename
        }
        
        # Store in vector database
        logger.info("Storing in vector database", document_id=doc_id)
        vector_store.add_documents(
            texts=chunks,
            embeddings=embeddings,
            document_id=doc_id,
            document_name=file.filename,
            metadata=full_metadata
        )
        
        # Clean up uploaded file
        try:
            saved_path.unlink()
        except Exception:
            pass
        
        return IngestResponse(
            document_id=doc_id,
            name=file.filename,
            chunks_created=len(chunks),
            status="success"
        )
        
    except Exception as e:
        logger.error("Error ingesting document", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")

