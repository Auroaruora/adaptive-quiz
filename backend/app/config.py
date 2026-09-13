"""Application configuration, read from the environment.

Credentials live in the repo-root `.env` and are never hard-coded here.
"""

import os
import pathlib
from urllib.parse import quote_plus

from dotenv import load_dotenv

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

load_dotenv(_REPO_ROOT / ".env")


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
