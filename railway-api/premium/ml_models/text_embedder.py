"""
Text Embedder Service
---------------------
Generates semantic vector embeddings from text (Titles, Hooks) 
using lightweight Sentence Transformers.

Model: all-MiniLM-L6-v2 (384 dimensional output)
"""

import logging
from typing import List, Union
import numpy as np
import os

# Fix for potential segfaults with tokenizers parallelism
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Lazy loader for sentence_transformers
_model = None

logger = logging.getLogger(__name__)

class TextEmbedder:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.embedding_size = 384 # Known dimension for MiniLM-L6-v2
        
    def _load_model(self):
        global _model
        if _model is None:
            try:
                from sentence_transformers import SentenceTransformer
                # device='cpu' is safer for serverless/basic environments
                _model = SentenceTransformer(self.model_name, device='cpu')
                logger.info(f"Loaded SentenceTransformer: {self.model_name}")
            except ImportError:
                logger.error("sentence-transformers not installed.")
                raise ImportError("Please install 'sentence-transformers' to use TextEmbedder.")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return _model

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embedding(s) for the given text.
        
        Args:
            text: A single string or list of strings.
            
        Returns:
            numpy array of shape (384,) or (n, 384)
        """
        model = self._load_model()
        
        if not text:
            # Return zero vector if empty
            if isinstance(text, str):
                return np.zeros(self.embedding_size)
            else:
                return np.zeros((len(text), self.embedding_size))
                
        try:
            # show_progress_bar=False to keep logs clean
            embeddings = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Fallback to zeros
            if isinstance(text, str):
                return np.zeros(self.embedding_size)
            else:
                return np.zeros((len(text) if isinstance(text, list) else 1, self.embedding_size))

    def get_embedding_size(self) -> int:
        return self.embedding_size

if __name__ == "__main__":
    # Test
    print("Testing TextEmbedder...")
    embedder = TextEmbedder()
    
    # Single
    vec = embedder.embed("Minecraft Speedrun")
    print(f"Shape: {vec.shape}")
    print(f"First 5 dim: {vec[:5]}")
    
    # Compare semantic similarity
    vec1 = embedder.embed("How to bake a cake")
    vec2 = embedder.embed("Cake baking tutorial")
    vec3 = embedder.embed("Minecraft gameplay")
    
    from sklearn.metrics.pairwise import cosine_similarity
    sim1 = cosine_similarity([vec1], [vec2])[0][0]
    sim2 = cosine_similarity([vec1], [vec3])[0][0]
    
    print(f"Similarity (Cake vs Cake): {sim1:.4f}")
    print(f"Similarity (Cake vs Minecraft): {sim2:.4f}")
    
    assert sim1 > sim2
    print("✅ Semantic check passed.")
