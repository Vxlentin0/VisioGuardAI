"""Shared test fixtures for VisioGuardAI.

The ML service modules (detector, captioner) import ``transformers`` and
``torch`` at the top level. Those libraries may not be buildable or
compatible in every test environment (e.g., numpy 1.x vs 2.x). To avoid
that, we inject lightweight stub modules into ``sys.modules`` *before*
anything else imports them.
"""

import io
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PIL import Image

# ---------------------------------------------------------------------------
# Inject stub service modules so the import chain never touches transformers.
# ---------------------------------------------------------------------------

_FAKE_DETECTIONS = [
    {"label": "person", "score": 0.95, "box": [10.0, 20.0, 100.0, 200.0]}
]
_FAKE_CAPTION = "a person standing in a room"


def _stub_detect_objects(image_bytes, threshold=None):
    return list(_FAKE_DETECTIONS)


def _stub_generate_caption(image_bytes):
    return _FAKE_CAPTION


def _install_service_stubs():
    """Replace the real detector/captioner modules with test stubs."""
    for mod_name, func_name, stub in [
        ("app.services.detector", "detect_objects", _stub_detect_objects),
        ("app.services.captioner", "generate_caption", _stub_generate_caption),
    ]:
        mod = types.ModuleType(mod_name)
        setattr(mod, func_name, stub)
        sys.modules[mod_name] = mod


_install_service_stubs()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Ensure test env vars don't leak from one test to the next."""
    monkeypatch.setenv("VISIOGUARD_API_KEY", "test-key-12345")
    monkeypatch.delenv("API_KEY_DB", raising=False)
    monkeypatch.delenv("FERNET_KEY", raising=False)


@pytest.fixture()
def _reset_settings():
    """Clear the lru_cache on get_settings so env changes take effect."""
    from app.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def _reset_auth():
    """Reset the auth module cache between tests."""
    from app.security import auth

    auth._api_keys_cache.clear()
    auth._cache_loaded = False
    yield
    auth._api_keys_cache.clear()
    auth._cache_loaded = False


@pytest.fixture()
def client(_reset_settings, _reset_auth):
    """TestClient with auth reset and service stubs in place."""
    from app.main import app

    return TestClient(app)


@pytest.fixture()
def valid_image_bytes() -> bytes:
    """A minimal valid JPEG image."""
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), color="red").save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture()
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": "test-key-12345"}
