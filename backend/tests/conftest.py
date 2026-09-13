"""Fixtures for API tests.

Tests run against the real MySQL schema rather than a substitute, since
the schema leans on generated columns, CHECK constraints and composite
foreign keys that only MySQL enforces.

Nothing they write survives. Each test opens one connection, begins a
transaction on it, and hands the application a session bound to that same
connection in savepoint mode — so the endpoint's own commit lands on a
savepoint and the outer rollback undoes the lot.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import database_url
from app.db.models import Topic
from app.db.session import get_session
from app.main import app


@pytest.fixture
async def session():
    """Yields a session whose writes are rolled back afterwards."""
    engine = create_async_engine(database_url("aiomysql"))
    async with engine.connect() as connection:
        transaction = await connection.begin()
        db = AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        try:
            yield db
        finally:
            await db.close()
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def client(session):
    """Yields an HTTP client talking to the app over the test session."""

    async def _use_test_session():
        yield session

    app.dependency_overrides[get_session] = _use_test_session
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as http:
        yield http
    app.dependency_overrides.clear()


@pytest.fixture
async def topic_id(session):
    """Id of the seeded logarithms topic."""
    return await session.scalar(
        select(Topic.id).where(Topic.slug == "logarithms")
    )


@pytest.fixture
async def user_id(client):
    """Creates a student through the API and returns their id."""
    response = await client.post("/users", json={"displayName": "Test"})
    assert response.status_code == 201
    return response.json()["id"]
