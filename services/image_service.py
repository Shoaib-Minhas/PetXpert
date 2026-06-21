"""
Image processing service — validates, preprocesses, and classifies uploaded images.

Architecture:
    Image → EfficientNet B3/B4 (fine-tuned) → disease predictions (JSON)
    The predictions are then injected into the LLM prompt by llm_service.py.

For now, this is a placeholder that performs basic validation. The EfficientNet
inference will be implemented in services/ml/efficientnet_model.py (Phase 2).
"""
import os
from pathlib import Path
from PIL import Image
from django.conf import settings


def validate_image(image_path: str) -> dict | None:
    """
    Validate an uploaded image before processing.

    Returns:
        None if valid, or a dict with {"error": str} if invalid.
    """
    if not os.path.exists(image_path):
        return {"error": "Image file not found."}

    try:
        img = Image.open(image_path)
        img.verify()
        img = Image.open(image_path)  # Re-open after verify
        if img.width < 50 or img.height < 50:
            return {
                "error": "Image too small — please upload a clearer photo (minimum 50x50 pixels)."
            }
        return None  # Valid
    except Exception as e:
        return {"error": f"Invalid or corrupted image file: {str(e)}"}


def classify_image(image_path: str) -> dict | None:
    """
    Classify a pet disease image using EfficientNet.

    NOTE: This function currently returns None until the EfficientNet model
    is fine-tuned and deployed. Once the model checkpoint is available at
    data/model_checkpoints/efficientnet-pet-disease.pth, this will return:

        {
            "disease": "Skin Infection",
            "confidence": 0.87,
            "top_predictions": [
                {"disease": "Skin Infection", "confidence": 0.87},
                {"disease": "Ear Infection", "confidence": 0.08},
                {"disease": "Parasites", "confidence": 0.03},
            ],
        }

    Args:
        image_path: Absolute path to the uploaded image

    Returns:
        dict or None on failure
    """
    # Validate image first
    validation_error = validate_image(image_path)
    if validation_error:
        return {
            "disease": "Unknown",
            "confidence": 0.0,
            "error": validation_error["error"],
        }

    # Try EfficientNet inference
    try:
        from services.ml.efficientnet_model import predict
        return predict(image_path)
    except ImportError:
        # EfficientNet not installed yet — return None so callers degrade gracefully
        return None
    except Exception:
        return None


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
