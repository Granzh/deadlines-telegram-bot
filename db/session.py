import logging

from sqlalchemy import StaticPool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from config import settings
from exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Determine if using SQLite
is_sqlite = str(settings.database_url).startswith("sqlite")

# Configure engine parameters based on database type
engine_params: dict[str, object] = {
    "echo": False,
}

if is_sqlite:
    # SQLite-specific configuration
    engine_params["poolclass"] = StaticPool
    engine_params["connect_args"] = {"check_same_thread": False}
else:
    # Server database configuration (PostgreSQL, MySQL, etc.)
    engine_params["pool_size"] = 20
    engine_params["max_overflow"] = 30
    engine_params["pool_pre_ping"] = True
    engine_params["pool_recycle"] = 3600

engine = create_async_engine(str(settings.database_url), **engine_params)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db():
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


async def check_db_connection() -> bool:
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
