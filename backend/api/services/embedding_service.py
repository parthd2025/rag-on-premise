"""
Embedding service using sentence-transformers
"""
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer
from api.utils.config import settings
from api.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Service for generating embeddings using sentence-transformers"""
    
    def __init__(self):
        self.model_name = settings.embedding_model_name
        self.device = settings.embedding_device
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model from local path or Hugging Face"""
        try:
            # Check if local model path is configured
            if settings.embedding_model_path:
                model_path = settings.embedding_model_path
                logger.info("Loading embedding model from local path", path=model_path, device=self.device)
                self.model = SentenceTransformer(model_path, device=self.device)
            else:
                logger.info("Loading Search/Embedding Model (not LLM) from Hugging Face", model=self.model_name, device=self.device)
                self.model = SentenceTransformer(self.model_name, device=self.device)
            
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error("Failed to load embedding model", error=str(e))
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.model:
            self._load_model()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if not self.model:
            self._load_model()
        
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        if not self.model:
            self._load_model()
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
embedding_service = EmbeddingService()

