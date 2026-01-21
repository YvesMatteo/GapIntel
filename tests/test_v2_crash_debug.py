
import os
import sys

# Path setup
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)
railway_api = os.path.join(root_dir, 'railway-api')
if railway_api not in sys.path:
    sys.path.append(railway_api)

from premium.thumbnail_extractor import ThumbnailFeatureExtractor

TEST_URL = "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"

def test_ocr():
    print("\n--- Testing OCR Only ---")
    try:
        ext = ThumbnailFeatureExtractor(use_ocr=True, use_face_detection=False)
        print("Initialized OCR.")
        feat = ext.extract_from_url(TEST_URL)
        print("Extracted OCR features.", feat.has_text)
    except Exception as e:
        print(f"OCR Failed: {e}")

def test_face():
    print("\n--- Testing Face Only ---")
    try:
        ext = ThumbnailFeatureExtractor(use_ocr=False, use_face_detection=True)
        print("Initialized Face.")
        feat = ext.extract_from_url(TEST_URL)
        print("Extracted Face features.", feat.face_count)
    except Exception as e:
        print(f"Face Failed: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True)
    args = parser.parse_args()
    
    if args.mode == "ocr":
        test_ocr()
    elif args.mode == "face":
        test_face()
