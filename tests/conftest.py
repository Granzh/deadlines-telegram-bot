import asyncio
import subprocess
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from db.base import Base
from db.models import Deadline, NotificationSettings, User
from db.session import Session

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def migrate():
    subprocess.run(["alembic", "upgrade", "head"], check=True)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create a fresh database engine for each test."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Override the global Session for testing."""
    global Session
    original_session = Session

    test_session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # Temporarily replace global Session
    import db.session

    db.session.Session = test_session_maker

    yield test_session_maker

    # Restore original Session
    db.session.Session = original_session


@pytest_asyncio.fixture
async def sample_user(session):
    """Create a sample user for testing."""
    user = User(id=1, telegram_id=12345, timezone="UTC")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_deadline(session, sample_user):
    """Create a sample deadline for testing."""
    future_date = datetime.now() + timedelta(days=7)
    deadline = Deadline(
        user_id=sample_user.id, title="Test Deadline", deadline_at=future_date
    )
    session.add(deadline)
    await session.commit()
    await session.refresh(deadline)
    return deadline


@pytest_asyncio.fixture
async def sample_notification_settings(session, sample_user):
    """Create sample notification settings for testing."""
    settings = NotificationSettings(
        user_id=sample_user.id,
        notify_1_week=True,
        notify_3_days=True,
        notify_1_day=True,
        notify_3_hours=True,
        notify_1_hour=True,
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings


@pytest_asyncio.fixture
async def multiple_deadlines(session, sample_user):
    """Create multiple deadlines for testing."""
    deadlines = []

    # Create deadlines with different dates
    dates = [
        datetime.now() + timedelta(days=1),
        datetime.now() + timedelta(days=3),
        datetime.now() + timedelta(days=7),
    ]

    for i, date in enumerate(dates):
        deadline = Deadline(
            user_id=sample_user.id, title=f"Test Deadline {i + 1}", deadline_at=date
        )
        session.add(deadline)
        deadlines.append(deadline)

    await session.commit()

    for deadline in deadlines:
        await session.refresh(deadline)

    return deadlines


@pytest.fixture
def past_deadline_data():
    """Data for a deadline in the past."""
    return {"title": "Past Deadline", "deadline_at": datetime.now() - timedelta(days=1)}


@pytest.fixture
def future_deadline_data():
    """Data for a deadline in the future."""
    return {
        "title": "Future Deadline",
        "deadline_at": datetime.now() + timedelta(days=7),
    }


@pytest.fixture
def invalid_deadline_data():
    """Data for invalid deadline."""
    return {"title": "", "deadline_at": datetime.now() - timedelta(days=1)}
