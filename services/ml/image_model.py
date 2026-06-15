"""
Vision Transformer (ViT) model for pet disease image classification.

Fine-tuned on Roboflow pet disease datasets:
- Dog Diseases (9 classes - skin + eye)
- Cat Diseases (41 classes - ear, eye, skin, fur, wounds, lumps)
- Skin Disease (6 classes - bacterial, fungal, dermatitis, ringworm, demodicosis)
"""
import torch
import torch.nn as nn
from PIL import Image
from pathlib import Path
from django.conf import settings
from services.disease_mapping import IMAGE_CLASS_MAPPING

_model: nn.Module | None = None
_transform: object | None = None
_idx_to_label: dict[int, str] | None = None


def _get_device() -> torch.device:
    device_str = getattr(settings, 'DEVICE', 'cpu')
    if device_str == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def get_image_transform():
    """Get the standard ViT image preprocessing transform."""
    global _transform
    if _transform is None:
        from torchvision import transforms
        _transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
    return _transform


def _discover_classes_from_datasets() -> list[str]:
    """Scan all dataset directories and return sorted unique class names."""
    datasets_dir = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"
    classes = set()
    for ds_name in ["dog_diseases", "cat_diseases", "skin_disease"]:
        ds_path = datasets_dir / ds_name
        if not ds_path.exists():
            continue
        for split in ["train", "valid", "test"]:
            split_dir = ds_path / split
            if not split_dir.exists():
                continue
            for d in split_dir.iterdir():
                if d.is_dir():
                    classes.add(d.name)
    return sorted(classes)


def load_model(checkpoint_path: str | None = None) -> nn.Module:
    """
    Load the ViT model with custom classification head.
    Caches the model in memory after first load.
    """
    global _model, _idx_to_label

    if _model is not None:
        return _model

    device = _get_device()
    class_names = _discover_classes_from_datasets()
    image_model_name = getattr(settings, 'IMAGE_MODEL_NAME', 'google/vit-base-patch16-224-in21k')
    image_model_path = getattr(settings, 'IMAGE_MODEL_PATH', '')

    try:
        from transformers import ViTForImageClassification

        checkpoint = checkpoint_path or image_model_path

        if checkpoint and Path(checkpoint).exists():
            print(f"[ViT] Loading fine-tuned model from {checkpoint}")
            checkpoint_data = torch.load(checkpoint, map_location=device, weights_only=False)

            if isinstance(checkpoint_data, dict) and "classes" in checkpoint_data:
                class_names = checkpoint_data["classes"]
                state_dict = checkpoint_data["model_state_dict"]
            else:
                state_dict = checkpoint_data

            num_classes = len(class_names)
            _model = ViTForImageClassification.from_pretrained(
                image_model_name,
                num_labels=num_classes,
                ignore_mismatched_sizes=True,
            )
            _model.load_state_dict(state_dict, strict=False)
        else:
            num_classes = len(class_names) if class_names else 6
            print(f"[ViT] No checkpoint found. Loading pretrained {image_model_name}")
            print(f"[ViT] Classification head: {num_classes} classes (untrained)")
            print(f"[ViT] Train the model first: python scripts/train_image_model.py")
            _model = ViTForImageClassification.from_pretrained(
                image_model_name,
                num_labels=num_classes,
                ignore_mismatched_sizes=True,
            )

        _model.to(device)
        _model.eval()
        _idx_to_label = {i: name for i, name in enumerate(class_names)}
        return _model

    except ImportError as e:
        raise ImportError(
            "Transformers library not installed. Run: pip install transformers"
        ) from e


def predict(image_path: str) -> tuple[str, float]:
    """
    Run inference on a single image.

    Returns:
        Tuple of (standardized_disease_label, confidence_score)
    """
    model = load_model()
    device = _get_device()
    transform = get_image_transform()

    image = Image.open(image_path).convert("RGB")
    image_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image_tensor)
        logits = outputs.logits
        probabilities = torch.nn.functional.softmax(logits, dim=1)
        confidence, predicted_idx = torch.max(probabilities, dim=1)

    confidence_val = confidence.item()
    raw_class = _idx_to_label.get(predicted_idx.item(), "Unknown")
    standardized = IMAGE_CLASS_MAPPING.get(raw_class.lower(), raw_class)

    return standardized, confidence_val
