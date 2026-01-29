"""RAG System - Document storage and retrieval with embeddings"""
import os
import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import httpx
import asyncio


@dataclass
class Document:
    """A document chunk with metadata"""
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    doc_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.doc_id:
            self.doc_id = hashlib.md5(self.content.encode()).hexdigest()[:12]


class SimpleEmbedder:
    """
    Simple embeddings using word frequency vectors
    No external API needed - works offline
    """
    
    def __init__(self, vector_size: int = 384):
        self.vector_size = vector_size
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization"""
        import re
        text = text.lower()
        tokens = re.findall(r'\b[a-z]+\b', text)
        return tokens
    
    def _hash_token(self, token: str) -> int:
        """Hash token to vector index"""
        return hash(token) % self.vector_size
    
    def embed(self, text: str) -> List[float]:
        """Create embedding from text using TF-IDF-like approach"""
        tokens = self._tokenize(text)
        if not tokens:
            return [0.0] * self.vector_size
        
        # Count token frequencies
        freq: Dict[str, int] = {}
        for token in tokens:
            freq[token] = freq.get(token, 0) + 1
        
        # Create sparse vector
        vector = [0.0] * self.vector_size
        for token, count in freq.items():
            idx = self._hash_token(token)
            # TF component (normalized)
            tf = count / len(tokens)
            vector[idx] += tf
        
        # Normalize
        magnitude = sum(v ** 2 for v in vector) ** 0.5
        if magnitude > 0:
            vector = [v / magnitude for v in vector]
        
        return vector
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts"""
        return [self.embed(text) for text in texts]


class OpenAIEmbedder:
    """Embeddings using OpenAI API (if available)"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/embeddings"
    
    async def embed_async(self, text: str) -> List[float]:
        """Create embedding using OpenAI API"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"input": text, "model": self.model}
            )
            data = response.json()
            return data["data"][0]["embedding"]
    
    def embed(self, text: str) -> List[float]:
        """Sync wrapper"""
        return asyncio.run(self.embed_async(text))


