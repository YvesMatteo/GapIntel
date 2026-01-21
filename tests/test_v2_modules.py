
import sys
import os

# Path setup
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
    
# Add railway-api to path
railway_api = os.path.join(root_dir, 'railway-api')
if railway_api not in sys.path:
    sys.path.append(railway_api)

def test_embedder():
    print("\n1. Testing TextEmbedder...")
    try:
        from premium.ml_models.text_embedder import TextEmbedder
        embedder = TextEmbedder()
        print("   Initialized.")
        vec = embedder.embed("Test Title")
        print(f"   Embed Success. Shape: {vec.shape}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

def test_extractor():
    print("\n2. Testing ThumbnailExtractor...")
    try:
        from premium.thumbnail_extractor import ThumbnailFeatureExtractor
        extractor = ThumbnailFeatureExtractor()
        print("   Initialized.")
        # Dry run with mock image? or just init check
        # We won't download an actual image to avoid network issues interfering
        print("   Init Success.")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

if __name__ == "__main__":
    print("Testing Modules sequentially...")
    test_embedder()
    test_extractor()
    print("\nDone.")
