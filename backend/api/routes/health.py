"""
Health check routes
"""
from fastapi import APIRouter, HTTPException
from api.services.vector_store import vector_store
from api.services.embedding_service import embedding_service
from api.services.generation_service import generation_service
from api.utils.config import settings
import requests

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check system health"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check ChromaDB
    try:
        vector_store.list_documents()
        health_status["services"]["chromadb"] = "healthy"
    except Exception as e:
        health_status["services"]["chromadb"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check embedding service
    try:
        embedding_service.get_embedding_dimension()
        health_status["services"]["embedding"] = "healthy"
    except Exception as e:
        health_status["services"]["embedding"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check vLLM
    try:
        if not generation_service.enabled:
            health_status["services"]["vllm"] = "disabled"
        else:
            # Try /v1/models endpoint (OpenAI-compatible)
            response = requests.get(
                f"{generation_service.base_url}/v1/models", 
                timeout=5
            )
            if response.status_code == 200:
                models = response.json()
                model_list = models.get("data", [])
                health_status["services"]["vllm"] = {
                    "status": "healthy",
                    "available_models": [m.get("id", "unknown") for m in model_list],
                    "base_url": generation_service.base_url
                }
            else:
                health_status["services"]["vllm"] = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
                health_status["status"] = "degraded"
    except requests.exceptions.Timeout:
        health_status["services"]["vllm"] = {
            "status": "unhealthy",
            "error": "Connection timeout"
        }
        health_status["status"] = "degraded"
    except requests.exceptions.ConnectionError:
        health_status["services"]["vllm"] = {
            "status": "unhealthy",
            "error": "Connection refused - vLLM server may not be running",
            "hint": f"Start vLLM with: vllm serve {generation_service.model} --port {settings.vllm_port}"
        }
        health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["vllm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    if health_status["status"] == "degraded":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

