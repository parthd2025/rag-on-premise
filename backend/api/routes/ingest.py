"""
Document ingestion routes
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import Optional
import uuid
import re
from pathlib import Path
from datetime import datetime
from api.models.schemas import IngestResponse
from api.services.document_processor import document_processor
from api.services.embedding_service import embedding_service
from api.services.vector_store import vector_store
from api.services.generation_service import generation_service
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


def generate_questions_background(document_id: str, context_text: str):
    """Generate sample questions in the background"""
    try:
        logger.info("Starting background question generation", document_id=document_id)
        
        prompt = f"""Analyze the following document excerpt and generate 3-5 specific questions that can be answered based on this text.
Return ONLY the questions, one per line. Do not include any introductory text or numbering.

Text:
{context_text}

Questions:"""
        
        # This is the slow part
        generated_text = generation_service.generate(prompt, max_tokens=256, temperature=0.7)
        
        # Parse questions
        valid_questions = []
        for line in generated_text.split('\n'):
            line = line.strip()
            # Remove numbering like "1. ", "- "
            line = re.sub(r'^[\d\-\.\)\s]+', '', line)
            
            # Remove <think> blocks if any remain
            line = re.sub(r'<think>.*?</think>', '', line, flags=re.DOTALL).strip()
            
            if line and '?' in line:
                valid_questions.append(line)
                
        # Limit to 5
        valid_questions = valid_questions[:5]
        
        logger.info("Generated sample questions", count=len(valid_questions), document_id=document_id)
        
        # Store questions in vector store metadata (update existing chunks)
        # Note: We can't easily update metadata for all chunks in Chroma without re-adding them.
        # Enhancements for "Best Practices": Use a proper relational DB (SQLite/Postgres) for document metadata
        # For now, we will skip saving them to DB in this refactor to solve the speed issue first.
        # Ideally, we would push these to the frontend via WebSocket or store in a 'documents' table.
        
    except Exception as e:
        logger.error("Error generating questions in background", error=str(e))



@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    background_tasks: BackgroundTasks,
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
        
        # Prepare context for background question generation
        # Use first few chunks for context
        context_text = "\n".join(chunks[:3])
        if len(context_text) > 3000:
            context_text = context_text[:3000]
            
        # Add background task
        # Note: Since we are returning immediately, the frontend won't get the valid_questions in the response.
        # This is a trade-off for speed. 
        # Ideally we would signal the frontend via WebSocket when questions are ready.
        # For this turn, we just speed up the upload.
        # background_tasks.add_task(generate_questions_background, doc_id, context_text)
        
        # Optimization: We can just skip question generation if speed is the priority.
        # The user asked "where is the problem". It IS the question generation.
        # Let's keep it but make it optional or lightweight? 
        # No, let's move it to background as requested. DOWNSIDE: Frontend won't show questions immediately.
        
        background_tasks.add_task(generate_questions_background, doc_id, context_text)
        
        valid_questions = []

        return IngestResponse(
            document_id=doc_id,
            name=file.filename,
            chunks_created=len(chunks),
            status="success",
            valid_questions=valid_questions
        )
        
    except Exception as e:
        logger.error("Error ingesting document", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")

