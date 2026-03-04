"""BLIP-based image captioning service with lazy model loading."""

import io
import logging

import torch
from PIL import Image, UnidentifiedImageError
from transformers import BlipForConditionalGeneration, BlipProcessor

from app.config import get_settings
from app.exceptions import ImageTooLargeError, ModelUnavailableError

logger = logging.getLogger(__name__)

_processor: BlipProcessor | None = None
_model: BlipForConditionalGeneration | None = None


def _load_model() -> tuple[BlipProcessor, BlipForConditionalGeneration]:
    """Load the BLIP model on first call and cache it."""
    global _processor, _model
    if _processor is not None and _model is not None:
        return _processor, _model

    settings = get_settings()
    model_name = settings.captioning_model
    logger.info("Loading captioning model '%s'...", model_name)
    try:
        _processor = BlipProcessor.from_pretrained(model_name)
        _model = BlipForConditionalGeneration.from_pretrained(model_name)
    except Exception:
        logger.exception("Failed to load captioning model '%s'", model_name)
        raise ModelUnavailableError(model_name)
    logger.info("Captioning model loaded")
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


def generate_caption(image_bytes: bytes) -> str:
    """Return a natural-language caption describing the image."""
    processor, model = _load_model()
    image = _open_and_validate(image_bytes)

    inputs = processor(image, return_tensors="pt")
    with torch.no_grad():
        out = model.generate(**inputs)

    caption: str = processor.decode(out[0], skip_special_tokens=True)
    return caption or "No caption generated"
