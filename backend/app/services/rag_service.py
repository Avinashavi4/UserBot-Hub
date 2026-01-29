"""
RAG (Retrieval Augmented Generation) Service
Handles document upload, embedding, and retrieval for chat
"""
import os
import hashlib
import tempfile
from typing import List, Optional, Dict, Any
from pathlib import Path

# LangChain imports
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# Data directory for ChromaDB
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "rag"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class RAGService:
    """Service for RAG-based document Q&A"""
    
    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.embeddings = None
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self._initialize_embeddings()
    
    def _initialize_embeddings(self):
        """Initialize the embedding model"""
        try:
            # Use a lightweight embedding model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            # Initialize or load existing vectorstore
            persist_directory = str(DATA_DIR / self.collection_name)
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
        except Exception as e:
            print(f"Error initializing embeddings: {e}")
            self.embeddings = None
            self.vectorstore = None
    
    def _get_file_hash(self, content: bytes) -> str:
        """Generate hash for file content"""
        return hashlib.md5(content).hexdigest()
    
    async def add_document(
        self, 
        file_content: bytes, 
        filename: str,
        file_type: str = "pdf"
    ) -> Dict[str, Any]:
        """
        Add a document to the knowledge base
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_type: Type of file (pdf, txt)
            
        Returns:
            Dict with status and document info
        """
        if not self.embeddings or not self.vectorstore:
            return {"success": False, "error": "RAG service not initialized"}
        
        try:
            # Save file temporarily
            suffix = f".{file_type}"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name
            
            # Load document based on type
            if file_type.lower() == "pdf":
                loader = PyPDFLoader(tmp_path)
            else:
                loader = TextLoader(tmp_path)
            
            documents = loader.load()
            
            # Clean up temp file
            os.unlink(tmp_path)
            
            if not documents:
                return {"success": False, "error": "No content extracted from document"}
            
            # Add metadata
            file_hash = self._get_file_hash(file_content)
            for doc in documents:
                doc.metadata["source"] = filename
                doc.metadata["file_hash"] = file_hash
            
            # Split into chunks
            chunks = self.text_splitter.split_documents(documents)
            
            # Add to vectorstore
            self.vectorstore.add_documents(chunks)
            
            return {
                "success": True,
                "filename": filename,
                "chunks": len(chunks),
                "pages": len(documents),
                "file_hash": file_hash
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def query(
        self, 
        question: str, 
        k: int = 4,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Query the knowledge base
        
        Args:
            question: User's question
            k: Number of documents to retrieve
            threshold: Minimum similarity threshold
            
        Returns:
            Dict with relevant documents and context
        """
        if not self.vectorstore:
            return {"success": False, "error": "RAG service not initialized", "documents": []}
        
        try:
            # Similarity search with scores
            results = self.vectorstore.similarity_search_with_score(question, k=k)
            
            documents = []
            context_parts = []
            
            for doc, score in results:
                # Filter by threshold (lower score = more similar in some implementations)
                relevance = 1 - score if score <= 1 else 1 / (1 + score)
                
                if relevance >= threshold or len(documents) < 2:  # Always return at least 2
                    documents.append({
                        "content": doc.page_content,
                        "source": doc.metadata.get("source", "Unknown"),
                        "page": doc.metadata.get("page", 0),
                        "relevance": round(relevance, 3)
                    })
                    context_parts.append(doc.page_content)
            
            # Create combined context
            context = "\n\n---\n\n".join(context_parts)
            
            return {
                "success": True,
                "documents": documents,
                "context": context,
                "query": question
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "documents": []}
    
    async def list_documents(self) -> List[str]:
        """List all unique documents in the knowledge base"""
        if not self.vectorstore:
            return []
        
        try:
            # Get all documents
            collection = self.vectorstore._collection
            results = collection.get()
            
            # Extract unique sources
            sources = set()
            for metadata in results.get("metadatas", []):
                if metadata and "source" in metadata:
                    sources.add(metadata["source"])
            
            return list(sources)
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
    
    async def delete_document(self, filename: str) -> bool:
        """Delete a document from the knowledge base"""
        if not self.vectorstore:
            return False
        
        try:
            collection = self.vectorstore._collection
            # Find and delete documents with matching source
            results = collection.get(where={"source": filename})
            if results["ids"]:
                collection.delete(ids=results["ids"])
                return True
            return False
        except Exception as e:
            print(f"Error deleting document: {e}")
            return False
    
    async def clear_all(self) -> bool:
        """Clear all documents from the knowledge base"""
        if not self.vectorstore:
            return False
        
        try:
            # Delete and recreate collection
            self.vectorstore.delete_collection()
            persist_directory = str(DATA_DIR / self.collection_name)
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=persist_directory
            )
            return True
        except Exception as e:
            print(f"Error clearing documents: {e}")
            return False


# Global instance
rag_service = RAGService()
