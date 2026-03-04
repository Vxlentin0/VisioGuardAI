"""Tests for application configuration."""

import pytest

from app.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings(
            _env_file=None,
            visioguard_api_key="k",
        )
        assert s.fastapi_host == "0.0.0.0"
        assert s.fastapi_port == 8000
        assert s.rate_limit_calls == 100
        assert s.rate_limit_period == 60
        assert s.max_file_size == 10 * 1024 * 1024

    def test_cors_origins_parsing(self):
        s = Settings(
            _env_file=None,
            allowed_origins="http://a.com, http://b.com",
        )
        assert s.cors_origins == ["http://a.com", "http://b.com"]

    def test_invalid_log_level(self):
        with pytest.raises(Exception):
            Settings(_env_file=None, log_level="INVALID")

    def test_confidence_threshold_bounds(self):
        with pytest.raises(Exception):
            Settings(_env_file=None, default_confidence_threshold=1.5)
        with pytest.raises(Exception):
            Settings(_env_file=None, default_confidence_threshold=-0.1)
