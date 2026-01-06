from unittest.mock import ANY, AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db.models import Deadline, User
from db.session import check_db_connection, create_engine_and_session, init_db
from exceptions import DatabaseError


class TestDatabaseSession:
    """Test database session configuration and operations"""

    @pytest.mark.asyncio
    async def test_init_sqlite_db_success(self):
        """Test successful database initialization"""
        # Create a temporary engine for testing
        engine, _ = create_engine_and_session("sqlite+aiosqlite:///:memory:")

        assert engine.pool.__class__.__name__ == "StaticPool"

    @pytest.mark.asyncio
    async def test_init_postgres_db_success(self):
        """Test successful database initialization"""
        # Create a temporary engine for testing
        engine, _ = create_engine_and_session(
            "postgresql+asyncpg://user:password@localhost/dbname"
        )

    @pytest.mark.asyncio
    async def test_init_db_with_sqlalchemy_error(self):
        """Test database initialization with SQLAlchemy error"""
        # Mock engine.begin to raise SQLAlchemyError
        mock_connection = Mock()
        mock_connection.run_sync = Mock(side_effect=Exception("Database error"))

        mock_cm = Mock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_cm.__aexit__ = AsyncMock(return_value=None)

        mock_engine = Mock()
        mock_engine.begin.return_value = mock_cm

        with pytest.raises(DatabaseError):
            await init_db(mock_engine)

    @pytest.mark.asyncio
    async def test_init_db_with_general_error(self):
        """Test database initialization with general error"""
        mock_connection = Mock()
        mock_connection.execute = AsyncMock(side_effect=Exception("Database error"))

        mock_ctx_manager = Mock()
        mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_ctx_manager.__aexit__ = AsyncMock(return_value=None)

        mock_engine = Mock()
        mock_engine.begin.return_value = mock_ctx_manager

        with pytest.raises(DatabaseError):
            await init_db(mock_engine)

    @pytest.mark.asyncio
    async def test_check_init_db_sqlachemy_error_raise(self):
        mock_engine = Mock()
        mock_engine.begin.side_effect = SQLAlchemyError("Mocked SQLAlchemyError")

        with pytest.raises(DatabaseError):
            await init_db(mock_engine)

    @pytest.mark.asyncio
    async def test_check_db_connection_success(self):
        mock_connection = Mock()
        mock_connection.execute = AsyncMock(return_value=None)

        mock_ctx_manager = Mock()
        mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_ctx_manager.__aexit__ = AsyncMock(return_value=None)

        mock_engine = Mock()
        mock_engine.begin.return_value = mock_ctx_manager

        with (
            patch("db.session.logger"),
        ):
            result = await check_db_connection(mock_engine)

        assert result is True
        mock_connection.execute.assert_called_once_with(ANY)

    @pytest.mark.asyncio
    async def test_check_db_connection_failure(self):
        """Test failed database connection check"""

        mock_engine = Mock()

        mock_ctx_manager = Mock()
        mock_ctx_manager.__aenter__ = AsyncMock(return_value=None)
        mock_ctx_manager.__aexit__ = AsyncMock(return_value=None)

        mock_engine.begin.return_value = mock_ctx_manager

        result = await check_db_connection(mock_engine)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_db_connection_execute_error(self):
        """Test database connection check with execute error"""
        mock_connection = Mock()
        mock_connection.execute = AsyncMock(side_effect=Exception("Execute error"))

        mock_ctx_manager = Mock()
        mock_ctx_manager.__aenter__ = AsyncMock(return_value=mock_connection)
        mock_ctx_manager.__aexit__ = AsyncMock(return_value=None)

        mock_engine = Mock()
        mock_engine.begin.return_value = mock_ctx_manager

        result = await check_db_connection(mock_engine)

        assert result is False

    @pytest_asyncio.fixture
    async def test_session_usage(self, test_db_session):
        """Test that session can be used for database operations"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Test basic query
            result = await session.execute(text("SELECT 1"))
            assert result is not None

    @pytest_asyncio.fixture
    async def test_session_commit(self, test_db_session, sample_user):
        """Test session commit functionality"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Create a new user
            new_user = User(id=999, telegram_id=99999, timezone="UTC")
            session.add(new_user)
            await session.commit()

            # Verify user was saved
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.id == 999))
            saved_user = result.scalar_one()
            assert saved_user.telegram_id == 99999

    @pytest_asyncio.fixture
    async def test_session_rollback(self, test_db_session):
        """Test session rollback functionality"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Create a new user
            new_user = User(id=998, telegram_id=99899, timezone="UTC")
            session.add(new_user)

            # Don't commit, let rollback happen automatically

        # Verify user was not saved
        async with session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(select(User).where(User.id == 998))
            saved_user = result.scalar_one_or_none()
            assert saved_user is None

    @pytest_asyncio.fixture
    async def test_multiple_concurrent_sessions(self, test_db_session):
        """Test using multiple sessions concurrently"""
        session_maker = test_db_session
        results = []

        async def create_user(user_id, telegram_id):
            async with session_maker() as session:
                user = User(id=user_id, telegram_id=telegram_id, timezone="UTC")
                session.add(user)
                await session.commit()
                return user_id

        # Create multiple users concurrently
        tasks = [
            create_user(1001, 100101),
            create_user(1002, 100102),
            create_user(1003, 100103),
        ]

        results = await asyncio.gather(*tasks)

        # Verify all users were created
        assert sorted(results) == [1001, 1002, 1003]

        # Verify in database
        async with session_maker() as session:
            from sqlalchemy import select

            result = await session.execute(
                select(User).where(User.id.in_([1001, 1002, 1003]))
            )
            users = result.scalars().all()
            assert len(users) == 3

    @pytest_asyncio.fixture
    async def test_session_with_relationships(self, test_db_session, sample_user):
        """Test session usage with model relationships"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Create user and deadline
            user = User(id=2001, telegram_id=200101, timezone="UTC")
            session.add(user)
            await session.flush()  # Get user ID without committing

            from datetime import datetime, timedelta

            deadline = Deadline(
                user_id=user.id,
                title="Test Deadline",
                deadline_at=datetime.now() + timedelta(days=7),
            )
            session.add(deadline)
            await session.commit()

            # Test relationship
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            result = await session.execute(
                select(User)
                .options(selectinload(User.deadlines))
                .where(User.id == user.id)
            )
            loaded_user = result.scalar_one()

            assert len(loaded_user.deadlines) == 1
            assert loaded_user.deadlines[0].title == "Test Deadline"

    @pytest_asyncio.fixture
    async def test_session_error_handling(self, test_db_session):
        """Test session error handling"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Try to violate constraint (if any)
            with pytest.raises(Exception):
                # This might not raise an error in SQLite, but shows the pattern
                invalid_user = User(
                    id=None, telegram_id=99999, timezone="UTC"
                )  # id should not be None
                session.add(invalid_user)
                await session.commit()

    @pytest_asyncio.fixture
    async def test_session_refresh(self, test_db_session, sample_user):
        """Test session refresh functionality"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Get user
            from sqlalchemy import select

            result = await session.execute(
                select(User).where(User.id == sample_user.id)
            )
            user = result.scalar_one()

            # Modify user directly in database (simulate external change)
            await session.execute(
                text("UPDATE users SET timezone = 'Europe/Moscow' WHERE id = :user_id"),
                {"user_id": sample_user.id},
            )
            await session.commit()

            # Refresh user
            await session.refresh(user)

            assert user.timezone == "Europe/Moscow"

    @pytest_asyncio.fixture
    async def test_session_delete(self, test_db_session, sample_deadline):
        """Test session delete functionality"""
        session_maker = test_db_session

        async with session_maker() as session:
            # Get deadline
            from sqlalchemy import select

            result = await session.execute(
                select(Deadline).where(Deadline.id == sample_deadline.id)
            )
            deadline = result.scalar_one()

            # Delete deadline
            await session.delete(deadline)
            await session.commit()

            # Verify deletion
            result = await session.execute(
                select(Deadline).where(Deadline.id == sample_deadline.id)
            )
            deleted_deadline = result.scalar_one_or_none()
            assert deleted_deadline is None
