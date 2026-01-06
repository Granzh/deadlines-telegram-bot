import logging

from sqlalchemy import StaticPool
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from exceptions import DatabaseError

logger = logging.getLogger(__name__)


def create_engine_and_session(database_url: str):
    engine_params: dict[str, object] = {
        "echo": False,
    }

    url = make_url(database_url)

    if url.drivername.startswith("sqlite"):
        # SQLite-specific configuration
        engine_params["poolclass"] = StaticPool
        engine_params["connect_args"] = {"check_same_thread": False}
    else:
        # Server database configuration (PostgreSQL, MySQL, etc.)
        engine_params["pool_size"] = 20
        engine_params["max_overflow"] = 30
        engine_params["pool_pre_ping"] = True
        engine_params["pool_recycle"] = 3600

    engine = create_async_engine(str(url), **engine_params)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    return engine, Session


async def init_db(engine):
    """Initialize database with error handling using migrations"""
    try:
        logger.info("Initializing database...")
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Database initialization failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {e}")
        raise DatabaseError(f"Unexpected database error: {e}") from e


async def check_db_connection(engine) -> bool:
    """Check database connection"""
    try:
        from sqlalchemy import text

        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.debug("Database connection check passed")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
