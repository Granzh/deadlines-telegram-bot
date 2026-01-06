from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from db.base import Base
from db.models import Deadline, NotificationSettings, User

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """Create session factory for testing."""
    async with engine.connect() as conn:
        trans = await conn.begin()

        async_session = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
        )

        yield async_session

        await trans.rollback()


@pytest_asyncio.fixture
async def session(engine):
    """Create a session for each test."""
    async with engine.connect() as conn:
        trans = await conn.begin()

        async_session = async_sessionmaker(
            bind=conn,
            expire_on_commit=False,
        )

        async with async_session() as session:
            yield session

        await trans.rollback()


@pytest_asyncio.fixture
async def sample_user(session):
    """Create a sample user for testing."""
    user = User(telegram_id=12345, timezone="UTC")
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_deadline(session, sample_user):
    """Create a sample deadline for testing."""
    future_date = datetime.now(timezone.utc) + timedelta(days=7)
    deadline = Deadline(
        user_id=sample_user.id, title="Test Deadline", deadline_at=future_date
    )
    session.add(deadline)
    await session.commit()
    await session.refresh(deadline)
    return deadline


@pytest_asyncio.fixture
async def multiple_deadlines(session, sample_user):
    """Create multiple deadlines for testing."""
    deadlines_data = [
        datetime.now(timezone.utc) + timedelta(days=1),
        datetime.now(timezone.utc) + timedelta(days=3),
        datetime.now(timezone.utc) + timedelta(days=7),
    ]
    deadlines = []

    for i, deadline_date in enumerate(deadlines_data):
        deadline = Deadline(
            user_id=sample_user.id,
            title=f"Test Deadline {i + 1}",
            deadline_at=deadline_date,
        )
        session.add(deadline)
        deadlines.append(deadline)

    await session.commit()

    for deadline in deadlines:
        await session.refresh(deadline)

    return deadlines


@pytest.fixture
def valid_deadline_data():
    """Provide valid deadline data for testing."""
    return {
        "title": "Test Deadline",
        "deadline_at": datetime.now(timezone.utc) + timedelta(days=7),
    }


@pytest.fixture
def invalid_deadline_data():
    """Provide invalid deadline data for testing."""
    return {"title": "", "deadline_at": datetime.now(timezone.utc) - timedelta(days=1)}


@pytest.fixture
def past_deadline_data():
    """Provide past deadline data for testing."""
    return {
        "title": "Past Deadline",
        "deadline_at": datetime.now(timezone.utc) - timedelta(days=1),
    }


@pytest.fixture
def future_deadline_data():
    """Provide future deadline data for testing."""
    return {
        "title": "Future Deadline",
        "deadline_at": datetime.now(timezone.utc) + timedelta(days=7),
    }


@pytest_asyncio.fixture
async def sample_notification_settings(session, sample_user):
    """Create sample notification settings for testing."""
    settings = NotificationSettings(
        user_id=sample_user.id,
        notify_on_due=True,
        notify_1_hour=True,
        notify_3_hours=True,
        notify_1_day=True,
        notify_3_days=True,
        notify_1_week=True,
    )
    session.add(settings)
    await session.commit()
    await session.refresh(settings)
    return settings
