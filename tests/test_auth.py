"""Tests for API key authentication."""

from datetime import datetime, timedelta

import pytest

from app.config import Settings
from app.exceptions import ExpiredApiKeyError, InvalidApiKeyError, MissingApiKeyError
from app.security.auth import (
    _api_keys_cache,
    load_api_keys,
    validate_api_key,
)


class TestLoadApiKeys:
    def test_loads_key_from_env(self, _reset_settings, _reset_auth):
        load_api_keys()
        assert "test-key-12345" in _api_keys_cache

    def test_no_key_configured(self, _reset_auth):
        """When neither env var nor DB is set, cache should be empty."""
        settings = Settings(_env_file=None, visioguard_api_key=None)
        load_api_keys(settings)
        assert len(_api_keys_cache) == 0


class TestValidateApiKey:
    async def test_valid_key(self, _reset_settings, _reset_auth):
        load_api_keys()
        result = await validate_api_key("test-key-12345")
        assert result == "test-key-12345"

    async def test_missing_key(self, _reset_settings, _reset_auth):
        load_api_keys()
        with pytest.raises(MissingApiKeyError):
            await validate_api_key("")

    async def test_missing_key_none(self, _reset_settings, _reset_auth):
        load_api_keys()
        with pytest.raises(MissingApiKeyError):
            await validate_api_key(None)

    async def test_invalid_key(self, _reset_settings, _reset_auth):
        load_api_keys()
        with pytest.raises(InvalidApiKeyError):
            await validate_api_key("wrong-key")

    async def test_expired_key(self, _reset_settings, _reset_auth):
        _api_keys_cache["expired-key"] = datetime.now() - timedelta(days=1)
        with pytest.raises(ExpiredApiKeyError):
            await validate_api_key("expired-key")
        assert "expired-key" not in _api_keys_cache
