"""Application-specific exception hierarchy.

All custom exceptions carry a machine-readable ``code`` so API consumers
can handle errors programmatically without parsing human-readable messages.
"""

from fastapi import HTTPException
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    HTTP_415_UNSUPPORTED_MEDIA_TYPE,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_503_SERVICE_UNAVAILABLE,
)


class AppError(HTTPException):
    """Base for all application errors.  Adds an error ``code`` field."""

    def __init__(
        self,
        status_code: int,
        code: str,
        detail: str,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={"code": code, "message": detail},
        )


# --- Auth / Security ---

class MissingApiKeyError(AppError):
    def __init__(self) -> None:
        super().__init__(HTTP_403_FORBIDDEN, "MISSING_API_KEY", "API key is required")


class InvalidApiKeyError(AppError):
    def __init__(self) -> None:
        super().__init__(HTTP_403_FORBIDDEN, "INVALID_API_KEY", "Invalid API key")


class ExpiredApiKeyError(AppError):
    def __init__(self) -> None:
        super().__init__(HTTP_403_FORBIDDEN, "EXPIRED_API_KEY", "API key has expired")


class RateLimitExceededError(AppError):
    def __init__(self, retry_after: int) -> None:
        self.retry_after = retry_after
        super().__init__(
            HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMIT_EXCEEDED",
            "Rate limit exceeded. Try again later.",
        )


# --- Validation ---

class FileTooLargeError(AppError):
    def __init__(self, max_bytes: int) -> None:
        mb = max_bytes / (1024 * 1024)
        super().__init__(
            HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "FILE_TOO_LARGE",
            f"File exceeds the {mb:.0f} MB limit",
        )


class UnsupportedMediaTypeError(AppError):
    def __init__(self, content_type: str) -> None:
        super().__init__(
            HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "UNSUPPORTED_MEDIA_TYPE",
            f"Content type '{content_type}' is not supported",
        )


class EmptyFileError(AppError):
    def __init__(self) -> None:
        super().__init__(HTTP_400_BAD_REQUEST, "EMPTY_FILE", "Uploaded file is empty")


class ImageTooLargeError(AppError):
    def __init__(self, width: int, height: int, max_dim: int) -> None:
        super().__init__(
            HTTP_400_BAD_REQUEST,
            "IMAGE_TOO_LARGE",
            f"Image dimensions {width}x{height} exceed the {max_dim}px limit",
        )


# --- Inference ---

class InferenceError(AppError):
    def __init__(self) -> None:
        super().__init__(
            HTTP_500_INTERNAL_SERVER_ERROR,
            "INFERENCE_ERROR",
            "Failed to process image. Please try again.",
        )


class ModelUnavailableError(AppError):
    def __init__(self, model_name: str) -> None:
        super().__init__(
            HTTP_503_SERVICE_UNAVAILABLE,
            "MODEL_UNAVAILABLE",
            f"Model '{model_name}' is not available",
        )
