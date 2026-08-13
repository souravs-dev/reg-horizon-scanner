import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_scanner.db"

import pytest_asyncio

from app.db import Base, SessionLocal
from app.db import engine as db_engine


@pytest_asyncio.fixture
async def session():
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as s:
        yield s
