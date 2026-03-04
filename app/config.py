"""Centralized application configuration using Pydantic Settings.

All environment variables are validated at startup. Missing required
values raise immediately instead of failing silently at request time.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # --- Server ---
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"
    allowed_origins: str = "*"  # comma-separated origins for CORS

    # --- SSL (optional) ---
    ssl_keyfile: str | None = None
    ssl_certfile: str | None = None

    # --- Auth ---
    visioguard_api_key: str | None = None  # fallback single key
    api_key_db: str | None = None  # path to SQLite key database
    fernet_key: str | None = None  # base64 Fernet key for DB encryption

    # --- Rate Limiting ---
    rate_limit_calls: int = Field(default=100, ge=1)
    rate_limit_period: int = Field(default=60, ge=1)  # seconds

    # --- ML Models ---
    detection_model: str = "facebook/detr-resnet-50"
    captioning_model: str = "Salesforce/blip-image-captioning-base"
    default_confidence_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    max_image_dimension: int = Field(default=4096, ge=256)
    preload_models: bool = False  # load models at startup vs. first request

    # --- Upload ---
    max_file_size: int = Field(default=10 * 1024 * 1024, ge=1)  # 10 MB

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v

    @field_validator("allowed_origins")
    @classmethod
    def parse_origins(cls, v: str) -> str:
        return v.strip()

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def db_path(self) -> Path | None:
        if self.api_key_db:
            return Path(self.api_key_db)
        return None


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — parsed once per process."""
    return Settings()
