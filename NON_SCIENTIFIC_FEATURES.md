# Non-Scientific Features Audit

The following features use hard-coded heuristics, "magic numbers", or subjective rule-based logic instead of data-driven machine learning models. These must be replaced to achieve scientific validity.

## 1. Viral Opportunity Scoring (`scoring_engine.py`)
- **Issue**: The core `calculate_viral_score` function uses arbitrary weights.
- **Code Location**: `scoring_engine.py` lines 57-62.
- **Current Logic**:
    ```python
    WEIGHTS = {
        "comment_frequency": 0.2,
        "visual_outlier": 0.2,
        "trend_momentum": 0.3,
        "saturation_inverse": 0.3
    }
    ```
- **Scientific Impact**: Weights assume universal importance of factors across all niches, which is scientifically invalid (e.g., "visuals" might matter more in Art than in Finance).

## 2. Views Prediction Fallback (`railway-api/premium/ml_models/views_predictor.py`)
- **Issue**: The `_rule_based_prediction` method uses hardcoded multipliers to guess 7-day and 30-day views.
- **Code Location**: `ViewsVelocityPredictor.DEFAULT_TRAJECTORY_PATTERNS`.
- **Current Logic**:
    ```python
    'viral': {'7d_mult': 50, '30d_mult': 100},
    'steady_growth': {'7d_mult': 7, '30d_mult': 15}
    ```
- **Scientific Impact**: These multipliers are static and do not account for channel size, current velocity, or niche norms.

## 3. CTR Prediction Fallback (`railway-api/premium/ml_models/ctr_predictor.py`)
- **Issue**: The `_rule_based_prediction` adds arbitrary percentage points for feature presence.
- **Code Location**: `CTRPredictor._rule_based_prediction`.
- **Current Logic**:
    - `Large face visible`: +1.5% CTR
    - `Power words`: +0.6% CTR
    - `Red accent`: +0.3% CTR
- **Scientific Impact**: Feature impact varies wildly by niche (e.g., "shocked face" might hurt CTR in minimal design niches).

## 4. Comment Signal Filtering (`railway-api/GAP_ULTIMATE.py`)
- **Issue**: `filter_high_signal_comments` uses a hardcoded dictionary of "good" and "bad" words with arbitrary point values.
- **Code Location**: `filter_high_signal_comments` function.
- **Current Logic**:
    - `HIGH_INTENT_KEYWORDS` (+2 points)
    - `LOW_INTENT_KEYWORDS` (-1 point)
- **Scientific Impact**: Fails to capture semantic meaning or context; susceptible to language bias.

## 5. Niche Saturation (Market Intelligence)
- **Issue**: Uses generic thresholds for "saturation" based on search result counts.
- **Scientific Impact**: High search volume in Gaming is "normal", but in a micro-niche it's "saturated". Single threshold fails.

---

## Remediation Plan
All above features will be replaced by:
1.  **Niche-Specific XGBoost Models**: Trained on large datasets per category (Gaming, Education, Tech, etc.).
2.  **Semantic Classifiers**: BERT/DistilBERT fine-tuned on comment data for signal detection.
3.  **Data-Derived Weights**: Feature importance derived from SHAP values of trained models, not manuall assigned.
