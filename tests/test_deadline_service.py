import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from db.models import Deadline, User
from exceptions import (
    DeadlineCreationError,
    DeadlineNotFoundError,
    InvalidDeadlineError,
    InvalidTimezoneError,
    ValidationError,
)
from services.deadline_service import DeadlineService


class TestDeadlineService:
    """Test cases for DeadlineService"""

    @pytest.mark.asyncio
    async def test_get_or_create_user_return_existing(self, session, db_session):
        """Test getting an existing user"""
        service = DeadlineService(db_session)

        user = User(telegram_id=1, timezone="UTC")
        session.add(user)
        await session.commit()

        result = await service._get_or_create_user_by_id(session, user_id=1)
        assert result.telegram_id == 1
        assert result.timezone == "UTC"

    @pytest.mark.asyncio
    async def test_get_or_create_user_create_new(self, session, db_session):
        """Test creating new user when not exists"""
        service = DeadlineService(db_session)

        user = await service._get_or_create_user_by_id(session, user_id=456)

        assert user.telegram_id == 456
        assert user.timezone == "UTC"

    @pytest.mark.asyncio
    async def test_create_deadline_success(self, session, db_session):
        """Test successful deadline creation"""
        service = DeadlineService(db_session)
        future_date = datetime.now() + timedelta(days=7)

        deadline = await service.create(
            user_id=1, title="Test Deadline", dt=future_date
        )

        assert deadline.id is not None
        assert deadline.title == "Test Deadline"
        assert deadline.user_id == 1
        assert deadline.deadline_at == future_date

    @pytest.mark.asyncio
    async def test_create_deadline_in_past_raises_error(self, session, db_session):
        """Test creating deadline in past raises error"""
        service = DeadlineService(db_session)
        past_date = datetime.now() - timedelta(days=1)

        with pytest.raises(InvalidDeadlineError):
            await service.create(user_id=1, title="Past Deadline", dt=past_date)

    @pytest.mark.asyncio
    async def test_create_deadline_empty_title_raises_error(self, session, db_session):
        """Test creating deadline with empty title raises error"""
        service = DeadlineService(db_session)
        future_date = datetime.now() + timedelta(days=7)

        with pytest.raises(ValidationError):
            await service.create(user_id=1, title="", dt=future_date)

    @pytest.mark.asyncio
    async def test_create_deadline_raise_infrastructure_error(self, db_session, caplog):
        service = DeadlineService(db_session)
        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(side_effect=Exception("DB is down"))

        with pytest.raises(DeadlineCreationError):
            await service.create(
                user_id=1, title="Test", dt=datetime.now() + timedelta(days=7)
            )

        assert any(
            "Failed to create deadline" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_create_deadline_whitespace_title_raises_error(
        self, session, db_session
    ):
        """Test creating deadline with whitespace title raises error"""
        service = DeadlineService(db_session)
        future_date = datetime.now() + timedelta(days=7)

        with pytest.raises(ValidationError):
            await service.create(user_id=1, title="   ", dt=future_date)

    @pytest.mark.asyncio
    async def test_create_deadline_strips_title_whitespace(self, session, db_session):
        """Test creating deadline strips title whitespace"""
        service = DeadlineService(db_session)
        future_date = datetime.now() + timedelta(days=7)

        deadline = await service.create(
            user_id=1, title="  Test Deadline  ", dt=future_date
        )

        assert deadline.title == "Test Deadline"

    @pytest.mark.asyncio
    async def test_get_due_deadlines(self, session, db_session):
        """Test getting due deadlines"""
        service = DeadlineService(db_session)

        # Create a past deadline
        past_deadline = Deadline(
            user_id=1,
            title="Past Deadline",
            deadline_at=datetime.now() - timedelta(days=1),
        )
        session.add(past_deadline)

        # Create a future deadline
        future_deadline = Deadline(
            user_id=1,
            title="Future Deadline",
            deadline_at=datetime.now() + timedelta(days=1),
        )
        session.add(future_deadline)

        await session.commit()

        due_deadlines = await service.get_due()

        # Should only return the past deadline
        assert len(due_deadlines) == 1
        assert due_deadlines[0].title == "Past Deadline"

    @pytest.mark.asyncio
    async def test_get_due_deadlines_raises_error(self, session, db_session, caplog):
        """Test get_due_deadlines raises error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.get_due()

    @pytest.mark.asyncio
    async def test_list_for_user_success(self, session, multiple_deadlines, db_session):
        """Test listing deadlines for user"""
        service = DeadlineService(db_session)

        deadlines = await service.list_for_user(user_id=1)

        assert len(deadlines) == len(multiple_deadlines)
        # Should be ordered by deadline_at
        assert (
            deadlines[0].deadline_at
            <= deadlines[1].deadline_at
            <= deadlines[2].deadline_at
        )

    @pytest.mark.asyncio
    async def test_list_for_user_empty_list(self, session, db_session):
        """Test listing deadlines for user with no deadlines"""
        service = DeadlineService(db_session)

        deadlines = await service.list_for_user(user_id=999)

        assert deadlines == []

    @pytest.mark.asyncio
    async def test_list_for_user_error(self, session, db_session, caplog):
        """Test listing deadlines for user with error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.list_for_user(user_id=1)

        assert "Something went wrong" in caplog.text

    @pytest.mark.asyncio
    async def test_delete_deadline_success(self, session, sample_deadline, db_session):
        """Test successful deadline deletion"""
        service = DeadlineService(db_session)

        result = await service.delete(sample_deadline.id, sample_deadline.user_id)

        assert result is True

        # Verify deadline is deleted
        from sqlalchemy import select

        from db.models import Deadline
        from db.session import Session

        async with Session() as session:
            result = await session.execute(
                select(Deadline).where(Deadline.id == sample_deadline.id)
            )
            deleted_deadline = result.scalar_one_or_none()
            assert deleted_deadline is None

    @pytest.mark.asyncio
    async def test_delete_deadline_not_found_raises_error(self, session, db_session):
        """Test deleting non-existent deadline raises error"""
        service = DeadlineService(db_session)

        with pytest.raises(DeadlineNotFoundError):
            await service.delete(99999, 1)

    @pytest.mark.asyncio
    async def test_delete_deadline_error(
        self, session, db_session, sample_deadline, caplog
    ):
        """Test deleting deadline with error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.delete(sample_deadline.id, sample_deadline.user_id)

        assert "Something went wrong" in caplog.text

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, session, sample_deadline, db_session):
        """Test getting deadline by ID"""
        service = DeadlineService(db_session)

        deadline = await service.get_by_id(sample_deadline.id, sample_deadline.user_id)

        assert deadline is not None
        assert deadline.id == sample_deadline.id
        assert deadline.title == sample_deadline.title

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, session, db_session):
        """Test getting non-existent deadline by ID"""
        service = DeadlineService(db_session)

        deadline = await service.get_by_id(99999, 1)

        assert deadline is None

    @pytest.mark.asyncio
    async def test_get_by_id_error(self, db_session, sample_deadline, caplog):
        """Test getting deadline by ID with error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.get_by_id(sample_deadline.id, sample_deadline.user_id)

    @pytest.mark.asyncio
    async def test_get_or_create_user_new_user(self, session, db_session):
        """Test getting or creating new user by telegram_id"""
        service = DeadlineService(db_session)

        user = await service.get_or_create_user(telegram_id=12345)

        assert user.telegram_id == 12345
        assert user.timezone == "UTC"
        assert user.id is not None

    @pytest.mark.asyncio
    async def test_get_or_create_user_existing_user(self, sample_user, db_session):
        """Test getting existing user by telegram_id"""
        service = DeadlineService(db_session)

        user = await service.get_or_create_user(telegram_id=sample_user.telegram_id)

        assert user.telegram_id == sample_user.telegram_id
        assert user.id == sample_user.id

    @pytest.mark.asyncio
    async def test_get_or_create_user_error(self, db_session, caplog):
        """Test getting or creating user with error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.get_or_create_user(telegram_id=12345)

        assert "Something went wrong" in caplog.text

    @pytest.mark.asyncio
    async def test_edit_timezone_success(self, session, sample_user, db_session):
        """Test successful timezone edit"""
        service = DeadlineService(db_session)

        result = await service.edit_timezone(sample_user.telegram_id, "Europe/Moscow")

        assert result is True

        # Verify timezone was updated
        from sqlalchemy import select

        from db.models import User
        from db.session import Session

        async with Session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == sample_user.telegram_id)
            )
            user = result.scalar_one()
            assert user.timezone == "Europe/Moscow"

    @pytest.mark.asyncio
    async def test_edit_timezone_invalid_timezone_raises_error(
        self, session, sample_user, db_session
    ):
        """Test editing with invalid timezone raises error"""
        service = DeadlineService(db_session)

        with pytest.raises(InvalidTimezoneError):
            await service.edit_timezone(sample_user.telegram_id, "Invalid/Timezone")

    @pytest.mark.asyncio
    async def test_edit_timezone_creates_user_if_not_exists(self, session, db_session):
        """Test editing timezone creates user if not exists"""
        service = DeadlineService(db_session)

        result = await service.edit_timezone(99999, "Europe/Moscow")

        assert result is True

        # Verify user was created
        from sqlalchemy import select

        from db.models import User
        from db.session import Session

        async with Session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == 99999)
            )
            user = result.scalar_one()
            assert user.timezone == "Europe/Moscow"

    @pytest.mark.asyncio
    async def test_edit_timezone_error(self, db_session, caplog):
        """Test editing timezone with error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.edit_timezone(999999, "Europe/Moscow")

    @pytest.mark.asyncio
    async def test_get_timezone_for_user_exists(self, session, sample_user, db_session):
        """Test getting timezone for existing user"""
        service = DeadlineService(db_session)

        timezone = await service.get_timezone_for_user(sample_user.telegram_id)

        assert timezone == sample_user.timezone

    @pytest.mark.asyncio
    async def test_get_timezone_for_user_not_exists_returns_utc(
        self, session, db_session
    ):
        """Test getting timezone for non-existent user returns UTC"""
        service = DeadlineService(db_session)

        timezone = await service.get_timezone_for_user(999999)

        assert timezone == "UTC"

    @pytest.mark.asyncio
    async def test_get_timezone_for_user_error(self, db_session, caplog):
        """Test getting timezone for non-existent user with error"""
        service = DeadlineService(db_session)

        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(
            side_effect=Exception("Something went wrong")
        )

        with pytest.raises(Exception):
            await service.get_timezone_for_user(999999)

    @pytest.mark.asyncio
    async def test_update_deadline_success(self, session, sample_deadline, db_session):
        """Test successful deadline update"""
        service = DeadlineService(db_session)
        new_title = "Updated Title"
        new_date = datetime.now() + timedelta(days=14)

        result = await service.update(
            deadline_id=sample_deadline.id, title=new_title, dt=new_date
        )

        assert result is True

        # Verify deadline was updated
        updated_deadline = await service.get_by_id(
            sample_deadline.id, sample_deadline.user_id
        )
        assert updated_deadline is not None
        assert updated_deadline.title == new_title
        assert updated_deadline.deadline_at == new_date

    @pytest.mark.asyncio
    async def test_update_deadline_title_only(
        self, session, sample_deadline, db_session
    ):
        """Test updating only deadline title"""
        service = DeadlineService(db_session)
        new_title = "Updated Title Only"

        result = await service.update(deadline_id=sample_deadline.id, title=new_title)

        assert result is True

        # Verify deadline was updated
        updated_deadline = await service.get_by_id(
            sample_deadline.id, sample_deadline.user_id
        )
        assert updated_deadline is not None
        assert updated_deadline.title == new_title
        # Deadline time should remain unchanged
        assert updated_deadline.deadline_at == sample_deadline.deadline_at

    @pytest.mark.asyncio
    async def test_update_deadline_date_only(
        self, session, sample_deadline, db_session
    ):
        """Test updating only deadline date"""
        service = DeadlineService(db_session)
        new_date = datetime.now() + timedelta(days=14)

        result = await service.update(deadline_id=sample_deadline.id, dt=new_date)

        assert result is True

        # Verify deadline was updated
        updated_deadline = await service.get_by_id(
            sample_deadline.id, sample_deadline.user_id
        )
        assert updated_deadline is not None
        assert updated_deadline.deadline_at == new_date
        # Title should remain unchanged
        assert updated_deadline.title == sample_deadline.title

    @pytest.mark.asyncio
    async def test_update_deadline_not_found_raises_error(self, session, db_session):
        """Test updating non-existent deadline raises error"""
        service = DeadlineService(db_session)

        with pytest.raises(DeadlineNotFoundError):
            await service.update(deadline_id=99999, title="Updated Title")

    @pytest.mark.asyncio
    async def test_update_deadline_empty_title_raises_error(
        self, db_session, sample_deadline
    ):
        """Test updating deadline with empty title raises error"""
        service = DeadlineService(db_session)

        with pytest.raises(ValidationError):
            await service.update(deadline_id=sample_deadline.id, title="")

    @pytest.mark.asyncio
    async def test_update_deadline_past_date_raises_error(
        self, db_session, sample_deadline
    ):
        """Test updating deadline with past date raises error"""
        service = DeadlineService(db_session)

        with pytest.raises(InvalidDeadlineError):
            await service.update(
                deadline_id=sample_deadline.id, dt=datetime.now() - timedelta(days=1)
            )

    @pytest.mark.asyncio
    async def test_update_deadline_strips_title_whitespace(
        self, db_session, sample_deadline
    ):
        """Test updating deadline strips title whitespace"""
        service = DeadlineService(db_session)

        result = await service.update(
            deadline_id=sample_deadline.id, title="  Updated Title  "
        )

        assert result is True

        updated_deadline = await service.get_by_id(
            sample_deadline.id, sample_deadline.user_id
        )
        assert updated_deadline is not None
        assert updated_deadline.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_deadline_error(self, db_session, sample_deadline, caplog):
        """Test updating deadline with error"""
        service = DeadlineService(db_session)
        caplog.set_level(logging.ERROR)

        service.session_factory = MagicMock(side_effect=Exception("Test error"))

        with pytest.raises(Exception):
            await service.update(
                deadline_id=sample_deadline.id,
                title="Updated Title",
                dt=datetime.now() + timedelta(days=1),
            )

    def test_is_valid_timezone_valid_timezone(self):
        """Test valid timezone validation"""
        from services.deadline_service import is_valid_timezone

        assert is_valid_timezone("UTC") is True
        assert is_valid_timezone("Europe/Moscow") is True
        assert is_valid_timezone("America/New_York") is True

    def test_is_valid_timezone_invalid_timezone(self):
        """Test invalid timezone validation"""
        from services.deadline_service import is_valid_timezone

        assert is_valid_timezone("Invalid/Timezone") is False
        assert is_valid_timezone("Mars/Phobos") is False
        assert is_valid_timezone("") is False
        assert is_valid_timezone("NotATimezone") is False
