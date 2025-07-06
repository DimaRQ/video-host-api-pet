import os

import httpx
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import src.video.models  # noqa
from src.auth.router import router as auth_router
from src.db.session import Base, get_db
from src.video import router as video_router_module
from src.video.router import router as video_router


class TestProducer:
    async def send(self, *args, **kwargs):
        pass

    async def flush(self):
        pass


@pytest.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///./test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def override_get_db():
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(video_router)
    app.dependency_overrides[get_db] = override_get_db

    video_router_module.kafka_producer._producer = TestProducer()
    video_router_module.is_mp4 = lambda *_: True

    async with AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    await engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")
