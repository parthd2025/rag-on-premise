"""
Document management routes
"""
from fastapi import APIRouter, HTTPException
from typing import List
from api.models.schemas import DocumentInfo
from api.services.vector_store import vector_store
from api.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents():
    """List all ingested documents"""
    try:
        docs = vector_store.list_documents()
        return [DocumentInfo(**doc) for doc in docs]
    except Exception as e:
        logger.error("Error listing documents", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error listing documents: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    try:
        success = vector_store.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully", "document_id": document_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Error deleting document: {str(e)}")

