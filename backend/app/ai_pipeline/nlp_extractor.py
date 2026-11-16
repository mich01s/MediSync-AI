"""
MediSync AI — NLP Extractor (AI Pipeline)
Extracts clinical entities and symptom embeddings from patient complaint text.

Uses Hugging Face Transformers pipeline in production.
Falls back to a keyword-based heuristic in demo/offline mode.
"""
import re
from typing import Any

# ── Keyword symptom dictionary ────────────────────────────────────────────────
# Maps common complaint keywords → candidate diagnoses
_SYMPTOM_MAP: dict[str, list[str]] = {
    "chest pain": ["angina", "myocardial_infarction", "pericarditis"],
    "shortness of breath": ["asthma", "pneumonia", "heart_failure", "COPD"],
    "headache": ["tension_headache", "migraine", "hypertension", "meningitis"],
    "fever": ["infection", "malaria", "typhoid", "dengue"],
    "cough": ["URTI", "pneumonia", "asthma", "tuberculosis"],
    "dizziness": ["hypotension", "anemia", "vestibular_disorder"],
    "fatigue": ["anemia", "diabetes", "hypothyroidism", "depression"],
    "nausea": ["gastritis", "pregnancy", "GERD", "food_poisoning"],
    "abdominal pain": ["appendicitis", "gastritis", "peptic_ulcer", "cholecystitis"],
    "back pain": ["muscle_strain", "herniated_disc", "kidney_stone"],
    "swelling": ["heart_failure", "renal_failure", "deep_vein_thrombosis"],
    "diabetes": ["type2_diabetes", "diabetic_complication"],
    "hypertension": ["essential_hypertension", "secondary_hypertension"],
}

# ── HuggingFace pipeline (lazy loaded) ───────────────────────────────────────

_hf_pipeline: Any = None


def _load_hf_pipeline() -> Any:
    """Lazily load a HuggingFace zero-shot or NER pipeline."""
    global _hf_pipeline
    if _hf_pipeline is not None:
        return _hf_pipeline
    try:
        from transformers import pipeline
        _hf_pipeline = pipeline(
            "zero-shot-classification",
            model="cross-encoder/nli-MiniLM2-L6-H768",
            device=-1,  # CPU
        )
        return _hf_pipeline
    except Exception:
        return None


# ── Main extractor ────────────────────────────────────────────────────────────

def extract_nlp_features(complaint_text: str) -> dict[str, Any]:
    """
    Extract symptoms and candidate diagnoses from free-text patient complaints.

    Args:
        complaint_text: Raw complaint string from the patient, e.g.
            "I have been having chest pain and shortness of breath since yesterday."

    Returns:
        Dict with keys:
        - ``output``: extraction result dict
        - ``confidence``: overall confidence score
    """
    # Try HuggingFace zero-shot classification first
    pipe = _load_hf_pipeline()
    if pipe is not None:
        return _hf_extract(complaint_text, pipe)

    return _keyword_extract(complaint_text)


def _hf_extract(text: str, pipe: Any) -> dict[str, Any]:
    """Use zero-shot classification to match symptoms to candidate conditions."""
    candidate_labels = list(_SYMPTOM_MAP.keys())
    try:
        result = pipe(text, candidate_labels=candidate_labels, multi_label=True)
        # Filter labels with score > 0.4
        matched = [
            {"symptom": lbl, "score": round(sc, 4)}
            for lbl, sc in zip(result["labels"], result["scores"])
            if sc > 0.4
        ]
        conditions: set[str] = set()
        for item in matched:
            conditions.update(_SYMPTOM_MAP.get(item["symptom"], []))

        return {
            "output": {
                "matched_symptoms": matched,
                "candidate_diagnoses": sorted(conditions),
                "mode": "huggingface_zero_shot",
            },
            "confidence": round(max(result["scores"][:3]), 4) if result["scores"] else 0.5,
        }
    except Exception as exc:
        # Fall back gracefully
        return _keyword_extract(text)


def _keyword_extract(text: str) -> dict[str, Any]:
    """Keyword-based heuristic extraction — used when HF model is unavailable."""
    lower = text.lower()
    matched_symptoms: list[str] = []
    candidate_conditions: set[str] = set()

    for keyword, conditions in _SYMPTOM_MAP.items():
        if keyword in lower:
            matched_symptoms.append(keyword)
            candidate_conditions.update(conditions)

    # Also look for negation patterns (simple heuristic)
    negated: list[str] = []
    for sym in matched_symptoms[:]:
        # e.g. "no chest pain" or "denies headache"
        if re.search(rf"\b(no|denies|without|without any)\b.{{0,20}}{re.escape(sym)}", lower):
            matched_symptoms.remove(sym)
            negated.append(sym)

    confidence = min(0.9, 0.5 + len(matched_symptoms) * 0.1)

    return {
        "output": {
            "matched_symptoms": matched_symptoms,
            "negated_symptoms": negated,
            "candidate_diagnoses": sorted(candidate_conditions),
            "word_count": len(text.split()),
            "mode": "keyword_heuristic",
        },
        "confidence": round(confidence, 2),
    }
