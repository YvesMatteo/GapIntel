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
        if TRANSFORMERS_AVAILABLE:
            try:
                # Load a lightweight, fast sentiment model
                self.pipeline = pipeline(
                    "sentiment-analysis", 
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1 # CPU by default, change to 0 for GPU if available
                )
                logger.info("✅ DistilBERT Sentiment Model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to load DistilBERT: {e}")
                self.pipeline = None
        else:
            logger.warning("⚠️ Transformers library not found. Falling back to pure heuristics.")

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

    def _classify_category(self, text: str, base_sentiment: str) -> str:
        """Classify comment into GapIntel specific categories."""
        text_lower = text.lower()
        
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
