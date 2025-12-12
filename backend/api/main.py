"""
FastAPI main application entry point
"""
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import time

from api.routes import query, ingest, documents, health
from api.utils.logger import setup_logging, get_logger
from api.utils.config import settings

# Setup logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="Local RAG API",
    description="Free, local RAG application using ChromaDB and vLLM",
    version="1.0.0"
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID to all requests for tracking"""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id
    
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        request_id=request_id,
        client=request.client.host if request.client else "unknown"
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    logger.info(
        "Request completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        request_id=request_id,
        process_time=f"{process_time:.3f}s"
    )
    
    return response

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(ingest.router, prefix="/api", tags=["ingest"])
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.get("/")
async def root():
    return {"message": "Local RAG API", "status": "running"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

