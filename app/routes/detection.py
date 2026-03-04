"""Detection API endpoint — single-image threat analysis."""

import asyncio
import logging
from functools import partial

from fastapi import APIRouter, Depends, File, Response, UploadFile
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.exceptions import (
    AppError,
    EmptyFileError,
    FileTooLargeError,
    InferenceError,
    UnsupportedMediaTypeError,
)
from app.middleware import add_rate_limit_headers
from app.security.auth import validate_api_key
from app.security.rate_limit import RateLimiter
from app.services.captioner import generate_caption
from app.services.detector import detect_objects

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["detection"])

ALLOWED_CONTENT_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/bmp", "image/tiff"}
)


# --- Response models ---

class BoundingBox(BaseModel):
    label: str
    score: float = Field(ge=0, le=1)
    box: list[float] = Field(min_length=4, max_length=4)


class DetectionResponse(BaseModel):
    detections: list[BoundingBox]
    caption: str


# --- Dependency factories ---

def _get_rate_limiter(settings: Settings = Depends(get_settings)) -> RateLimiter:
    """Build or reuse a rate limiter from settings."""
    return _rate_limiter_singleton(settings.rate_limit_calls, settings.rate_limit_period)


_rl_instance: RateLimiter | None = None


def _rate_limiter_singleton(calls: int, period: int) -> RateLimiter:
    global _rl_instance
    if _rl_instance is None:
        _rl_instance = RateLimiter(calls=calls, period=period)
    return _rl_instance


# --- Endpoint ---

@router.post(
    "/detect",
    response_model=DetectionResponse,
    summary="Detect threats in an image",
    description="Upload an image to receive object detections and a descriptive caption.",
)
async def detect_image(
    response: Response,
    file: UploadFile = File(..., description="Image file (JPEG, PNG, WebP, BMP, TIFF)"),
    api_key: str = Depends(validate_api_key),
    settings: Settings = Depends(get_settings),
    rate_limiter: RateLimiter = Depends(_get_rate_limiter),
):
    # --- rate limit ---
    rl_info = await rate_limiter.check(api_key)
    add_rate_limit_headers(
        response,
        limit=rl_info.limit,
        remaining=rl_info.remaining,
        reset=rl_info.reset,
    )

    # --- content-type validation ---
    content_type = file.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedMediaTypeError(content_type)

    # --- read and validate size ---
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise EmptyFileError()
    if len(image_bytes) > settings.max_file_size:
        raise FileTooLargeError(settings.max_file_size)

    # --- inference (off the event loop) ---
    loop = asyncio.get_running_loop()
    try:
        detections, caption = await asyncio.gather(
            loop.run_in_executor(None, partial(detect_objects, image_bytes)),
            loop.run_in_executor(None, partial(generate_caption, image_bytes)),
        )
    except AppError:
        raise  # re-raise structured errors (ImageTooLarge, ModelUnavailable, etc.)
    except Exception:
        logger.exception("Unhandled error during inference")
        raise InferenceError()

    return DetectionResponse(detections=detections, caption=caption)
