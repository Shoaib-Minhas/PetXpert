"""
EfficientNet B4 / B3 model for pet disease image classification.

Uses timm (matching the proven Kaggle notebook — 90.74% val accuracy)
for better pretrained weights and consistent behavior.

Architecture:
    EfficientNet-B4 (default) or EfficientNet-B3 backbone
    → Custom Linear classification head
    → N output classes (auto-discovered from checkpoint or dataset)

Usage:
    from services.ml.efficientnet_model import predict, load_model
    result = predict("path/to/pet_image.jpg")
    # {"disease": "ringworm", "confidence": 0.978, "top_predictions": [...]}

The model expects a fine-tuned checkpoint at:
    data/model_checkpoints/efficientnet-pet-disease.pth
"""
import os
import torch
import torch.nn as nn
import timm
from PIL import Image
from pathlib import Path
from django.conf import settings
from torchvision import transforms
from services.disease_mapping import IMAGE_CLASS_MAPPING, DISEASES

# ── ImageNet normalization constants ─────────────────────────────────────
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD  = [0.229, 0.224, 0.225]

# ── Module-level cache ───────────────────────────────────────────────────
_model: nn.Module | None = None
_transform: object | None = None
_class_names: list[str] = []
_device_str: str | None = None
_img_size: int = 380  # B4 default


def _get_device() -> torch.device:
    global _device_str
    if _device_str is None:
        device_setting = getattr(settings, 'DEVICE', 'cpu')
        if device_setting == "cuda" and torch.cuda.is_available():
            _device_str = "cuda"
        else:
            _device_str = "cpu"
    return torch.device(_device_str)


