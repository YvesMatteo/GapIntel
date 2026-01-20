"""
Sentiment Engine for GapIntel.
Uses DistilBERT for core sentiment and heuristic layers for specific GapIntel categories.
"""

import logging
from typing import List, Dict, Union
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

import re
from collections import Counter
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class SentimentEngine:
    """
    Advanced Sentiment Analysis using DistilBERT + Custom Heuristics.
    
    Classes:
    - Positive (ML)
    - Negative (ML)
    - Inquiry (Heuristic)
    - Confusion (Heuristic)
    - Implementation Success (Heuristic)
    """
    
    def __init__(self):
        self.pipeline = None
        self.embedding_pipeline = None
        self.prototypes = {}
        self.prototype_embeddings = {}
        
        if TRANSFORMERS_AVAILABLE:
            try:
                # 1. Sentiment Model (Fine-tuned SST-2)
                self.pipeline = pipeline(
                    "sentiment-analysis", 
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1
                )
                logger.info("✅ DistilBERT Sentiment Model loaded successfully")
                
                # 2. Embedding Model for Categorization (Feature Extraction)
                # Use base DistilBERT for better semantic representations
                self.embedding_pipeline = pipeline(
                    "feature-extraction", 
                    model="distilbert-base-uncased",
                    tokenizer="distilbert-base-uncased",
                    device=-1
                )
                self._initialize_prototypes()
                logger.info("✅ DistilBERT Embedding Model loaded for categorization")
                
            except Exception as e:
                logger.error(f"❌ Failed to load Transformers models: {e}")
                self.pipeline = None
                self.embedding_pipeline = None
        else:
            logger.warning("⚠️ Transformers library not found. Falling back to pure heuristics.")

    def _initialize_prototypes(self):
        """Initialize and embed prototype sentences for zero-shot categorization."""
        self.prototypes = {
            'success': [
                "I tried this method and it worked perfectly",
                "I saw great results after implementing this",
                "This strategy helped me grow my channel",
                "Thanks for the tutorial, I did it"
            ],
            'confusion': [
                "I am confused about this part",
                "I don't understand how to do this",
                "This is not working for me",
                "I'm stuck and need help",
                "Can you clarify this step?"
            ],
            'inquiry': [
                "How do I do this?",
                "Can you make a video about X?",
                "What camera do you use?",
                "Do you have any tips for beginners?",
                "Question about the process"
            ]
        }
        
        # Pre-compute embeddings for prototypes
        if self.embedding_pipeline:
            for category, sentences in self.prototypes.items():
                embeddings = []
                for sent in sentences:
                    emb = self._get_embedding(sent)
                    if emb is not None:
                        embeddings.append(emb)
                
                if embeddings:
                    # Store mean embedding for the category
                    self.prototype_embeddings[category] = np.mean(embeddings, axis=0)

    def analyze_batch(self, comments: List[Dict]) -> List[Dict]:
        """
        Analyze a batch of comments adding 'sentiment' and 'category' fields.
        """
        texts = [c.get('text', '')[:512] for c in comments] # Truncate for BERT
        
        ml_results = []
        if self.pipeline and texts:
            try:
                ml_results = self.pipeline(texts)
            except Exception as e:
                logger.error(f"Batch inference failed: {e}")
                ml_results = [{'label': 'NEUTRAL', 'score': 0.5}] * len(texts)
        else:
             ml_results = [{'label': 'NEUTRAL', 'score': 0.5}] * len(texts)
             
        enhanced_comments = []
        
        for i, comment in enumerate(comments):
            text = comment.get('text', '')
            ml_res = ml_results[i]
            
            # Base Sentiment (POSITIVE/NEGATIVE)
            base_sentiment = ml_res['label']
            confidence = ml_res['score']
            
            # Refine with GapIntel specifics
            category = self._classify_category(text, base_sentiment)
            
            # Override sentiment for specific categories if needed
            if category in ['confusion', 'inquiry']:
                final_sentiment = 'NEUTRAL'
            elif category == 'success':
                final_sentiment = 'POSITIVE'
            else:
                final_sentiment = base_sentiment
                
            comment['sentiment'] = final_sentiment
            comment['sentiment_score'] = confidence
            comment['category'] = category
            
            enhanced_comments.append(comment)
            
        return enhanced_comments

    def _get_embedding(self, text: str) -> np.ndarray:
        """Get pooled embedding for text."""
        try:
            # Output is list of lists: [batch_size, seq_len, hidden_dim]
            # Batch size is 1. We want mean over seq_len.
            outputs = self.embedding_pipeline(text[:512])
            token_embeddings = np.array(outputs[0]) # (seq_len, 768)
            # Mean pooling
            return np.mean(token_embeddings, axis=0)
        except Exception:
            return None

    def _classify_category(self, text: str, base_sentiment: str) -> str:
        """Classify comment using embeddings (scientific) or regex (fallback)."""
        text_lower = text.lower()
        
        # 1. Scientific Classification (Embedding Similarity)
        if self.embedding_pipeline and self.prototype_embeddings:
            try:
                # Get text embedding
                text_emb = self._get_embedding(text)
                if text_emb is not None:
                    # Calculate similarity to each category prototype
                    scores = {}
                    for category, proto_emb in self.prototype_embeddings.items():
                        # Cosine similarity
                        sim = cosine_similarity([text_emb], [proto_emb])[0][0]
                        scores[category] = sim
                    
                    # Get best match
                    best_category = max(scores, key=scores.get)
                    best_score = scores[best_category]
                    
                    # Threshold for valid classification (e.g. > 0.6 similarity)
                    # Note: DistilBERT raw embeddings aren't always cosine-optimized like S-BERT
                    # But often suffice for gross categorization.
                    # We accept if significantly better than others or high absolute
                    if best_score > 0.75: 
                         return best_category
            except Exception as e:
                logger.debug(f"Embedding classification failed: {e}")
        
        # 2. Heuristic Fallback (Regex)
        # 1. Implementation Success (High Value)
        success_patterns = [
            r"i tried this", r"worked for me", r"saw results", r"just did this",
            r"changed my", r"thanks to this", r"implementation", r"started doing"
        ]
        if any(re.search(p, text_lower) for p in success_patterns) and base_sentiment == 'POSITIVE':
            return "success"
            
        # 2. Confusion / Pain Points (High Value)
        confusion_patterns = [
            r"confused", r"don't understand", r"doesn't work", r"stuck", 
            r"help", r"trouble", r"fail", r"hard to", r"unsure", r"clarify"
        ]
        if any(re.search(p, text_lower) for p in confusion_patterns):
            return "confusion"
            
        # 3. Inquiry / Questions
        if "?" in text or any(w in text_lower for w in ["how to", "what if", "can i", "do you"]):
            return "inquiry"
            
        # 4. Fallback to base
        return base_sentiment.lower()

if __name__ == "__main__":
    # Test
    engine = SentimentEngine()
    test_comments = [
        {"text": "This video is amazing, I loved it!"},
        {"text": "I tried this strategy and gained 100 subs!"},
        {"text": "I'm confused about step 3, it didn't work."},
        {"text": "This is terrible advice."},
        {"text": "How do I download the checklist?"}
    ]
    results = engine.analyze_batch(test_comments)
    for r in results:
        print(f"Text: {r['text'][:30]}... -> {r['sentiment']} ({r['category']})")
