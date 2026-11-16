"""
MediSync AI — Tabular Predictor (AI Pipeline)
Classifies patient risk level from vital sign metrics using XGBoost.

In demo mode (no trained model file present), returns a heuristic simulation
based on threshold rules. In production, load a serialized XGBoost model from disk.
"""
import os
from typing import Any

import numpy as np

# ── Feature definitions ───────────────────────────────────────────────────────

FEATURE_COLUMNS = [
    "bp_systolic",
    "bp_diastolic",
    "heart_rate",
    "temperature",
    "spo2",
    "glucose",
    "respiratory_rate",
]

RISK_LABELS = ["normal", "low_risk", "medium_risk", "high_risk"]

# ── Model loader (lazy) ───────────────────────────────────────────────────────

_model: Any = None
MODEL_PATH = os.environ.get("TABULAR_MODEL_PATH", "app/ai_pipeline/models/xgboost_risk.pkl")


def _load_model() -> Any:
    """Load the serialized XGBoost model; fall back to None if not found."""
    global _model
    if _model is not None:
        return _model

    if os.path.exists(MODEL_PATH):
        try:
            import joblib
            _model = joblib.load(MODEL_PATH)
            return _model
        except Exception:
            pass
    return None


# ── Prediction ────────────────────────────────────────────────────────────────

def predict_tabular(vitals: dict[str, Any]) -> dict[str, Any]:
    """
    Predict patient risk class from vital sign metrics.

    Args:
        vitals: Dict of vital sign values, e.g.::
            {
                "bp_systolic": 150, "bp_diastolic": 95,
                "heart_rate": 105, "temperature": 38.5,
                "spo2": 96, "glucose": 180
            }

    Returns:
        Dict with keys:
        - ``output``: prediction result dict
        - ``confidence``: probability of predicted class (0.0–1.0)
    """
    model = _load_model()

    if model is not None:
        # Build feature vector — fill missing with median defaults
        defaults = {
            "bp_systolic": 120, "bp_diastolic": 80, "heart_rate": 72,
            "temperature": 36.8, "spo2": 98, "glucose": 100, "respiratory_rate": 16
        }
        features = np.array(
            [[vitals.get(col, defaults[col]) for col in FEATURE_COLUMNS]]
        )
        proba = model.predict_proba(features)[0]
        predicted_idx = int(np.argmax(proba))
        return {
            "output": {
                "predicted_label": RISK_LABELS[predicted_idx],
                "probabilities": {
                    label: round(float(proba[i]), 4)
                    for i, label in enumerate(RISK_LABELS)
                },
                "mode": "xgboost",
            },
            "confidence": round(float(proba[predicted_idx]), 4),
        }

    # ── Heuristic simulation (demo mode) ─────────────────────────────────────
    return _heuristic_predict(vitals)


def _heuristic_predict(vitals: dict[str, Any]) -> dict[str, Any]:
    """Simple rule-based risk scoring when no model is available."""
    score = 0
    flags: list[str] = []

    if vitals.get("bp_systolic", 120) > 160:
        score += 2; flags.append("high_bp")
    elif vitals.get("bp_systolic", 120) > 140:
        score += 1; flags.append("elevated_bp")

    if vitals.get("heart_rate", 72) > 100:
        score += 1; flags.append("tachycardia")
    elif vitals.get("heart_rate", 72) < 50:
        score += 2; flags.append("bradycardia")

    if vitals.get("temperature", 36.8) > 38.5:
        score += 1; flags.append("fever")
    elif vitals.get("temperature", 36.8) > 39:
        score += 2; flags.append("high_fever")

    if vitals.get("spo2", 98) < 94:
        score += 2; flags.append("low_spo2")

    if vitals.get("glucose", 100) > 250:
        score += 1; flags.append("hyperglycemia")
    elif vitals.get("glucose", 100) < 70:
        score += 2; flags.append("hypoglycemia")

    label = RISK_LABELS[min(score, 3)]
    confidence = max(0.6, 1.0 - score * 0.08)

    return {
        "output": {
            "predicted_label": label,
            "risk_score": score,
            "triggered_flags": flags,
            "mode": "heuristic_simulation",
        },
        "confidence": round(confidence, 2),
    }
