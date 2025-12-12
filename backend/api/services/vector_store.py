"""
Vector store service using ChromaDB
"""
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from api.utils.config import settings
from api.utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """Service for managing vector storage in ChromaDB"""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self.collection_name = settings.chroma_collection_name
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and collection"""
        # Try HTTP client first (if ChromaDB server is running)
        try:
            logger.info("Trying ChromaDB HTTP client", 
                       host=settings.chroma_host, 
                       port=settings.chroma_port)
            
            self.client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info("Retrieved existing collection", collection=self.collection_name)
            except Exception:
                self.collection = self.client.create_collection(name=self.collection_name)
                logger.info("Created new collection", collection=self.collection_name)
            return
                
        except Exception as e:
            logger.info("HTTP client failed, using persistent client", error=str(e))
        
        # Fallback to persistent client (local file-based)
        try:
            import os
            persist_dir = settings.chroma_persist_dir
            os.makedirs(persist_dir, exist_ok=True)
            
            logger.info("Initializing persistent ChromaDB client", path=persist_dir)
            self.client = chromadb.PersistentClient(path=persist_dir)
            
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info("Retrieved existing collection", collection=self.collection_name)
            except Exception:
                self.collection = self.client.create_collection(name=self.collection_name)
                logger.info("Created new collection", collection=self.collection_name)
                
        except Exception as fallback_error:
            logger.error("Failed to initialize ChromaDB", error=str(fallback_error))
            raise
    
    def add_documents(self, 
                     texts: List[str], 
                     embeddings: List[List[float]], 
                     document_id: str,
                     document_name: str,
                     metadata: Optional[Dict[str, Any]] = None) -> int:
        """Add documents to the vector store"""
        try:
            ids = []
            metadatas = []
            
            for i, text in enumerate(texts):
                chunk_id = f"{document_id}_chunk_{i}"
                ids.append(chunk_id)
                
                chunk_metadata = {
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_index": i,
                    "text": text[:500],  # Store first 500 chars for reference
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                metadatas.append(chunk_metadata)
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas
            )
            
            logger.info("Added documents to vector store", 
                       document_id=document_id, 
                       num_chunks=len(texts))
            
            return len(texts)
            
        except Exception as e:
            logger.error("Error adding documents to vector store", error=str(e))
            raise
    
    def search(self, 
               query_embedding: List[float], 
               top_k: int = 5,
               filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            where = filter_dict if filter_dict else None
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )
            
            # Format results
            formatted_results = []
            
            if results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    result = {
                        "id": results['ids'][0][i],
                        "text": results['documents'][0][i],
                        "metadata": results['metadatas'][0][i],
                        "distance": results['distances'][0][i] if 'distances' in results else None,
                        "score": 1 - results['distances'][0][i] if 'distances' in results else None
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error("Error searching vector store", error=str(e))
            raise
    
    def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document"""
        try:
            # Get all chunks for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info("Deleted document chunks", 
                           document_id=document_id, 
                           num_chunks=len(results['ids']))
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error deleting document", document_id=document_id, error=str(e))
            raise
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all unique documents in the store"""
        try:
            # Get all data
            all_data = self.collection.get()
            
            # Group by document_id
            documents = {}
            
            if all_data['ids']:
                for i, doc_id in enumerate(all_data['ids']):
                    metadata = all_data['metadatas'][i]
                    doc_id_key = metadata.get('document_id')
                    
                    if doc_id_key not in documents:
                        documents[doc_id_key] = {
                            "id": doc_id_key,
                            "name": metadata.get('document_name', 'Unknown'),
                            "chunk_count": 0,
                            "file_type": metadata.get('file_type', 'unknown'),
                            "upload_date": metadata.get('upload_date', datetime.now().isoformat())
                        }
                    
                    documents[doc_id_key]["chunk_count"] += 1
            
            return list(documents.values())
            
        except Exception as e:
            logger.error("Error listing documents", error=str(e))
            return []


# Singleton instance
vector_store = VectorStore()

