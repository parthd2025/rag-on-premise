"""
Query routes for RAG
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.models.schemas import QueryRequest
from api.services.rag_service import rag_service
import json

router = APIRouter()


@router.post("/query")
async def query(request: QueryRequest):
    """Query the RAG system"""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    def generate():
        for result in rag_service.query_stream(request.question, top_k=request.top_k):
            yield f"data: {json.dumps(result)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

