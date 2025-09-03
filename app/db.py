from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import declarative_base

from app.config import settings

ASYNC_DB_URL = settings.DATABASE_URL
if ASYNC_DB_URL.startswith("sqlite+") and "aiosqlite" not in ASYNC_DB_URL:
    # ensure async driver
    ASYNC_DB_URL = ASYNC_DB_URL.replace("sqlite://", "sqlite+aiosqlite://")

engine = create_async_engine(ASYNC_DB_URL, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
Base = declarative_base()

async def init_db():
    from app import models  # ensure models are imported
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
