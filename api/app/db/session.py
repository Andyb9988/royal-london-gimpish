from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def sanitize_asyncpg_url(url: str) -> tuple[str, dict]:
    connect_args: dict = {}
    url_obj = make_url(url)
    if url_obj.drivername.endswith("+asyncpg"):
        query = dict(url_obj.query)
        sslmode = query.pop("sslmode", None)
        if sslmode and sslmode != "disable":
            connect_args["ssl"] = True
        url_obj = url_obj.set(query=query)
    return url_obj.render_as_string(hide_password=False), connect_args


def create_engine_and_sessionmaker(
    url: str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    db_url, connect_args = sanitize_asyncpg_url(url)
    engine = create_async_engine(db_url, echo=False, connect_args=connect_args)
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return engine, sessionmaker


async def init_db(app: FastAPI) -> None:
    engine, sessionmaker = create_engine_and_sessionmaker(settings.DATABASE_URL)
    app.state.db_engine = engine
    app.state.db_sessionmaker = sessionmaker


async def close_db(app: FastAPI) -> None:
    engine = getattr(app.state, "db_engine", None)
    if engine is not None:
        await engine.dispose()


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    sessionmaker = getattr(request.app.state, "db_sessionmaker", None)
    if sessionmaker is None:
        raise RuntimeError("Database sessionmaker is not initialized")

    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


__all__ = [
    "create_engine_and_sessionmaker",
    "sanitize_asyncpg_url",
    "init_db",
    "close_db",
    "get_db",
]