def get_image_transform():
    """EfficientNet preprocessing — matches the training notebook."""
    global _transform, _img_size
    if _transform is None:
        _img_size = getattr(settings, 'EFFICIENTNET_IMAGE_SIZE', 380)
        _transform = transforms.Compose([
            transforms.Resize((_img_size, _img_size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    return _transform


def _get_class_names() -> list[str]:
    """
    Return class names — from checkpoint, auto-discovered, or fallback.
    """
    global _class_names
    if _class_names:
        return _class_names
    discovered = _discover_from_datasets()
    if discovered:
        _class_names = discovered
        return _class_names
    _class_names = list(DISEASES)
    return _class_names


def _discover_from_datasets() -> list[str]:
    """Auto-discover class names from the datasets directory."""
    datasets_dir = Path(__file__).resolve().parent.parent.parent / "data" / "datasets"
    if not datasets_dir.exists():
        return []

    classes = set()
    for item in sorted(datasets_dir.iterdir()):
        if item.is_dir() and (item / "train").exists():
            for cls_dir in (item / "train").iterdir():
                if cls_dir.is_dir():
                    classes.add(cls_dir.name)
        elif item.is_dir():
            has_images = any(
                f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
                for f in item.iterdir()
            )
            if has_images:
                classes.add(item.name)
    return sorted(classes)


def _normalize_class_names(raw) -> list[str]:
    """Convert class names from checkpoint to plain strings."""
    return [str(c) for c in raw]


def load_model(checkpoint_path: str | None = None) -> nn.Module:
    """
    Load EfficientNet with fine-tuned weights.

    Priority:
        1. checkpoint_path argument
        2. settings.EFFICIENTNET_MODEL_PATH
        3. ImageNet pretrained (untrained head — low accuracy)
    """
    global _model, _class_names, _img_size

    if _model is not None:
        return _model

    device = _get_device()
    variant = getattr(settings, 'EFFICIENTNET_VARIANT', 'efficientnet-b4')
    num_classes = getattr(settings, 'EFFICIENTNET_NUM_CLASSES', 5)
    model_path = checkpoint_path or getattr(settings, 'EFFICIENTNET_MODEL_PATH', '')

    # Try loading checkpoint first
    ckpt = None
    if model_path and os.path.exists(model_path):
        print(f"[EfficientNet] Loading checkpoint: {model_path}")
        ckpt = torch.load(model_path, map_location=device, weights_only=False)

        if isinstance(ckpt, dict):
            if "class_names" in ckpt:
                _class_names = _normalize_class_names(ckpt["class_names"])
                num_classes = len(_class_names)
            if "img_size" in ckpt:
                _img_size = ckpt["img_size"]
            if "variant" in ckpt:
                variant = ckpt.get("variant", variant)
            if "num_classes" in ckpt:
                num_classes = ckpt["num_classes"]

    # Create model via timm (matching the notebook)
    model_name = f"efficientnet_{variant.replace('efficientnet-', '')}"
    _model = timm.create_model(model_name, pretrained=(ckpt is None))
    _model.classifier = nn.Linear(_model.classifier.in_features, num_classes)

    # Load weights
    if ckpt is not None:
        state_dict = ckpt.get("model_state_dict", ckpt)
        if isinstance(state_dict, dict) and "model_state_dict" not in state_dict:
            # Handle DataParallel wrapper
            if any(k.startswith("module.") for k in state_dict.keys()):
                from collections import OrderedDict
                clean = OrderedDict()
                for k, v in state_dict.items():
                    clean[k.replace("module.", "")] = v
                state_dict = clean
        _model.load_state_dict(state_dict, strict=False)

    _model.to(device)
    _model.eval()

    classes = _get_class_names()
    print(f"[EfficientNet] Model ready — {len(classes)} classes: {classes}")
    return _model


def predict(image_path: str, top_k: int = 3) -> dict | None:
    """
    Run inference on a single pet image.

    Returns:
        {
            "disease": "ringworm",
            "confidence": 0.9783,
            "top_predictions": [
                {"disease": "ringworm", "confidence": 0.9783},
                {"disease": "fungal_infection", "confidence": 0.0150},
                {"disease": "hotspot", "confidence": 0.0042},
            ],
        }
        or None on failure.
    """
    if not os.path.exists(image_path):
        return None

    try:
        model = load_model()
        device = _get_device()
        transform = get_image_transform()
        class_names = _get_class_names()

        image = Image.open(image_path).convert("RGB")
        tensor = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)

        topk_conf, topk_indices = torch.topk(probs, k=min(top_k, len(class_names)), dim=1)

        top_predictions = []
        for i in range(topk_indices.size(1)):
            idx = topk_indices[0, i].item()
            conf = topk_conf[0, i].item()
            raw_label = class_names[idx]
            # Map to standardized category AND keep raw name
            standardized = IMAGE_CLASS_MAPPING.get(raw_label.lower(), raw_label)
            top_predictions.append({
                "disease": standardized,       # e.g., "Skin Infection"
                "raw_class": raw_label,        # e.g., "ringworm"
                "confidence": round(conf, 4),
            })

        return {
            "disease": top_predictions[0]["disease"],
            "raw_class": top_predictions[0]["raw_class"],
            "confidence": round(top_predictions[0]["confidence"], 4),
            "top_predictions": top_predictions,
        }

    except Exception as e:
        print(f"[EfficientNet] Inference error: {type(e).__name__}: {e}")
        return None


def predict_batch(image_paths: list[str], top_k: int = 3) -> list[dict | None]:
    """Batch inference on multiple images."""
    model = load_model()
    device = _get_device()
    transform = get_image_transform()
    class_names = _get_class_names()
    results = []

    batch_size = getattr(settings, 'EFFICIENTNET_BATCH_SIZE', 8)
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i + batch_size]
        batch_tensors = []
        valid_map = {}  # batch_idx -> result_idx

        for j, path in enumerate(batch_paths):
            if not os.path.exists(path):
                results.append(None)
                continue
            try:
                image = Image.open(path).convert("RGB")
                tensor = transform(image)
                batch_tensors.append(tensor)
                valid_map[len(batch_tensors) - 1] = i + j
            except Exception:
                results.append(None)

        if not batch_tensors:
            continue

        batch = torch.stack(batch_tensors).to(device)
        with torch.no_grad():
            outputs = model(batch)
            probs = torch.softmax(outputs, dim=1)

        for b in range(len(batch_tensors)):
            prob = probs[b]
            topk_conf, topk_indices = torch.topk(prob, k=min(top_k, len(class_names)))

            top_predictions = []
            for k in range(topk_indices.size(0)):
                idx = topk_indices[k].item()
                conf = topk_conf[k].item()
                raw = class_names[idx]
                std = IMAGE_CLASS_MAPPING.get(raw.lower(), raw)
                top_predictions.append({
                    "disease": std,
                    "raw_class": raw,
                    "confidence": round(conf, 4),
                })

            results.append({
                "disease": top_predictions[0]["disease"],
                "raw_class": top_predictions[0]["raw_class"],
                "confidence": top_predictions[0]["confidence"],
                "top_predictions": top_predictions,
            })

    return results
