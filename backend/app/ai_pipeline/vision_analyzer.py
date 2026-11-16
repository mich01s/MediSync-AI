"""
MediSync AI — Vision Analyzer (AI Pipeline)
Performs anomaly detection on medical images (X-Ray, MRI, CT-Scan).

In production: loads a fine-tuned CNN/ViT model via PyTorch.
In demo mode: returns a structured simulation result without loading a model.
"""
import io
import os
from typing import Any

# ── Class label definitions ───────────────────────────────────────────────────

FINDING_LABELS = [
    "normal",
    "pneumonia",
    "pleural_effusion",
    "cardiomegaly",
    "atelectasis",
    "nodule",
    "mass",
    "consolidation",
]

MODEL_PATH = os.environ.get("VISION_MODEL_PATH", "app/ai_pipeline/models/vision_cnn.pt")

# ── Model loader ──────────────────────────────────────────────────────────────

_vision_model: Any = None


def _load_vision_model() -> Any:
    """Load a serialized PyTorch vision model; returns None if unavailable."""
    global _vision_model
    if _vision_model is not None:
        return _vision_model
    if not os.path.exists(MODEL_PATH):
        return None
    try:
        import torch
        _vision_model = torch.load(MODEL_PATH, map_location="cpu")
        _vision_model.eval()
        return _vision_model
    except Exception:
        return None


# ── MinIO image fetcher ───────────────────────────────────────────────────────

def _fetch_image_bytes(image_key: str) -> bytes | None:
    """Retrieve image bytes from MinIO using the stored object key."""
    try:
        from app.core.config import settings
        from minio import Minio

        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        response = client.get_object(settings.MINIO_BUCKET_MEDICAL_IMAGES, image_key)
        return response.read()
    except Exception:
        return None


# ── Main analyzer ─────────────────────────────────────────────────────────────

def analyze_medical_image(image_key: str) -> dict[str, Any]:
    """
    Analyze a medical image stored in MinIO/S3.

    Args:
        image_key: Object storage key for the image file.

    Returns:
        Dict with keys:
        - ``output``: classification result dict
        - ``confidence``: top-1 confidence score
    """
    model = _load_vision_model()
    image_bytes = _fetch_image_bytes(image_key)

    if model is not None and image_bytes is not None:
        return _torch_inference(image_bytes, model)

    return _simulation_result(image_key)


def _torch_inference(image_bytes: bytes, model: Any) -> dict[str, Any]:
    """Run actual PyTorch inference on the provided image bytes."""
    try:
        import torch
        from PIL import Image
        from torchvision import transforms

        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225]),
        ])
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        tensor = transform(img).unsqueeze(0)

        with torch.no_grad():
            logits = model(tensor)
            proba = torch.softmax(logits, dim=1)[0].tolist()

        top_idx = int(max(range(len(proba)), key=lambda i: proba[i]))
        return {
            "output": {
                "predicted_finding": FINDING_LABELS[top_idx],
                "probabilities": {
                    label: round(proba[i], 4)
                    for i, label in enumerate(FINDING_LABELS[:len(proba)])
                },
                "mode": "pytorch_cnn",
            },
            "confidence": round(proba[top_idx], 4),
        }
    except Exception as exc:
        return _simulation_result("error") | {"error": str(exc)}


def _simulation_result(image_key: str) -> dict[str, Any]:
    """
    Deterministic simulation result for demo/development when model is absent.
    Uses the image_key string hash to vary the returned finding.
    """
    idx = abs(hash(image_key)) % len(FINDING_LABELS)
    finding = FINDING_LABELS[idx]
    confidence = round(0.72 + (abs(hash(image_key[:5])) % 20) / 100, 2)

    return {
        "output": {
            "predicted_finding": finding,
            "probabilities": {
                label: round(0.05 if label != finding else confidence, 4)
                for label in FINDING_LABELS
            },
            "mode": "simulation",
            "note": "No trained model loaded. This is a simulated result for demo purposes.",
        },
        "confidence": confidence,
    }
