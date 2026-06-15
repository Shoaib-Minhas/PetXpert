"""
Image processing service — validates, preprocesses, and classifies uploaded images.
"""
import os
from pathlib import Path
from PIL import Image
from django.conf import settings


def classify_image(image_path: str) -> dict | None:
    """
    Classify a pet disease image using the ViT model.

    Args:
        image_path: Absolute path to the uploaded image

    Returns:
        dict with {"disease": str, "confidence": float} or None on failure
    """
    if not os.path.exists(image_path):
        return None

    # Validate image
    try:
        img = Image.open(image_path)
        img.verify()
        img = Image.open(image_path)  # Re-open after verify
        if img.width < 50 or img.height < 50:
            return {
                "disease": "Unknown",
                "confidence": 0.0,
                "error": "Image too small — please upload a clearer photo",
            }
    except Exception:
        return None

    # Run inference
    try:
        from services.ml.image_model import predict
        disease, confidence = predict(image_path)
        return {"disease": disease, "confidence": round(confidence, 4)}
    except ImportError:
        return None
    except Exception:
        return {"disease": "Unknown", "confidence": 0.0}


def get_image_dimensions(image_path: str) -> tuple[int, int]:
    """Get the width and height of an image."""
    with Image.open(image_path) as img:
        return img.size


def is_valid_image(file_bytes: bytes) -> bool:
    """Check if file bytes represent a valid image."""
    try:
        from io import BytesIO
        img = Image.open(BytesIO(file_bytes))
        img.verify()
        return True
    except Exception:
        return False
