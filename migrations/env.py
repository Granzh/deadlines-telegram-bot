from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig
from typing import AsyncGenerator

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, async_session_maker

from config import settings
from db.base import Base
from db.models import Deadline, User

target_metadata = Base.metadata


def get_url() -> str:
    return str(settings.database_url)


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = context.config
    configuration.set_main_option("sqlalchemy.url", get_url())

    connectable = AsyncEngine(
        context.config.attributes.get("engine", pool.NullPool(get_url()))
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
