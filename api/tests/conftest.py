"""Shared pytest fixtures for API tests."""

import os

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.asset import Asset
from app.models.job import Job
from app.models.report import Report


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Get the test database URL from environment."""
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set")
    if os.getenv("TEST_DATABASE_ALLOW_RESET") != "1":
        pytest.skip("Set TEST_DATABASE_ALLOW_RESET=1 to allow schema reset")
    return url


@pytest.fixture(scope="session")
async def async_engine(test_db_url: str):
    """Create async database engine and set up schema."""
    engine = create_async_engine(test_db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db(async_engine):
    """Create a database session for each test.

    Only use this fixture for integration tests that need a real database.
    """
    session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    async with session_factory() as session:
        # Clean tables before each test
        await session.execute(delete(Job))
        await session.execute(delete(Asset))
        await session.execute(delete(Report))
        await session.commit()
        yield session
