"""API key authentication with SQLite-backed storage and env-var fallback."""

import logging
import sqlite3
from datetime import datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from fastapi import Security
from fastapi.security import APIKeyHeader

from app.config import Settings, get_settings
from app.exceptions import ExpiredApiKeyError, InvalidApiKeyError, MissingApiKeyError

logger = logging.getLogger(__name__)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# In-memory cache: plaintext key -> expiration datetime
_api_keys_cache: dict[str, datetime] = {}
_cache_loaded: bool = False


def _build_fernet(settings: Settings) -> Fernet | None:
    """Return a Fernet cipher from settings, or None if unconfigured."""
    if not settings.fernet_key:
        return None
    try:
        return Fernet(settings.fernet_key.encode())
    except (ValueError, TypeError):
        logger.error("FERNET_KEY is malformed — cannot decrypt database keys")
        return None


def _load_keys_from_db(settings: Settings) -> dict[str, datetime]:
    """Load active, non-expired keys from the SQLite database."""
    db_path = settings.db_path
    if db_path is None or not db_path.exists():
        return {}

    fernet = _build_fernet(settings)
    keys: dict[str, datetime] = {}

    try:
        with sqlite3.connect(str(db_path), timeout=5) as conn:
            rows = conn.execute(
                "SELECT api_key, expires_at FROM ApiKeys "
                "WHERE is_active = 1 AND expires_at > ?",
                (datetime.now().isoformat(),),
            ).fetchall()
    except sqlite3.Error:
        logger.exception("Failed to query API keys database at %s", db_path)
        return {}

    for encrypted_key, expires_at_str in rows:
        try:
            plaintext = (
                fernet.decrypt(encrypted_key.encode()).decode()
                if fernet
                else encrypted_key
            )
            keys[plaintext] = datetime.fromisoformat(expires_at_str)
        except (InvalidToken, ValueError, UnicodeDecodeError):
            logger.warning("Skipping corrupt key row in database")

    return keys


def _load_keys_from_env(settings: Settings) -> dict[str, datetime]:
    """Fallback: load a single key from VISIOGUARD_API_KEY."""
    key = settings.visioguard_api_key
    if not key:
        return {}
    return {key: datetime.now() + timedelta(days=30)}


def load_api_keys(settings: Settings | None = None) -> None:
    """Load API keys — database first, then env-var fallback."""
    global _cache_loaded
    if settings is None:
        settings = get_settings()

    db_keys = _load_keys_from_db(settings)
    if db_keys:
        _api_keys_cache.update(db_keys)
        logger.info("Loaded %d API key(s) from database", len(db_keys))
    else:
        env_keys = _load_keys_from_env(settings)
        _api_keys_cache.update(env_keys)
        if env_keys:
            logger.info("Loaded API key from VISIOGUARD_API_KEY env var")
        else:
            logger.warning("No API keys configured — all requests will be rejected")

    _cache_loaded = True


def reload_api_keys() -> None:
    """Clear the cache and re-read from all sources."""
    _api_keys_cache.clear()
    global _cache_loaded
    _cache_loaded = False
    load_api_keys()


async def validate_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """FastAPI dependency — validates the X-API-Key header."""
    if not _cache_loaded:
        load_api_keys()

    if not api_key:
        raise MissingApiKeyError()

    expiration = _api_keys_cache.get(api_key)
    if expiration is None:
        logger.warning("Rejected request with unknown API key")
        raise InvalidApiKeyError()

    if datetime.now() > expiration:
        del _api_keys_cache[api_key]
        logger.info("Rejected request with expired API key")
        raise ExpiredApiKeyError()

    return api_key
