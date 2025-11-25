from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import SQL_URL

from .base import Base

engine = create_async_engine(SQL_URL, echo=False)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
