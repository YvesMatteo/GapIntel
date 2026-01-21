
import sys
import os

# Ensure we're in the right directory
current_dir = os.getcwd()
if not current_dir.endswith('AiRAG'):
    print(f"Warning: running from {current_dir}, expected to be in AiRAG root.")

# Add railway-api to path so we can simulate how the app runs
railway_api_path = os.path.join(current_dir, 'railway-api')
sys.path.append(railway_api_path)

def test_integration():
    print("Test: Scientific Integration Check")
    print("==================================")

    # 1. Test Inference Engine Loading
    print("\n1. Testing Inference Engine Import...")
    try:
        from premium.ml_models.inference_engine import ScientificInference
        inference = ScientificInference()
        print("   ✅ ScientificInference imported and initialized")
    except ImportError as e:
        print(f"   ❌ Export Failed: {e}")
        return

    # 2. Test Viral Predictor (Modified to use Inference)
    print("\n2. Testing Viral Predictor...")
    try:
        from premium.ml_models.viral_predictor import ViralPredictor
        predictor = ViralPredictor()
        print("   ✅ ViralPredictor initialized")
        
        # Test Prediction
        print("   🧪 Running Test Prediction...")
        
        # Provide clean inputs
        pred = predictor.predict(
            title="Minecraft but the World is LAVA",
            hook_text="You won't believe what happened when I touched the ground!",
            topic="Gaming",
            channel_history=[{'view_count': 5000}, {'view_count': 5500}, {'view_count': 4500}] # Median ~5000
        )
        
        print("\n   [Result]")
        print(f"   Predicted Views: {pred.predicted_views}")
        print(f"   Viral Probability: {pred.viral_probability}")
        print(f"   Factors: {pred.factors}")
        print(f"   Tips: {pred.tips}")
        print(f"   Is Heuristic: {pred.is_heuristic}")
        
        # Validation
        if not pred.is_heuristic and 'ml_uplift' in pred.factors:
             print("   ✅ SUCCESS: Scientific Model Used!")
        else:
             print("   ⚠️ WARNING: Heuristic Fallback Used (Check if models are trained/found)")

    except ImportError as e:
        print(f"   ❌ Import Failed: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"   ❌ Runtime Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_integration()
