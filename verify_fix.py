import sys
import os

# Ensure we can import modules
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'railway-api'))

from premium.ml_models.optimization_scorer import OptimizationScorer

def test_virtual_scoring():
    print("🧪 Testing Virtual Thumbnail Scoring & Niche Rules...")
    
    scorer = OptimizationScorer()
    
    # CASE 1: Blind Scoring (Old functionality)
    print("\n[1] Testing Blind Scoring (No thumbnail)...")
    res1 = scorer.evaluate(title="My Viral Video", thumbnail_features=None, thumbnail_description=None)
    print(f"    Score: {res1.total_score} (Should be low/neutral, e.g. based on title only)")
    
    # CASE 2: Virtual Scoring (New functionality)
    print("\n[2] Testing Virtual Scoring (With Description)...")
    concept = "Close up of shocked face holding a stack of cash. Bright yellow background. High contrast. Text says: 'STOP NOW'"
    res2 = scorer.evaluate(title="My Viral Video", thumbnail_features=None, thumbnail_description=concept)
    print(f"    Score: {res2.total_score}")
    print(f"    Pros: {res2.positive_factors}")
    
    if res2.total_score > res1.total_score:
        print("    ✅ PASS: Virtual scoring improved the score (Blindness Fixed!)")
    else:
        print("    ❌ FAIL: Virtual scoring didn't affect score.")

    # CASE 3: Niche Sensitivity
    print("\n[3] Testing Niche Sensitivity (Business)...")
    # 'Proven' is a Business power word (from user's guide)
    title_business = "The Proven Way to Make Money"
    
    # Score as General
    res_gen = scorer.evaluate(title=title_business, niche="General")
    # Score as Business
    res_biz = scorer.evaluate(title=title_business, niche="Business")
    
    print(f"    General Score: {res_gen.title_score}")
    print(f"    Business Score: {res_biz.title_score}")
    
    if res_biz.title_score > res_gen.title_score:
        print("    ✅ PASS: Niche scoring boosted score for niche-specific keywords!")
        print(f"    Biz Pros: {res_biz.positive_factors}")
    else:
        print("    ❌ FAIL: Niche rules didn't apply.")

if __name__ == "__main__":
    test_virtual_scoring()
