"""DETR-based object detection service with lazy model loading."""

import io
import logging

import torch
from PIL import Image, UnidentifiedImageError
from transformers import DetrForObjectDetection, DetrImageProcessor

from app.config import get_settings
from app.exceptions import ImageTooLargeError, ModelUnavailableError

logger = logging.getLogger(__name__)

_processor: DetrImageProcessor | None = None
_model: DetrForObjectDetection | None = None


def _load_model() -> tuple[DetrImageProcessor, DetrForObjectDetection]:
    """Load the DETR model on first call and cache it."""
    global _processor, _model
    if _processor is not None and _model is not None:
        return _processor, _model

    settings = get_settings()
    model_name = settings.detection_model
    logger.info("Loading detection model '%s'...", model_name)
    try:
        _processor = DetrImageProcessor.from_pretrained(model_name)
        _model = DetrForObjectDetection.from_pretrained(model_name)
    except Exception:
        logger.exception("Failed to load detection model '%s'", model_name)
        raise ModelUnavailableError(model_name)
    logger.info("Detection model loaded")
    return _processor, _model


def _open_and_validate(image_bytes: bytes) -> Image.Image:
    """Open raw bytes as a PIL image and enforce dimension limits."""
    try:
        image = Image.open(io.BytesIO(image_bytes))
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc

    image = image.convert("RGB")

    max_dim = get_settings().max_image_dimension
    w, h = image.size
    if w > max_dim or h > max_dim:
        raise ImageTooLargeError(w, h, max_dim)

    return image


def detect_objects(
    image_bytes: bytes,
    threshold: float | None = None,
) -> list[dict]:
    """Run object detection and return bounding-box dicts.

    Each dict has keys ``label``, ``score``, ``box`` (4-element list).
    """
    if threshold is None:
        threshold = get_settings().default_confidence_threshold

    processor, model = _load_model()
    image = _open_and_validate(image_bytes)

    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs)

    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(
        outputs, target_sizes=target_sizes, threshold=threshold
    )[0]

    return [
        {
            "label": model.config.id2label[label.item()],
            "score": round(score.item(), 4),
            "box": [round(c, 2) for c in box.tolist()],
        }
        for score, label, box in zip(
            results["scores"], results["labels"], results["boxes"]
        )
    ]
