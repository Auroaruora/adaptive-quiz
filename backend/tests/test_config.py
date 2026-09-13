"""Tests for environment-driven configuration."""

import pytest

from app import config


class TestDatabaseUrl:
    """Building the connection URL."""

    def test_selects_the_requested_driver(self):
        assert config.database_url("pymysql").startswith("mysql+pymysql://")
        assert config.database_url("aiomysql").startswith("mysql+aiomysql://")

    def test_requests_utf8mb4(self):
        """The schema is utf8mb4, so the connection must agree."""
        assert "charset=utf8mb4" in config.database_url("pymysql")

    def test_fails_loudly_when_a_credential_is_missing(self, monkeypatch):
        """Misconfiguration should stop the process, not reach MySQL."""
        monkeypatch.delenv("MYSQL_USER", raising=False)
        with pytest.raises(RuntimeError, match="MYSQL_USER"):
            config.database_url("pymysql")

    def test_escapes_a_password_containing_url_characters(self, monkeypatch):
        """An unescaped '@' or '/' would silently corrupt the URL."""
        monkeypatch.setenv("MYSQL_PASSWORD", "p@ss/w:rd")
        url = config.database_url("pymysql")
        assert "p%40ss%2Fw%3Ard" in url
