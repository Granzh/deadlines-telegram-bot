import logging

from alembic import command
from alembic.config import Config
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.sql import text

from config import settings
from exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Determine if using SQLite
is_sqlite = str(settings.database_url).startswith("sqlite")

# Configure engine parameters based on database type
engine_params = {
    "echo": False,
    "pool_size": None,
}

if is_sqlite:
    # SQLite-specific configuration
    engine_params["poolclass"] = StaticPool
    engine_params["connect_args"] = {"check_same_thread": False}
    engine_params.pop("pool_size", None)
else:
    # Server database configuration (PostgreSQL, MySQL, etc.)
    engine_params["pool_size"] = 20
    engine_params["max_overflow"] = 30
    engine_params["pool_pre_ping"] = True
    engine_params["pool_recycle"] = 3600

engine = create_async_engine(str(settings.database_url), **engine_params)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def run_migrations():
    """Run Alembic migrations"""
    try:
        logger.info("Running database migrations...")
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.database_url))
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")
        raise DatabaseError(f"Migration failed: {e}") from e


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
