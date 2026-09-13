"""Async engine and session factory for the application.

Alembic and the seed script connect separately over `pymysql`; only the
request path uses this async engine.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import database_url

engine = create_async_engine(database_url("aiomysql"), pool_pre_ping=True)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    """Yields a session bound to the request, closing it on completion."""
    async with async_session() as session:
        yield session
