"""
Document processing service for PDF, TXT, and DOCX files
"""
import os
import re
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pypdf
from docx import Document
from api.utils.config import settings
from api.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    """Service for processing various document formats"""
    
    def __init__(self):
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}]', ' ', text)
        # Strip whitespace
        text = text.strip()
        return text
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """Split text into overlapping chunks"""
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap
        
        # Simple token-based chunking (approximate by splitting on spaces)
        words = text.split()
        chunks = []
        
        if len(words) <= chunk_size:
            return [text]
        
        i = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = ' '.join(chunk_words)
            chunks.append(chunk_text)
            
            # Move forward by chunk_size - overlap
            i += chunk_size - overlap
            
            if i >= len(words):
                break
        
        return chunks
    
    def process_pdf(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from PDF file"""
        try:
            text_parts = []
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text_parts.append(page.extract_text())
            
            full_text = '\n\n'.join(text_parts)
            cleaned_text = self.clean_text(full_text)
            
            metadata = {
                "file_type": "pdf",
                "num_pages": num_pages,
                "file_size": file_path.stat().st_size
            }
            
            return cleaned_text, metadata
            
        except Exception as e:
            logger.error("Error processing PDF", file=str(file_path), error=str(e))
            raise
    
    def process_txt(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                text = file.read()
            
            cleaned_text = self.clean_text(text)
            
            metadata = {
                "file_type": "txt",
                "file_size": file_path.stat().st_size
            }
            
            return cleaned_text, metadata
            
        except Exception as e:
            logger.error("Error processing TXT", file=str(file_path), error=str(e))
            raise
    
    def process_docx(self, file_path: Path) -> Tuple[str, Dict[str, Any]]:
        """Extract text from DOCX file"""
        try:
            doc = Document(file_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            full_text = '\n\n'.join(text_parts)
            cleaned_text = self.clean_text(full_text)
            
            metadata = {
                "file_type": "docx",
                "num_paragraphs": len(text_parts),
                "file_size": file_path.stat().st_size
            }
            
            return cleaned_text, metadata
            
        except Exception as e:
            logger.error("Error processing DOCX", file=str(file_path), error=str(e))
            raise
    
    def process_document(self, file_path: Path) -> Tuple[List[str], Dict[str, Any]]:
        """Process a document and return chunks with metadata"""
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            text, metadata = self.process_pdf(file_path)
        elif file_extension == '.txt':
            text, metadata = self.process_txt(file_path)
        elif file_extension in ['.docx', '.doc']:
            text, metadata = self.process_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        # Chunk the text
        chunks = self.chunk_text(text)
        
        metadata["num_chunks"] = len(chunks)
        metadata["file_name"] = file_path.name
        
        return chunks, metadata


# Singleton instance
document_processor = DocumentProcessor()

