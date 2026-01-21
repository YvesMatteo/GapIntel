"""
Text Embedder Service (OpenAI Version)
--------------------------------------
Generates semantic vector embeddings from text using OpenAI's API.
Replaces local sentence-transformers due to environment instability.

Model: text-embedding-3-small
Dimension: 1536 (can be reduced via API or PCA later)
"""

import logging
import os
from typing import List, Union
import numpy as np
import time
from openai import OpenAI

logger = logging.getLogger(__name__)

class TextEmbedder:
    def __init__(self, model_name: str = 'text-embedding-3-small'):
        self.model_name = model_name
        self.client = None
        self.embedding_size = 1536 
        
    def _get_client(self):
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("OPENAI_API_KEY not found. Text embeddings disabled.")
                return None
            try:
                self.client = OpenAI(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to init OpenAI client: {e}")
                return None
        return self.client

    def embed(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embedding(s) for the given text.
        """
        client = self._get_client()
        if not client:
            return self._zeros(text)
            
        if not text:
            return self._zeros(text)
            
        # Normalize input
        is_single = isinstance(text, str)
        texts = [text] if is_single else text
        
        # Clean empty strings
        texts = [t if t and t.strip() else " " for t in texts]
        
        try:
            response = client.embeddings.create(
                input=texts,
                model=self.model_name,
                encoding_format="float"
            )
            
            embeddings = [data.embedding for data in response.data]
            
            if is_single:
                return np.array(embeddings[0])
            else:
                return np.array(embeddings)
                
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            # Backoff?
            return self._zeros(text)

    def _zeros(self, text):
        if isinstance(text, str):
            return np.zeros(self.embedding_size)
        else:
            return np.zeros((len(text), self.embedding_size))

    def get_embedding_size(self) -> int:
        return self.embedding_size

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    print("Testing OpenAI TextEmbedder...")
    embedder = TextEmbedder()
    
    vec = embedder.embed("Minecraft Speedrun")
    print(f"Shape: {vec.shape}")
    print(f"First 5: {vec[:5]}")