class VectorStore:
    """
    Simple in-memory vector store with persistence
    No external database needed
    """
    
    def __init__(self, embedder=None, storage_path: str = "data/vectors"):
        self.embedder = embedder or SimpleEmbedder()
        self.storage_path = storage_path
        self.documents: Dict[str, Document] = {}
        
        # Create storage directory
        os.makedirs(storage_path, exist_ok=True)
        
        # Load existing documents
        self._load()
    
    def _load(self):
        """Load documents from disk"""
        index_path = os.path.join(self.storage_path, "index.json")
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r') as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = Document(
                            content=doc_data['content'],
                            metadata=doc_data['metadata'],
                            embedding=doc_data['embedding'],
                            doc_id=doc_data['doc_id']
                        )
                        self.documents[doc.doc_id] = doc
            except Exception as e:
                print(f"Error loading vector store: {e}")
    
    def _save(self):
        """Save documents to disk"""
        index_path = os.path.join(self.storage_path, "index.json")
        data = [
            {
                'content': doc.content,
                'metadata': doc.metadata,
                'embedding': doc.embedding,
                'doc_id': doc.doc_id
            }
            for doc in self.documents.values()
        ]
        with open(index_path, 'w') as f:
            json.dump(data, f)
    
    def add_document(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Add a document to the store"""
        embedding = self.embedder.embed(content)
        doc = Document(
            content=content,
            metadata=metadata or {},
            embedding=embedding
        )
        self.documents[doc.doc_id] = doc
        self._save()
        return doc.doc_id
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add multiple documents"""
        doc_ids = []
        for doc_data in documents:
            content = doc_data.get('content', doc_data.get('text', ''))
            metadata = doc_data.get('metadata', {})
            doc_id = self.add_document(content, metadata)
            doc_ids.append(doc_id)
        return doc_ids
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        mag1 = sum(a ** 2 for a in vec1) ** 0.5
        mag2 = sum(b ** 2 for b in vec2) ** 0.5
        if mag1 == 0 or mag2 == 0:
            return 0.0
        return dot_product / (mag1 * mag2)
    
    def search(self, query: str, top_k: int = 5, threshold: float = 0.1) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        if not self.documents:
            return []
        
        query_embedding = self.embedder.embed(query)
        
        # Calculate similarities
        results = []
        for doc in self.documents.values():
            if doc.embedding:
                similarity = self._cosine_similarity(query_embedding, doc.embedding)
                if similarity >= threshold:
                    results.append({
                        'doc_id': doc.doc_id,
                        'content': doc.content,
                        'metadata': doc.metadata,
                        'similarity': similarity
                    })
        
        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save()
            return True
        return False
    
    def clear(self):
        """Clear all documents"""
        self.documents = {}
        self._save()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        return {
            "total_documents": len(self.documents),
            "storage_path": self.storage_path,
            "embedder": type(self.embedder).__name__
        }


class TextSplitter:
    """Split text into chunks for better retrieval"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def split(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                for boundary in ['. ', '.\n', '! ', '? ', '\n\n']:
                    last_boundary = text[start:end].rfind(boundary)
                    if last_boundary > self.chunk_size // 2:
                        end = start + last_boundary + len(boundary)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.overlap
        
        return chunks


class RAGSystem:
    """
    Complete RAG system combining vector store and text processing
    """
    
    def __init__(self, storage_path: str = "data/rag"):
        self.vector_store = VectorStore(storage_path=storage_path)
        self.text_splitter = TextSplitter()
    
    def add_text(self, text: str, metadata: Optional[Dict] = None) -> List[str]:
        """Add text document, splitting into chunks"""
        chunks = self.text_splitter.split(text)
        doc_ids = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **(metadata or {}),
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            doc_id = self.vector_store.add_document(chunk, chunk_metadata)
            doc_ids.append(doc_id)
        
        return doc_ids
    
    def add_pdf_text(self, text: str, filename: str) -> List[str]:
        """Add PDF content"""
        return self.add_text(text, {'source': filename, 'type': 'pdf'})
    
    def add_url_content(self, text: str, url: str) -> List[str]:
        """Add web content"""
        return self.add_text(text, {'source': url, 'type': 'web'})
    
    def query(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """Query the RAG system"""
        results = self.vector_store.search(question, top_k=top_k)
        
        if not results:
            return {
                'context': '',
                'sources': [],
                'found': False
            }
        
        # Combine context from top results
        context_parts = []
        sources = []
        
        for r in results:
            context_parts.append(r['content'])
            sources.append({
                'id': r['doc_id'],
                'similarity': round(r['similarity'], 3),
                'metadata': r['metadata']
            })
        
        return {
            'context': '\n\n---\n\n'.join(context_parts),
            'sources': sources,
            'found': True
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return self.vector_store.get_stats()
    
    def clear(self):
        """Clear all documents"""
        self.vector_store.clear()


# Test
if __name__ == "__main__":
    rag = RAGSystem()
    
    # Add some test content
    test_text = """
    Python is a high-level programming language known for its simplicity and readability.
    It was created by Guido van Rossum and first released in 1991. Python supports multiple
    programming paradigms including procedural, object-oriented, and functional programming.
    
    Python is widely used in web development, data science, artificial intelligence, and
    machine learning. Popular frameworks include Django and Flask for web development,
    and TensorFlow and PyTorch for machine learning.
    
    The Python Package Index (PyPI) hosts thousands of third-party packages that extend
    Python's capabilities. Package management is typically done using pip.
    """
    
    doc_ids = rag.add_text(test_text, {'topic': 'python'})
    print(f"Added {len(doc_ids)} chunks")
    
    # Query
    result = rag.query("What is Python used for?")
    print(f"Found: {result['found']}")
    print(f"Context: {result['context'][:200]}...")
    print(f"Sources: {result['sources']}")
