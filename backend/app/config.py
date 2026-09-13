"""Application configuration, read from the environment.

Credentials live in the repo-root `.env` and are never hard-coded here.
"""

import os
import pathlib
from urllib.parse import quote_plus

from dotenv import load_dotenv

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

load_dotenv(_REPO_ROOT / ".env")

_DEFAULT_CORS_ORIGINS = ("http://localhost:3000",)


def _require(name: str) -> str:
    """Reads a required environment variable.

    Args:
        name: Environment variable name.

    Returns:
        The variable's value.

    Raises:
        RuntimeError: If the variable is unset or empty.
    """
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing environment variable: {name}")
    return value


def database_url(driver: str) -> str:
    """Builds the SQLAlchemy URL for the project database.

    Args:
        driver: DBAPI driver name. Use `aiomysql` for the application's
            async engine and `pymysql` for Alembic and the seed script.

    Returns:
        A SQLAlchemy connection URL.
    """
    user = quote_plus(_require("MYSQL_USER"))
    password = quote_plus(_require("MYSQL_PASSWORD"))
    database = _require("MYSQL_DATABASE")
    host = os.environ.get("MYSQL_HOST", "127.0.0.1")
    port = os.environ.get("MYSQL_PORT", "3306")
    return (
        f"mysql+{driver}://{user}:{password}@{host}:{port}/{database}"
        "?charset=utf8mb4"
    )


def cors_origins() -> list[str]:
    """Reads the browser origins allowed to call the API.

    Taken from `CORS_ORIGINS`, comma-separated. Unset means the local
    Next.js dev server, so a fresh checkout works without editing `.env`;
    the deployed origin is added in Phase 6 as configuration, not code.

    Returns:
        The allowed origins, in the order given.
    """
    raw = os.environ.get("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in raw.split(",")]
    return [origin for origin in origins if origin] or list(
        _DEFAULT_CORS_ORIGINS
    )
