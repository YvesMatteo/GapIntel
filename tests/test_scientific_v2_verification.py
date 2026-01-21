
import os
import sys
import json
import numpy as np
import shutil

# Path setup
import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Add railway-api to path to allow imports
railway_api = os.path.join(root_dir, 'railway-api')
if railway_api not in sys.path:
    sys.path.append(railway_api)

from premium.ml_models.scientific_trainer import NicheTrainer
from premium.ml_models.inference_engine import ScientificInference
    
def generate_mock_data():
    print("1. Generating Mock Data (V2)...")
    data = []
    for i in range(50): # Need enough for training
        vec = np.random.rand(1536).tolist()
        thumb = {
            'avg_brightness': float(np.random.rand()), 
            'contrast_score': float(np.random.rand()),
            'has_text': True,
            'face_count': 1
        }
        entry = {
            'video_id': f'vid_{i}',
            'niche': 'Test_V2_Niche',
            'title': f'Test Video {i}',
            'view_count': int(1000 + np.random.rand() * 10000),
            'like_count': 100,
            'duration_seconds': 600,
            'tags': ['test', 'mock'],
            'channel_id': 'ch_1',
            # V2 Features
            'title_embedding': vec,
            'thumbnail_features': thumb
        }
        data.append(entry)
        
    os.makedirs("tests/data_mock", exist_ok=True)
    with open("tests/data_mock/mock_v2.json", "w") as f:
        json.dump(data, f)
    print("   Saved tests/data_mock/mock_v2.json")

def train_mock_model():
    print("\n2. Training Mock Model...")
    trainer = NicheTrainer()
    data_dir = "tests/data_mock"
    save_dir = "tests/models_mock"
    
    # Train
    results = trainer.train_all_niches(data_dir)
    trainer.save_models(save_dir)
    
    print("\n   Training Results:", results.keys())
    return save_dir

def verify_inference(model_dir):
    print("\n3. Verifying Inference...")
    engine = ScientificInference(models_dir=model_dir)
    
    # Check if model loaded
    model = engine.get_model("Test_V2_Niche")
    if not model:
        print("   ❌ Model not found in inference engine.")
        return
        
    print(f"   Model Features: {model['features']}")
    
    # Test Prediction
    meta = {
        'title': "New Test Video",
        'duration_seconds': 600,
        'tags': ['a', 'b']
    }
    stats = {'view_average': 2000, 'subscriber_count': 10000}
    
    # We need to mock Embedder if we don't want to call OpenAI during test
    # OR we just let it call if credentials exist.
    # We will patch it to return random vector to save cost/time
    class MockEmbedder:
        def embed(self, text):
            return np.random.rand(1536)
            
    engine.embedder = MockEmbedder()
    print("   (Mocked Embedder for inference test)")
    
    prediction = engine.predict_expected_views(
        niche="Test_V2_Niche",
        video_metadata=meta,
        channel_stats=stats,
        thumbnail_features={'avg_brightness': 0.8}
    )
    
    print("   Prediction:", prediction)
    if prediction.get('is_scientific'):
        print("   ✅ SUCCESS: V2 Pipeline Verified!")
    else:
        print("   ❌ FAILURE: Prediction was not scientific.")

if __name__ == "__main__":
    generate_mock_data()
    model_dir = train_mock_model()
    verify_inference(model_dir)
    
    # Cleanup
    # shutil.rmtree("tests/data_mock")
    # shutil.rmtree("tests/models_mock")
