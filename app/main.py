"""VisioGuardAI — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.middleware import RequestIdMiddleware
from app.routes import detection
from app.security.auth import load_api_keys

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — replaces deprecated @app.on_event("startup") / ("shutdown")
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle for the application."""
    logger.info("Starting VisioGuardAI...")

    load_api_keys(settings)

    if settings.preload_models:
        logger.info("Pre-loading ML models (PRELOAD_MODELS=true)...")
        from app.services.captioner import _load_model as load_captioner
        from app.services.detector import _load_model as load_detector

        load_detector()
        load_captioner()
        logger.info("Models pre-loaded")

    logger.info("VisioGuardAI ready")
    yield
    logger.info("Shutting down VisioGuardAI")


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="VisioGuardAI",
    description="AI-powered threat detection via computer vision",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Middleware (applied bottom-up: last added = outermost) ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIdMiddleware)

# --- Routes ---

app.include_router(detection.router)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# Dev entry point:  python -m app.main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        ssl_keyfile=settings.ssl_keyfile,
        ssl_certfile=settings.ssl_certfile,
    )
