"""
Configuration management
"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix=""
    )
    
    # ChromaDB settings
    chroma_host: str = "localhost"
    chroma_port: int = Field(default=8002, description="ChromaDB port (changed from 8000 to avoid conflict)")
    chroma_collection: str = "rag_documents"
    chroma_persist_dir: str = "./chroma_db"
    
    # Embedding model settings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_model_path: Optional[str] = Field(default=None, description="Local path to embedding model (overrides embedding_model if set)")
    embedding_device: str = Field(default="cpu", description="Device for embeddings: cpu or cuda")
    
    # vLLM settings
    vllm_host: str = "localhost"
    vllm_port: int = 8001
    vllm_base_url: str = "http://localhost:8001"
    vllm_model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    vllm_model_path: Optional[str] = Field(default=None, description="Local path to LLM model (for vLLM --model-path)")
    vllm_enabled: bool = True
    vllm_timeout: int = Field(default=60, ge=10, le=300, description="vLLM request timeout in seconds")
    vllm_max_retries: int = Field(default=3, ge=0, le=10, description="Max retries for vLLM requests")
    
    # Local models directory
    models_dir: str = Field(default="./models", description="Directory to store downloaded models")
    
    # Alternative LLM settings (OpenAI)
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    use_openai: bool = False
    
    # Ollama Settings (Fast local inference - recommended for Windows)
    use_ollama: bool = Field(default=False, description="Use Ollama for local inference")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama server URL")
    ollama_model: str = Field(default="qwen2.5:0.5b", description="Ollama model name")
    
    # Local transformers-based inference (fallback - uses Qwen2.5-0.5B)
    use_local_transformers: bool = Field(default=True, description="Use local transformers for inference when Ollama/vLLM unavailable")
    local_model_id: str = Field(default="Qwen/Qwen2.5-0.5B-Instruct", description="HuggingFace model ID for local inference")
    local_device: str = Field(default="cpu", description="Device for local model: auto, cpu, or cuda")
    
    # Chunking settings
    chunk_size: int = Field(default=300, ge=50, le=2000, description="Text chunk size in tokens")
    chunk_overlap: int = Field(default=50, ge=0, le=200, description="Chunk overlap in tokens")
    
    # RAG settings
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top results to retrieve")
    similarity_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    
    # Document storage
    upload_dir: str = "./uploads"
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="Maximum file size in MB")
    allowed_file_types: str = "pdf,txt,docx"
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1024, le=65535, description="FastAPI server port")
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level: DEBUG, INFO, WARNING, ERROR")
    
    @field_validator('chunk_overlap')
    @classmethod
    def validate_chunk_overlap(cls, v: int, info) -> int:
        """Ensure chunk_overlap is less than chunk_size"""
        if hasattr(info, 'data') and 'chunk_size' in info.data:
            if v >= info.data['chunk_size']:
                raise ValueError("chunk_overlap must be less than chunk_size")
        return v
    
    @property
    def chroma_collection_name(self) -> str:
        return self.chroma_collection
    
    @property
    def embedding_model_name(self) -> str:
        return self.embedding_model
    
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def allowed_extensions(self) -> list[str]:
        """Get list of allowed file extensions"""
        return [f".{ext.strip()}" for ext in self.allowed_file_types.split(",")]
    
    @property
    def cors_origins_list(self) -> list[str]:
        """Get list of CORS origins"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()

