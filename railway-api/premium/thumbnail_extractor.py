"""
Premium Analysis - Thumbnail Feature Extractor
Extracts 50+ features from YouTube thumbnails for ML training.

Uses:
- OpenCV for basic image processing
- EasyOCR for text extraction
- mediapipe for face detection
- Color analysis with K-means clustering
"""

import cv2
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from typing import Dict, List, Tuple, Optional
import colorsys
from dataclasses import dataclass, asdict
from sklearn.cluster import KMeans
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Lazy imports for optional dependencies
_easyocr_reader = None
_face_detection = None


def get_ocr_reader():
    """Lazy load EasyOCR reader."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        except ImportError:
            print("⚠️ EasyOCR not installed. Text detection disabled.")
            return None
    return _easyocr_reader


def get_face_detector():
    """Lazy load mediapipe face detector."""
    global _face_detection
    if _face_detection is None:
        try:
            import mediapipe as mp
            # Check if solutions attribute exists (version compatibility)
            if hasattr(mp, 'solutions') and hasattr(mp.solutions, 'face_detection'):
                _face_detection = mp.solutions.face_detection.FaceDetection(
                    model_selection=1, min_detection_confidence=0.5
                )
            else:
                print("⚠️ mediapipe version incompatible. Face detection disabled.")
                return None
        except Exception as e:
            print(f"⚠️ mediapipe init failed: {e}. Face detection disabled.")
            return None
    return _face_detection


@dataclass
class ThumbnailFeatures:
    """50+ features extracted from a thumbnail."""
    
    # === Color Features (10) ===
    dominant_color_1: Tuple[int, int, int] = (0, 0, 0)
    dominant_color_2: Tuple[int, int, int] = (0, 0, 0)
    dominant_color_3: Tuple[int, int, int] = (0, 0, 0)
    avg_saturation: float = 0.0
    avg_brightness: float = 0.0
    contrast_score: float = 0.0
    color_diversity: float = 0.0
    warm_color_ratio: float = 0.0
    has_red_accent: bool = False
    background_brightness: float = 0.0
    
    # === Face Features (10) ===
    face_count: int = 0
    face_area_ratio: float = 0.0
    primary_face_x: float = 0.5  # normalized position
    primary_face_y: float = 0.5
    primary_face_size: float = 0.0
    has_eye_contact: bool = False
    face_in_left_third: bool = False
    face_in_right_third: bool = False
    face_in_center: bool = False
    faces_are_large: bool = False
    
    # === Text Features (10) ===
    has_text: bool = False
    word_count: int = 0
    text_area_ratio: float = 0.0
    extracted_text: str = ""
    text_contrast_score: float = 0.0
    uses_numbers: bool = False
    uses_all_caps: bool = False
    text_length: int = 0
    has_question: bool = False
    has_exclamation: bool = False
    
    # === Composition Features (10) ===
    edge_density: float = 0.0
    center_focus_score: float = 0.0
    rule_of_thirds_score: float = 0.0
    symmetry_score: float = 0.0
    visual_complexity: float = 0.0
    negative_space_ratio: float = 0.0
    has_border: bool = False
    aspect_ratio: float = 1.77  # 16:9 standard
    image_quality_score: float = 0.0
    blur_score: float = 0.0
    
    # === Advanced Features (10) ===
    has_arrows_or_circles: bool = False
    has_emoji: bool = False
    has_before_after: bool = False
    has_split_layout: bool = False
    has_gradient: bool = False
    primary_hue: int = 0
    color_temperature: str = "neutral"  # warm/neutral/cool
    estimated_style: str = "unknown"  # vlog/tutorial/reaction/news
    overall_vibrancy: float = 0.0
    mobile_readability_score: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, tuple):
                # Convert numpy types in tuples to native Python
                result[key] = [int(v) if hasattr(v, 'item') else v for v in value]
            elif hasattr(value, 'item'):
                # Convert numpy scalars to Python natives
                result[key] = value.item()
            else:
                result[key] = value
        return result
    
    def to_feature_vector(self) -> List[float]:
        """Convert to numeric feature vector for ML models."""
        vector = []
        for key, value in asdict(self).items():
            if isinstance(value, bool):
                vector.append(float(value))
            elif isinstance(value, (int, float)):
                vector.append(float(value))
            elif isinstance(value, tuple):
                vector.extend([float(v) for v in value])
            elif isinstance(value, str):
                # Skip string features for vector
                continue
        return vector


class ThumbnailFeatureExtractor:
    """
    Extract comprehensive features from YouTube thumbnails.
    
    Usage:
        extractor = ThumbnailFeatureExtractor()
        features = extractor.extract_from_url(thumbnail_url)
        print(features.to_dict())
    """
    
    def __init__(self, use_ocr: bool = True, use_face_detection: bool = True):
        self.use_ocr = use_ocr
        self.use_face_detection = use_face_detection
    
    def extract_from_url(self, url: str) -> ThumbnailFeatures:
        """Download thumbnail and extract features."""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert('RGB')
            return self.extract_from_image(img)
        except Exception as e:
            print(f"⚠️ Failed to download thumbnail: {e}")
            return ThumbnailFeatures()
    
    def extract_from_path(self, path: str) -> ThumbnailFeatures:
        """Load thumbnail from file and extract features."""
        try:
            img = Image.open(path).convert('RGB')
            return self.extract_from_image(img)
        except Exception as e:
            print(f"⚠️ Failed to load thumbnail: {e}")
            return ThumbnailFeatures()
    
    def extract_from_image(self, img: Image.Image) -> ThumbnailFeatures:
        """Extract all features from a PIL Image."""
        features = ThumbnailFeatures()
        
        # Convert to numpy for OpenCV
        img_np = np.array(img)
        img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
        img_hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
        img_gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        
        h, w = img_np.shape[:2]
        features.aspect_ratio = w / h
        
        # === Color Features ===
        self._extract_color_features(img_np, img_hsv, features)
        
        # === Face Features ===
        if self.use_face_detection:
            self._extract_face_features(img_np, features)
        
        # === Text Features ===
        if self.use_ocr:
            self._extract_text_features(img_np, features)
        
        # === Composition Features ===
        self._extract_composition_features(img_gray, img_np, features)
        
        # === Advanced Features ===
        self._extract_advanced_features(img_np, img_hsv, features)
        
        return features
    
    def _extract_color_features(self, img_rgb: np.ndarray, img_hsv: np.ndarray, 
                                 features: ThumbnailFeatures):
        """Extract color-related features."""
        h, w = img_rgb.shape[:2]
        
        # Reshape for clustering
        pixels = img_rgb.reshape(-1, 3).astype(float)
        
        # K-means for dominant colors
        try:
            kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
            kmeans.fit(pixels)
            centers = kmeans.cluster_centers_.astype(int)
            
            # Sort by cluster size
            labels, counts = np.unique(kmeans.labels_, return_counts=True)
            sorted_indices = np.argsort(-counts)
            
            features.dominant_color_1 = tuple(centers[sorted_indices[0]])
            features.dominant_color_2 = tuple(centers[sorted_indices[1]])
            features.dominant_color_3 = tuple(centers[sorted_indices[2]])
        except:
            pass
        
        # Get 2D arrays for spatial operations BEFORE flattening
        hue_2d = img_hsv[:, :, 0]
        sat_2d = img_hsv[:, :, 1] / 255.0
        val_2d = img_hsv[:, :, 2] / 255.0
        
        # Background brightness (edges of image) - use 2D array
        border_rows = min(10, h // 4)
        border_cols = min(10, w // 4)
        border = np.concatenate([
            val_2d[:border_rows, :].flatten(),
            val_2d[-border_rows:, :].flatten(),
            val_2d[:, :border_cols].flatten(),
            val_2d[:, -border_cols:].flatten()
        ])
        features.background_brightness = float(np.mean(border))
        
        # Now flatten for statistics
        hue = hue_2d.flatten()
        sat = sat_2d.flatten()
        val = val_2d.flatten()
        
        features.avg_saturation = float(np.mean(sat))
        features.avg_brightness = float(np.mean(val))
        features.primary_hue = int(np.median(hue) * 2)  # Convert to 0-360
        
        # Contrast (std of brightness)
        features.contrast_score = float(np.std(val))
        
        # Color diversity (std of hue)
        features.color_diversity = float(np.std(hue) / 90.0)  # Normalize
        
        # Warm color ratio (red-yellow range: hue 0-60 or 300-360)
        warm_mask = ((hue < 30) | (hue > 150))  # OpenCV hue is 0-179
        features.warm_color_ratio = float(np.mean(warm_mask))
        
        # Red accent detection
        red_mask = (hue < 10) | (hue > 170)
        red_sat = sat[red_mask] if np.any(red_mask) else []
        features.has_red_accent = len(red_sat) > 0 and np.mean(red_sat) > 0.5
        
        # Color temperature
        avg_hue = np.mean(hue)
        if avg_hue < 30 or avg_hue > 150:
            features.color_temperature = "warm"
        elif 90 < avg_hue < 150:
            features.color_temperature = "cool"
        else:
            features.color_temperature = "neutral"
        
        # Overall vibrancy
        features.overall_vibrancy = float(features.avg_saturation * features.contrast_score)
    
    def _extract_face_features(self, img_rgb: np.ndarray, features: ThumbnailFeatures):
        """Extract face-related features using mediapipe."""
        detector = get_face_detector()
        if detector is None:
            return
        
        h, w = img_rgb.shape[:2]
        
        try:
            results = detector.process(img_rgb)
            
            if results.detections:
                features.face_count = len(results.detections)
                
                # Get largest face
                largest_face = None
                largest_area = 0
                
                for detection in results.detections:
                    bbox = detection.location_data.relative_bounding_box
                    area = bbox.width * bbox.height
                    if area > largest_area:
                        largest_area = area
                        largest_face = bbox
                
                if largest_face:
                    features.face_area_ratio = float(largest_area)
                    features.primary_face_x = float(largest_face.xmin + largest_face.width / 2)
                    features.primary_face_y = float(largest_face.ymin + largest_face.height / 2)
                    features.primary_face_size = float(max(largest_face.width, largest_face.height))
                    
                    # Position analysis
                    center_x = features.primary_face_x
                    features.face_in_left_third = center_x < 0.33
                    features.face_in_right_third = center_x > 0.66
                    features.face_in_center = 0.33 <= center_x <= 0.66
                    
                    # Large face detection (> 15% of image)
                    features.faces_are_large = largest_area > 0.15
                    
                    # Eye contact estimation (face looking forward)
                    # Simple heuristic: face is centered horizontally
                    features.has_eye_contact = abs(center_x - 0.5) < 0.15
        except Exception as e:
            print(f"⚠️ Face detection failed: {e}")
    
    def _extract_text_features(self, img_rgb: np.ndarray, features: ThumbnailFeatures):
        """Extract text-related features using EasyOCR."""
        reader = get_ocr_reader()
        if reader is None:
            return
        
        h, w = img_rgb.shape[:2]
        total_pixels = h * w
        
        try:
            results = reader.readtext(img_rgb)
            
            if results:
                features.has_text = True
                
                # Combine all text
                all_text = " ".join([r[1] for r in results])
                features.extracted_text = all_text[:200]  # Limit length
                features.text_length = len(all_text)
                features.word_count = len(all_text.split())
                
                # Calculate text area
                text_area = sum([
                    (r[0][2][0] - r[0][0][0]) * (r[0][2][1] - r[0][0][1])
                    for r in results
                ])
                features.text_area_ratio = float(text_area / total_pixels)
                
                # Text characteristics
                features.uses_numbers = any(c.isdigit() for c in all_text)
                features.uses_all_caps = all_text.isupper() and len(all_text) > 3
                features.has_question = '?' in all_text
                features.has_exclamation = '!' in all_text
                
                # Text contrast (simplified)
                features.text_contrast_score = min(1.0, features.text_area_ratio * 10)
        except Exception as e:
            print(f"⚠️ OCR failed: {e}")
    
    def _extract_composition_features(self, img_gray: np.ndarray, img_rgb: np.ndarray,
                                        features: ThumbnailFeatures):
        """Extract composition-related features."""
        h, w = img_gray.shape
        
        # Edge density (Canny edge detection)
        edges = cv2.Canny(img_gray, 100, 200)
        features.edge_density = float(np.mean(edges) / 255.0)
        
        # Center focus (brightness in center vs edges)
        center_region = img_gray[h//4:3*h//4, w//4:3*w//4]
        edge_regions = np.concatenate([
            img_gray[:h//4, :].flatten(),
            img_gray[3*h//4:, :].flatten()
        ])
        features.center_focus_score = float(
            np.mean(center_region) / max(np.mean(edge_regions), 1)
        )
        
        # Rule of thirds (look for features at intersection points)
        thirds_x = [w//3, 2*w//3]
        thirds_y = [h//3, 2*h//3]
        thirds_score = 0
        for x in thirds_x:
            for y in thirds_y:
                region = edges[max(0, y-20):min(h, y+20), max(0, x-20):min(w, x+20)]
                thirds_score += np.mean(region)
        features.rule_of_thirds_score = float(thirds_score / 4 / 255.0)
        
        # Symmetry (compare left and right halves)
        left = img_gray[:, :w//2]
        right = np.flip(img_gray[:, w//2:], axis=1)
        if left.shape == right.shape:
            features.symmetry_score = float(1 - np.mean(np.abs(left.astype(float) - right.astype(float))) / 255.0)
        
        # Visual complexity (entropy)
        hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
        hist = hist / hist.sum()
        hist = hist[hist > 0]
        features.visual_complexity = float(-np.sum(hist * np.log2(hist)) / 8.0)  # Normalize
        
        # Negative space (low-variance regions)
        blur = cv2.GaussianBlur(img_gray, (15, 15), 0)
        local_std = cv2.GaussianBlur((img_gray.astype(float) - blur.astype(float))**2, (15, 15), 0)**0.5
        features.negative_space_ratio = float(np.mean(local_std < 10))
        
        # Border detection
        border_pixels = np.concatenate([
            img_gray[0, :], img_gray[-1, :],
            img_gray[:, 0], img_gray[:, -1]
        ])
        features.has_border = float(np.std(border_pixels)) < 20
        
        # Image quality (Laplacian variance)
        laplacian = cv2.Laplacian(img_gray, cv2.CV_64F)
        features.image_quality_score = float(min(laplacian.var() / 1000, 1.0))
        
        # Blur score
        features.blur_score = float(1 - features.image_quality_score)
    
    def _extract_advanced_features(self, img_rgb: np.ndarray, img_hsv: np.ndarray,
                                     features: ThumbnailFeatures):
        """Extract advanced/semantic features."""
        h, w = img_rgb.shape[:2]
        
        # Arrow/circle detection using Hough circles
        gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                    param1=50, param2=30, minRadius=10, maxRadius=100)
        features.has_arrows_or_circles = circles is not None
        
        # Gradient detection (smooth color transitions)
        dx = np.abs(np.diff(img_hsv[:, :, 0].astype(float), axis=1))
        dy = np.abs(np.diff(img_hsv[:, :, 0].astype(float), axis=0))
        smooth_regions = (np.mean(dx) < 5) and (np.mean(dy) < 5)
        features.has_gradient = bool(features.color_diversity < 0.3 and smooth_regions)
        
        # Split layout detection (vertical line in center)
        center_col = gray[:, w//2-5:w//2+5]
        features.has_split_layout = float(np.std(center_col)) < 30
        
        # Before/after detection (two distinct halves)
        left_half = img_hsv[:, :w//2, :]
        right_half = img_hsv[:, w//2:, :]
        half_diff = np.mean(np.abs(
            np.mean(left_half, axis=(0, 1)) - np.mean(right_half, axis=(0, 1))
        ))
        features.has_before_after = half_diff > 20
        
        # Mobile readability (text is large enough)
        features.mobile_readability_score = float(
            (features.text_area_ratio / 0.1 if features.has_text else 0.5) +
            (0.5 if features.faces_are_large else 0)
        )
        features.mobile_readability_score = min(1.0, features.mobile_readability_score)
        
        # Style estimation based on features
        if features.face_count > 0 and features.faces_are_large:
            if features.has_text and features.word_count <= 3:
                features.estimated_style = "vlog"
            else:
                features.estimated_style = "reaction"
        elif features.has_text and features.word_count > 5:
            features.estimated_style = "tutorial"
        elif features.has_arrows_or_circles:
            features.estimated_style = "educational"
        else:
            features.estimated_style = "general"


# === Quick test ===
if __name__ == "__main__":
    extractor = ThumbnailFeatureExtractor(use_ocr=False, use_face_detection=False)
    
    # Test with a sample thumbnail
    test_url = "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
    print("🔍 Testing thumbnail feature extraction...")
    features = extractor.extract_from_url(test_url)
    
    print(f"\n📊 Extracted Features:")
    print(f"  Dominant Color 1: {features.dominant_color_1}")
    print(f"  Avg Saturation: {features.avg_saturation:.2f}")
    print(f"  Avg Brightness: {features.avg_brightness:.2f}")
    print(f"  Contrast Score: {features.contrast_score:.2f}")
    print(f"  Edge Density: {features.edge_density:.2f}")
    print(f"  Visual Complexity: {features.visual_complexity:.2f}")
    print(f"  Color Temperature: {features.color_temperature}")
    print(f"\n  Feature Vector Length: {len(features.to_feature_vector())}")
