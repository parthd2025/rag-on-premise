"""
RAG service orchestrating the entire pipeline
"""
from typing import List, Dict, Any, Iterator
from api.services.embedding_service import embedding_service
from api.services.vector_store import vector_store
from api.services.generation_service import generation_service
from api.models.schemas import SourceChunk
from api.utils.config import settings
from api.utils.logger import get_logger

logger = get_logger(__name__)


class RAGService:
    """Main RAG orchestration service"""
    
    def __init__(self):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.generation_service = generation_service
        self.top_k = settings.top_k
        self.similarity_threshold = settings.similarity_threshold
    
    def build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            score = result.get('score', 0)
            if score < self.similarity_threshold:
                continue
            
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            doc_name = metadata.get('document_name', 'Unknown')
            
            context_parts.append(f"[Source {i} from {doc_name}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def query_stream(self, question: str, top_k: int = None) -> Iterator[Dict[str, Any]]:
        """Query RAG pipeline with streaming response"""
        top_k = top_k or self.top_k
        
        try:
            # Step 1: Embed the question
            logger.info("Embedding question", question=question[:100])
            query_embedding = self.embedding_service.embed_text(question)
            
            # Step 2: Vector search
            logger.info("Searching vector store", top_k=top_k)
            search_results = self.vector_store.search(query_embedding, top_k=top_k)
            
            # Step 3: Build context
            context = self.build_context(search_results)
            logger.info("Built context", context_length=len(context), num_sources=len(search_results))
            
            # Step 4: Format sources
            sources = []
            for result in search_results:
                if result.get('score', 0) >= self.similarity_threshold:
                    metadata = result.get('metadata', {})
                    source = SourceChunk(
                        text=result.get('text', '')[:500],  # Truncate for display
                        document_id=metadata.get('document_id', ''),
                        document_name=metadata.get('document_name', 'Unknown'),
                        chunk_index=metadata.get('chunk_index', 0),
                        score=result.get('score', 0),
                        metadata=metadata
                    )
                    sources.append(source)
            
            # Step 5: Build prompt
            prompt = self.generation_service.build_prompt(context, question)
            
            # Step 6: Stream generation
            full_answer = ""
            for chunk in self.generation_service.generate_stream(prompt):
                full_answer += chunk
                yield {
                    "type": "chunk",
                    "content": chunk,
                    "sources": None
                }
            
            # Yield final response with sources
            yield {
                "type": "complete",
                "content": full_answer,
                "sources": [source.dict() for source in sources]
            }
            
        except Exception as e:
            logger.error("Error in RAG query", error=str(e))
            yield {
                "type": "error",
                "content": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Query RAG pipeline with non-streaming response"""
        top_k = top_k or self.top_k
        
        try:
            import time
            start_time = time.time()
            
            # Step 1: Embed the question
            query_embedding = self.embedding_service.embed_text(question)
            
            # Step 2: Vector search
            search_results = self.vector_store.search(query_embedding, top_k=top_k)
            
            # Step 3: Build context
            context = self.build_context(search_results)
            
            # Step 4: Format sources
            sources = []
            for result in search_results:
                if result.get('score', 0) >= self.similarity_threshold:
                    metadata = result.get('metadata', {})
                    source = SourceChunk(
                        text=result.get('text', '')[:500],
                        document_id=metadata.get('document_id', ''),
                        document_name=metadata.get('document_name', 'Unknown'),
                        chunk_index=metadata.get('chunk_index', 0),
                        score=result.get('score', 0),
                        metadata=metadata
                    )
                    sources.append(source)
            
            # Step 5: Generate response
            prompt = self.generation_service.build_prompt(context, question)
            answer = self.generation_service.generate(prompt)
            
            query_time = time.time() - start_time
            
            return {
                "answer": answer,
                "sources": [source.dict() for source in sources],
                "query_time": query_time
            }
            
        except Exception as e:
            logger.error("Error in RAG query", error=str(e))
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "query_time": 0
            }


# Singleton instance
rag_service = RAGService()

