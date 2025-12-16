"""
RAG service orchestrating the entire pipeline
"""
from typing import List, Dict, Any, Iterator
from datetime import datetime
import time
import uuid
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

    def _end_step(self, step: str, start_ts: str, start_time: float, request_id: str, status: str = "ok", **extra):
        """Log completion of a pipeline step with timestamps and duration"""
        end_ts = datetime.utcnow().isoformat()
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "pipeline_step_complete",
            step=step,
            status=status,
            request_id=request_id,
            start_ts=start_ts,
            end_ts=end_ts,
            duration_ms=duration_ms,
            **extra,
        )
    
    def build_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Build context string from search results"""
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            score = result.get('score', 0)
            doc_name = result.get('metadata', {}).get('document_name', 'Unknown')
            
            if score < self.similarity_threshold:
                logger.info(f"Filtering out result {i} (Score {score:.4f} < {self.similarity_threshold})")
                continue
            
            logger.info(f"Including result {i} in context (Score {score:.4f} >= {self.similarity_threshold})")
            text = result.get('text', '')
            context_parts.append(f"[Source {i} from {doc_name}]\n{text}\n")
        
        return "\n".join(context_parts)
    
    def query_stream(self, question: str, top_k: int = None) -> Iterator[Dict[str, Any]]:
        """Query RAG pipeline with streaming response"""
        top_k = top_k or self.top_k
        request_id = str(uuid.uuid4())
        pipeline_start_ts = datetime.utcnow().isoformat()
        pipeline_start = time.perf_counter()
        logger.info("pipeline_start", request_id=request_id, step="query_stream", question_preview=question[:100])
        
        try:
            # Step 1: Embed the question
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            logger.info("Embedding question", request_id=request_id, question=question[:100])
            query_embedding = self.embedding_service.embed_text(question)
            self._end_step("embed_question", step_ts, step_start, request_id)
            
            # Step 2: Vector search
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            logger.info("Searching vector store", request_id=request_id, top_k=top_k)
            search_results = self.vector_store.search(query_embedding, top_k=top_k)
            self._end_step("vector_search", step_ts, step_start, request_id, results=len(search_results))
            
            # Log all results for debugging
            logger.info(f"Found {len(search_results)} raw results", request_id=request_id)
            for i, res in enumerate(search_results):
                logger.info(
                    f"Result {i+1}: Score={res.get('score'):.4f}, Doc={res.get('metadata', {}).get('document_name')}, Text={res.get('text', '')[:50]}...",
                    request_id=request_id,
                )
            
            # Step 3: Build context
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            context = self.build_context(search_results)
            self._end_step("build_context", step_ts, step_start, request_id, context_length=len(context))
            
            # Step 4: Format sources
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
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
            self._end_step("format_sources", step_ts, step_start, request_id, sources_kept=len(sources))
            
            # Step 5: Build prompt
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            prompt = self.generation_service.build_prompt(context, question)
            self._end_step("build_prompt", step_ts, step_start, request_id, context_length=len(context))
            
            # Step 6: Stream generation
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            full_answer = ""
            for chunk in self.generation_service.generate_stream(prompt):
                full_answer += chunk
                yield {
                    "type": "chunk",
                    "content": chunk,
                    "sources": None
                }
            self._end_step("generate_stream", step_ts, step_start, request_id, answer_length=len(full_answer))
            
            # Yield final response with sources
            yield {
                "type": "complete",
                "content": full_answer,
                "sources": [source.dict() for source in sources]
            }

            self._end_step(
                "pipeline_complete",
                pipeline_start_ts,
                pipeline_start,
                request_id,
                total_sources=len(sources),
                answer_length=len(full_answer),
            )
            
        except Exception as e:
            self._end_step("pipeline_error", pipeline_start_ts, pipeline_start, request_id, status="error", error=str(e))
            logger.error("Error in RAG query", request_id=request_id, error=str(e))
            yield {
                "type": "error",
                "content": f"Error processing query: {str(e)}",
                "sources": []
            }
    
    def query(self, question: str, top_k: int = None) -> Dict[str, Any]:
        """Query RAG pipeline with non-streaming response"""
        top_k = top_k or self.top_k
        request_id = str(uuid.uuid4())
        pipeline_start_ts = datetime.utcnow().isoformat()
        pipeline_start = time.perf_counter()
        logger.info("pipeline_start", request_id=request_id, step="query", question_preview=question[:100])
        
        try:
            # Step 1: Embed the question
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            query_embedding = self.embedding_service.embed_text(question)
            self._end_step("embed_question", step_ts, step_start, request_id)
            
            # Step 2: Vector search
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            search_results = self.vector_store.search(query_embedding, top_k=top_k)
            self._end_step("vector_search", step_ts, step_start, request_id, results=len(search_results))
            
            # Step 3: Build context
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            context = self.build_context(search_results)
            self._end_step("build_context", step_ts, step_start, request_id, context_length=len(context))
            
            # Step 4: Format sources
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
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
            self._end_step("format_sources", step_ts, step_start, request_id, sources_kept=len(sources))
            
            # Step 5: Generate response
            step_ts = datetime.utcnow().isoformat()
            step_start = time.perf_counter()
            prompt = self.generation_service.build_prompt(context, question)
            answer = self.generation_service.generate(prompt)
            self._end_step("generate", step_ts, step_start, request_id, answer_length=len(answer))
            
            total_duration_ms = int((time.perf_counter() - pipeline_start) * 1000)
            logger.info(
                "pipeline_complete",
                request_id=request_id,
                step="query",
                total_duration_ms=total_duration_ms,
                sources=len(sources),
                answer_length=len(answer),
            )
            
            return {
                "answer": answer,
                "sources": [source.dict() for source in sources],
                "query_time": total_duration_ms / 1000
            }
            
        except Exception as e:
            self._end_step("pipeline_error", pipeline_start_ts, pipeline_start, request_id, status="error", error=str(e))
            logger.error("Error in RAG query", request_id=request_id, error=str(e))
            return {
                "answer": f"Error processing query: {str(e)}",
                "sources": [],
                "query_time": 0
            }


# Singleton instance
rag_service = RAGService()

