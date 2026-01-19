"""
Synthetic CTR Training Data Generator

Generates realistic CTR training data based on YouTube best practices and research.
This allows training the ML model before real customer data is available.

The synthetic data is based on:
- YouTube Creator Academy guidelines
- Industry CTR benchmarks (2-10% for most videos)
- Known thumbnail effectiveness patterns (faces, text, colors, etc.)
- Title effectiveness patterns (numbers, questions, power words, etc.)

Once real data from connected creators is available, the model will be
fine-tuned with actual CTR values, gradually replacing synthetic patterns.
"""

import random
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta

# Try to import Supabase client
try:
    import requests
except ImportError:
    requests = None


@dataclass
class SyntheticVideo:
    """A synthetically generated video with features and CTR."""
    video_id: str
    channel_id: str
    title: str
    thumbnail_features: Dict
    title_features: Dict
    ctr: float  # 0-100 percentage
    impressions: int
    clicks: int


class SyntheticCTRGenerator:
    """
    Generates synthetic CTR training data based on YouTube best practices.
    
    CTR Factors (based on research):
    - Faces with eye contact: +1.5-2.5% CTR
    - Large faces (close-up): +1-2% CTR
    - Text overlay (readable): +0.5-1.5% CTR
    - High contrast/saturation: +0.5-1% CTR
    - Red/yellow accents: +0.3-0.8% CTR
    - Rule of thirds composition: +0.5-1% CTR
    - Numbers in title: +0.5-1% CTR
    - Question in title: +0.3-0.8% CTR
    - Power words: +0.3-0.7% CTR
    - Optimal title length (40-60 chars): +0.3-0.5% CTR
    
    Base CTR range: 2-5% (average YouTube video)
    Top performers: 8-15%
    Poor performers: 1-2%
    """
    
    # Base CTR distribution parameters
    BASE_CTR_MEAN = 4.0
    BASE_CTR_STD = 2.0
    MIN_CTR = 0.5
    MAX_CTR = 20.0
    
    # Feature impact on CTR (additive percentages)
    FEATURE_IMPACTS = {
        # Thumbnail features
        'has_face': (1.0, 2.0),
        'face_is_large': (0.8, 1.5),
        'has_eye_contact': (0.5, 1.2),
        'face_has_emotion': (0.5, 1.0),
        'has_text': (0.3, 1.0),
        'text_is_readable': (0.3, 0.8),
        'has_contrast': (0.3, 0.8),
        'has_bright_colors': (0.2, 0.6),
        'has_red_accent': (0.2, 0.5),
        'has_yellow_accent': (0.2, 0.5),
        'rule_of_thirds': (0.3, 0.7),
        'mobile_optimized': (0.2, 0.5),
        
        # Title features  
        'has_number': (0.4, 0.9),
        'has_question': (0.2, 0.6),
        'has_power_word':    (0.3, 0.7),
        'optimal_length': (0.2, 0.4),
        'has_bracket': (0.2, 0.5),
        'has_emoji': (0.1, 0.4),
        'curiosity_gap': (0.5, 1.2),
    }
    
    # Negative impacts
    NEGATIVE_IMPACTS = {
        'too_much_text': (-0.5, -1.5),
        'cluttered': (-0.8, -2.0),
        'low_contrast': (-0.3, -0.8),
        'no_face': (-0.5, -1.0),
        'title_too_long': (-0.2, -0.5),
        'title_too_short': (-0.2, -0.4),
        'clickbait_penalty': (-0.5, -1.5),
    }
    
    # Power words that increase CTR
    POWER_WORDS = [
        'secret', 'revealed', 'shocking', 'amazing', 'incredible',
        'ultimate', 'best', 'worst', 'never', 'always', 'every',
        'free', 'new', 'proven', 'guaranteed', 'simple', 'easy',
        'fast', 'quick', 'instant', 'exclusive', 'limited', 'urgent',
        'breaking', 'finally', 'discover', 'truth', 'real', 'honest',
        'crazy', 'insane', 'mind-blowing', 'life-changing', 'game-changer'
    ]
    
    # Video categories with CTR modifiers
    CATEGORY_MODIFIERS = {
        'Entertainment': 0.0,
        'Gaming': -0.3,
        'Education': 0.2,
        'Howto': 0.5,
        'Music': -0.5,
        'News': 0.3,
        'Sports': 0.0,
        'Tech': 0.2,
        'Lifestyle': 0.1,
        'Comedy': 0.2,
    }
    
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
    def generate_thumbnail_features(self) -> Tuple[Dict, float]:
        """Generate random thumbnail features and calculate CTR impact."""
        features = {}
        ctr_impact = 0.0
        
        # Face presence (70% of good thumbnails have faces)
        features['has_face'] = random.random() < 0.7
        if features['has_face']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_face'])
            
            # Face size
            features['face_is_large'] = random.random() < 0.6
            if features['face_is_large']:
                ctr_impact += random.uniform(*self.FEATURE_IMPACTS['face_is_large'])
            
            # Eye contact
            features['has_eye_contact'] = random.random() < 0.5
            if features['has_eye_contact']:
                ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_eye_contact'])
            
            # Emotion
            features['face_has_emotion'] = random.random() < 0.6
            if features['face_has_emotion']:
                ctr_impact += random.uniform(*self.FEATURE_IMPACTS['face_has_emotion'])
            
            features['face_count'] = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
        else:
            features['face_count'] = 0
            ctr_impact += random.uniform(*self.NEGATIVE_IMPACTS['no_face'])
        
        # Text overlay
        features['has_text'] = random.random() < 0.65
        if features['has_text']:
            features['word_count'] = random.randint(1, 5)
            if features['word_count'] <= 4:
                features['text_is_readable'] = True
                ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_text'])
                ctr_impact += random.uniform(*self.FEATURE_IMPACTS['text_is_readable'])
            else:
                features['text_is_readable'] = False
                ctr_impact += random.uniform(*self.NEGATIVE_IMPACTS['too_much_text'])
        else:
            features['word_count'] = 0
            features['text_is_readable'] = False
        
        # Colors and contrast
        features['avg_saturation'] = random.uniform(0.3, 0.9)
        features['avg_brightness'] = random.uniform(0.3, 0.8)
        features['contrast_score'] = random.uniform(0.2, 0.9)
        
        features['has_contrast'] = features['contrast_score'] > 0.5
        if features['has_contrast']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_contrast'])
        else:
            ctr_impact += random.uniform(*self.NEGATIVE_IMPACTS['low_contrast'])
        
        features['has_bright_colors'] = features['avg_saturation'] > 0.6
        if features['has_bright_colors']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_bright_colors'])
        
        # Accent colors
        features['has_red_accent'] = random.random() < 0.3
        if features['has_red_accent']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_red_accent'])
        
        features['has_yellow_accent'] = random.random() < 0.2
        if features['has_yellow_accent']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_yellow_accent'])
        
        # Composition
        features['rule_of_thirds_score'] = random.uniform(0.2, 0.95)
        features['rule_of_thirds'] = features['rule_of_thirds_score'] > 0.6
        if features['rule_of_thirds']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['rule_of_thirds'])
        
        # Mobile optimization
        features['mobile_readability_score'] = random.uniform(0.3, 1.0)
        features['mobile_optimized'] = features['mobile_readability_score'] > 0.7
        if features['mobile_optimized']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['mobile_optimized'])
        
        # Clutter assessment
        elements = int(features['has_face']) + int(features['has_text']) + int(features['has_red_accent'])
        features['is_cluttered'] = elements > 3 or features.get('word_count', 0) > 4
        if features['is_cluttered']:
            ctr_impact += random.uniform(*self.NEGATIVE_IMPACTS['cluttered'])
        
        return features, ctr_impact
    
    def generate_title_features(self, title: str) -> Tuple[Dict, float]:
        """Analyze title and calculate CTR impact."""
        features = {}
        ctr_impact = 0.0
        
        features['title_length'] = len(title)
        features['word_count'] = len(title.split())
        
        # Optimal length (40-60 characters)
        features['optimal_length'] = 40 <= len(title) <= 60
        if features['optimal_length']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['optimal_length'])
        elif len(title) > 70:
            features['title_too_long'] = True
            ctr_impact += random.uniform(*self.NEGATIVE_IMPACTS['title_too_long'])
        elif len(title) < 25:
            features['title_too_short'] = True
            ctr_impact += random.uniform(*self.NEGATIVE_IMPACTS['title_too_short'])
        
        # Numbers
        features['has_number'] = any(char.isdigit() for char in title)
        if features['has_number']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_number'])
        
        # Question
        features['has_question'] = '?' in title
        if features['has_question']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_question'])
        
        # Power words
        title_lower = title.lower()
        features['has_power_word'] = any(word in title_lower for word in self.POWER_WORDS)
        if features['has_power_word']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_power_word'])
        
        # Brackets [NEW] (SHOCKING)
        features['has_bracket'] = '[' in title or '(' in title
        if features['has_bracket']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_bracket'])
        
        # Emoji (can be good or bad)
        features['has_emoji'] = any(ord(char) > 127 for char in title)
        if features['has_emoji']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['has_emoji'])
        
        # Curiosity gap patterns
        curiosity_patterns = ['...', 'what happens', 'you won\'t believe', 'the truth about', 
                           'secret', 'revealed', 'finally', 'i tried', 'i tested']
        features['has_curiosity_gap'] = any(pattern in title_lower for pattern in curiosity_patterns)
        if features['has_curiosity_gap']:
            ctr_impact += random.uniform(*self.FEATURE_IMPACTS['curiosity_gap'])
        
        # Capitalization ratio
        if len(title) > 0:
            features['caps_ratio'] = sum(1 for c in title if c.isupper()) / len(title)
        else:
            features['caps_ratio'] = 0
        
        # ALL CAPS is usually bad
        if features['caps_ratio'] > 0.5:
            ctr_impact -= 0.3
        
        return features, ctr_impact
    
    def generate_title(self) -> str:
        """Generate a realistic YouTube title."""
        templates = [
            "I Tried {thing} for {number} Days...",
            "The {adjective} Way to {action} in {year}",
            "{number} {thing} That Will {action}",
            "How I {action} in Just {number} {time}",
            "Why {thing} is {adjective} (The Truth)",
            "{thing} vs {thing2}: Which is Better?",
            "I Tested {number} {thing} - Here's What Happened",
            "The Secret to {action} Nobody Tells You",
            "[{tag}] {adjective} {thing} {action}",
            "{question}? Here's the Answer",
            "Stop Doing THIS with Your {thing}!",
            "What Happens When You {action}...",
            "{number} Mistakes You're Making with {thing}",
            "Is {thing} Worth It? Honest Review",
            "How to {action} Like a Pro",
        ]
        
        things = ['YouTube', 'TikTok', 'Instagram', 'coding', 'gaming', 'fitness', 
                  'productivity', 'investing', 'cooking', 'photography', 'AI', 'ChatGPT']
        adjectives = ['BEST', 'Ultimate', 'Secret', 'Shocking', 'Amazing', 'Simple', 
                     'Easy', 'Quick', 'Proven', 'Real']
        actions = ['grow your channel', 'make money', 'get views', 'go viral', 
                  'save time', 'be productive', 'learn faster', 'create content']
        tags = ['NEW', 'SHOCKING', '2024', 'UPDATED', 'REAL', 'HONEST']
        questions = ['Is this worth it', 'Should you do this', 'Does this actually work',
                    'Why is everyone doing this', 'What\'s the best strategy']
        
        template = random.choice(templates)
        title = template.format(
            thing=random.choice(things),
            thing2=random.choice(things),
            adjective=random.choice(adjectives),
            action=random.choice(actions),
            number=random.choice([3, 5, 7, 10, 30, 100]),
            year=2024,
            time=random.choice(['Days', 'Weeks', 'Hours']),
            tag=random.choice(tags),
            question=random.choice(questions)
        )
        
        return title
    
    def generate_video(self, channel_id: Optional[str] = None) -> SyntheticVideo:
        """Generate a single synthetic video with realistic CTR."""
        
        # Generate unique IDs
        video_id = f"synthetic_{random.randint(100000, 999999)}"
        if not channel_id:
            channel_id = f"UC_synthetic_{random.randint(1000, 9999)}"
        
        # Generate title
        title = self.generate_title()
        
        # Generate features and calculate impacts
        thumbnail_features, thumb_impact = self.generate_thumbnail_features()
        title_features, title_impact = self.generate_title_features(title)
        
        # Calculate base CTR with some randomness
        base_ctr = np.random.normal(self.BASE_CTR_MEAN, self.BASE_CTR_STD)
        
        # Add category modifier
        category = random.choice(list(self.CATEGORY_MODIFIERS.keys()))
        category_mod = self.CATEGORY_MODIFIERS[category]
        
        # Calculate final CTR
        final_ctr = base_ctr + thumb_impact + title_impact + category_mod
        
        # Add some noise
        noise = np.random.normal(0, 0.5)
        final_ctr += noise
        
        # Clamp to realistic range
        final_ctr = max(self.MIN_CTR, min(self.MAX_CTR, final_ctr))
        
        # Generate impressions (varies widely)
        impressions = int(np.random.lognormal(10, 2))  # Log-normal for realistic distribution
        impressions = max(1000, min(10000000, impressions))
        
        # Calculate clicks from CTR
        clicks = int(impressions * (final_ctr / 100))
        
        return SyntheticVideo(
            video_id=video_id,
            channel_id=channel_id,
            title=title,
            thumbnail_features=thumbnail_features,
            title_features=title_features,
            ctr=round(final_ctr, 2),
            impressions=impressions,
            clicks=clicks
        )
    
    def generate_dataset(self, num_videos: int = 1000, num_channels: int = 50) -> List[SyntheticVideo]:
        """Generate a dataset of synthetic videos."""
        videos = []
        
        # Generate channel IDs
        channel_ids = [f"UC_synthetic_{i:04d}" for i in range(num_channels)]
        
        for i in range(num_videos):
            channel_id = random.choice(channel_ids)
            video = self.generate_video(channel_id)
            videos.append(video)
            
            if (i + 1) % 100 == 0:
                print(f"📊 Generated {i + 1}/{num_videos} synthetic videos...")
        
        return videos
    
    def save_to_supabase(self, videos: List[SyntheticVideo]) -> Dict:
        """Save synthetic videos to the ctr_training_data table using batch inserts."""
        if not self.supabase_url or not self.supabase_key:
            return {"error": "Supabase credentials not configured"}
        
        if not requests:
            return {"error": "requests library not available"}
        
        inserted = 0
        errors = []
        batch_size = 100
        
        # Prepare all data first
        all_data = []
        for video in videos:
            data = {
                "video_id": video.video_id,
                "channel_id": video.channel_id,
                "impressions": video.impressions,
                "clicks": video.clicks,
                "ctr_actual": video.ctr,
                "thumbnail_features": video.thumbnail_features,
                "thumbnail_url": None,
                "title": video.title,
                "title_length": video.title_features.get('title_length', 0),
                "title_has_numbers": video.title_features.get('has_number', False),
                "title_has_question": video.title_features.get('has_question', False),
                "title_has_power_words": video.title_features.get('has_power_word', False),
                "title_capitalization_ratio": video.title_features.get('caps_ratio', 0),
                "data_source": "synthetic"
            }
            all_data.append(data)
        
        # Insert in batches
        for i in range(0, len(all_data), batch_size):
            batch = all_data[i:i + batch_size]
            
            try:
                response = requests.post(
                    f"{self.supabase_url}/rest/v1/ctr_training_data",
                    json=batch,
                    headers={
                        "apikey": self.supabase_key,
                        "Authorization": f"Bearer {self.supabase_key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal"
                    },
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    inserted += len(batch)
                    print(f"   ✓ Inserted batch {i//batch_size + 1} ({inserted}/{len(all_data)})")
                else:
                    errors.append(f"Batch {i//batch_size + 1}: {response.text[:200]}")
                    print(f"   ✗ Batch {i//batch_size + 1} failed: {response.status_code}")
            except Exception as e:
                errors.append(f"Batch {i//batch_size + 1}: {str(e)}")
                print(f"   ✗ Batch {i//batch_size + 1} error: {str(e)[:50]}")
        
        return {
            "inserted": inserted,
            "total": len(videos),
            "errors": errors[:10]  # Limit errors in response
        }
    
    def generate_and_save(self, num_videos: int = 1000) -> Dict:
        """Generate synthetic data and save to database."""
        print(f"🎲 Generating {num_videos} synthetic CTR training videos...")
        
        videos = self.generate_dataset(num_videos)
        
        print(f"💾 Saving to Supabase...")
        result = self.save_to_supabase(videos)
        
        # Calculate stats
        ctrs = [v.ctr for v in videos]
        stats = {
            "generated": len(videos),
            "saved": result.get("inserted", 0),
            "avg_ctr": round(np.mean(ctrs), 2),
            "min_ctr": round(min(ctrs), 2),
            "max_ctr": round(max(ctrs), 2),
            "std_ctr": round(np.std(ctrs), 2)
        }
        
        print(f"✅ Generated {stats['generated']} videos")
        print(f"   Saved: {stats['saved']}")
        print(f"   CTR Range: {stats['min_ctr']}% - {stats['max_ctr']}%")
        print(f"   Avg CTR: {stats['avg_ctr']}% (std: {stats['std_ctr']}%)")
        
        return {**stats, **result}


# CLI interface
if __name__ == "__main__":
    import sys
    
    num_videos = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    
    generator = SyntheticCTRGenerator()
    result = generator.generate_and_save(num_videos)
    
    print(f"\n📊 Final Result:")
    print(json.dumps(result, indent=2))
