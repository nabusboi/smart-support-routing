"""
Sentence Embeddings for Semantic Deduplication (Milestone 3)
Uses sentence-transformers to compute cosine similarity between tickets
"""
from sentence_transformers import SentenceTransformer
from typing import List, Tuple
import numpy as np
from config import settings


class EmbeddingService:
    """
    Service for computing sentence embeddings and cosine similarity
    for semantic deduplication.
    """
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.model = None
        self._loaded = False
    
    def load(self):
        """Load the sentence transformer model"""
        if self._loaded:
            return
        
        print(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self._loaded = True
        print("Embedding model loaded successfully")
    
    def get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for a single text.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector
        """
        if not self._loaded:
            self.load()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding
    
    def get_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Get embedding vectors for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not self._loaded:
            self.load()
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings
    
    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Formula: cos(θ) = (A · B) / (||A|| ||B||)
        
        Args:
            a: First embedding vector
            b: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def find_similar_tickets(
        self, 
        ticket_embedding: np.ndarray, 
        ticket_embeddings: List[np.ndarray],
        threshold: float = None
    ) -> List[Tuple[int, float]]:
        """
        Find tickets similar to the given ticket.
        
        Args:
            ticket_embedding: Embedding of the new ticket
            ticket_embeddings: List of embeddings of existing tickets
            threshold: Similarity threshold (default from settings)
            
        Returns:
            List of (index, similarity_score) tuples
        """
        threshold = threshold or settings.SIMILARITY_THRESHOLD
        similar_tickets = []
        
        for idx, existing_embedding in enumerate(ticket_embeddings):
            similarity = self.cosine_similarity(ticket_embedding, existing_embedding)
            if similarity >= threshold:
                similar_tickets.append((idx, similarity))
        
        return similar_tickets
    
    def is_available(self) -> bool:
        """Check if model is loaded and available"""
        return self._loaded


# Singleton instance
embedding_service = EmbeddingService()
