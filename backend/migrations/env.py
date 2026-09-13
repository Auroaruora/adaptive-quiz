"""Alembic environment.

Runs synchronously over `pymysql` even though the application uses an
async engine: migrations run once, so async buys nothing here and costs
a noticeably more complex setup.
"""

import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_BACKEND_ROOT))

from app.config import database_url  # noqa: E402
from app.db.models import Base  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emits migration SQL to stdout without connecting to a database."""
    context.configure(
        url=database_url("pymysql"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Applies migrations against the configured database."""
    # The URL is passed straight to create_engine rather than through
    # alembic.ini, so credentials stay out of committed files and the
    # password is never run through configparser interpolation.
    engine = create_engine(database_url("pymysql"), pool_pre_ping=True)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
