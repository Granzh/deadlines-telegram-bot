import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select

from db.models import Deadline, NotificationSettings, SentNotification
from exceptions import (
    NotificationError,
    ValidationError,
)
from services.notification_service import NotificationService


class TestNotificationService:
    """Test cases for NotificationService"""

    @pytest.mark.asyncio
    async def test_get_or_create_settings_creates_new(self, db_session, sample_user):
        """Test creating new notification settings"""
        service = NotificationService(db_session)

        settings = await service.get_or_create_settings(sample_user.id)

        assert settings.user_id == sample_user.id
        assert settings.notify_1_week is False
        assert settings.notify_3_days is False
        assert settings.notify_1_day is False
        assert settings.notify_3_hours is False
        assert settings.notify_1_hour is False

    @pytest.mark.asyncio
    async def test_get_or_create_settings_returns_existing(
        self, db_session, sample_notification_settings
    ):
        """Test returning existing notification settings"""
        service = NotificationService(db_session)

        settings = await service.get_or_create_settings(
            sample_notification_settings.user_id
        )

        assert settings.id == sample_notification_settings.id
        assert settings.user_id == sample_notification_settings.user_id

    @pytest.mark.asyncio
    async def test_get_or_create_settings_raise_exception(
        self, db_session, sample_user, caplog
    ):
        """Test raising infrastructure exception"""
        service = NotificationService(db_session)
        caplog.set_level(logging.ERROR)

        service.session_factory = Mock(side_effect=Exception("Something went wrong"))

        with pytest.raises(Exception):
            await service.get_or_create_settings(sample_user.id)

    @pytest_asyncio.fixture
    async def test_update_settings_existing_user(
        self, db_session, sample_notification_settings
    ):
        """Test updating settings for existing user"""
        service = NotificationService(db_session)

        settings = await service.update_settings(
            sample_notification_settings.user_id,
            notify_1_week=False,
            notify_3_hours=False,
        )

        assert settings.user_id == sample_notification_settings.user_id
        assert settings.notify_1_week is False
        assert settings.notify_3_days is False
        assert settings.notify_3_hours is False

    @pytest.mark.asyncio
    async def test_update_settings_new_user(self, db_session, sample_user):
        """Test updating settings for new user (creates new)"""
        service = NotificationService(db_session)

        settings = await service.update_settings(
            sample_user.id, notify_1_week=True, notify_1_day=True
        )

        assert settings.user_id == sample_user.id
        assert settings.notify_1_week is True
        assert settings.notify_1_day is True
        assert settings.notify_3_days is False  # default

    @pytest.mark.asyncio
    async def test_update_settings_invalid_field_raises_error(
        self, db_session, sample_user
    ):
        """Test updating with invalid field raises error"""
        service = NotificationService(db_session)

        with pytest.raises(ValidationError):
            await service.update_settings(
                sample_user.id,
                invalid_field=True,  # not a valid field
            )

    @pytest.mark.asyncio
    async def test_update_settings_existing(self, db_session, sample_user):
        """Test updating existing notification settings"""
        service = NotificationService(db_session)

        async with db_session() as session:
            settings = NotificationSettings(
                user_id=sample_user.id,
                notify_1_week=False,
                notify_3_days=False,
                notify_1_day=False,
                notify_3_hours=False,
                notify_1_hour=False,
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

            original_id = settings.id

        updated = await service.update_settings(
            sample_user.id,
            notify_1_week=True,
            notify_1_day=True,
        )

        assert updated.id == original_id
        assert updated.user_id == sample_user.id
        assert updated.notify_1_week is True
        assert updated.notify_1_day is True

        assert updated.notify_3_days is False
        assert updated.notify_3_hours is False
        assert updated.notify_1_hour is False

        async with db_session() as session:
            res = await session.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == sample_user.id
                )
            )
            db_settings = res.scalar_one()

            assert db_settings.id == original_id
            assert db_settings.notify_1_week is True
            assert db_settings.notify_1_day is True

    @pytest.mark.asyncio
    async def test_update_notification_error(self, db_session, caplog, sample_user):
        service = NotificationService(db_session)

        async with db_session() as session:
            settings = NotificationSettings(
                user_id=sample_user.id,
                notify_1_week=False,
                notify_3_days=False,
                notify_1_day=False,
                notify_3_hours=False,
                notify_1_hour=False,
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        caplog.set_level(logging.ERROR)

        service.session_factory = Mock(side_effect=Exception("Something went wrong"))

        with pytest.raises(Exception):
            await service.update_settings(
                user_id=sample_user.id,
                notify_1_week=True,
                notify_1_day=True,
                notify_3_days=True,
                notify_3_hours=True,
                notify_1_hour=True,
            )

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_empty(self, db_session):
        """Test getting notifications when no deadlines exist"""
        service = NotificationService(db_session)

        notifications = await service.get_deadlines_for_notifications()

        assert notifications == []

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_with_deadlines(
        self, db_session, sample_deadline, sample_notification_settings
    ):
        """Test getting notifications for deadlines"""
        service = NotificationService(db_session)

        # Create a deadline that should trigger notifications
        async with db_session() as session:
            # Create deadline due in 1 hour
            deadline_1h = Deadline(
                user_id=sample_deadline.user_id,
                title="Due in 1 hour",
                deadline_at=datetime.now(timezone.utc) + timedelta(hours=1, minutes=1),
            )
            session.add(deadline_1h)

            # Create deadline due in 1 day
            deadline_1d = Deadline(
                user_id=sample_deadline.user_id,
                title="Due in 1 day",
                deadline_at=datetime.now(timezone.utc) + timedelta(days=1, minutes=1),
            )
            session.add(deadline_1d)

            await session.commit()

        notifications = await service.get_deadlines_for_notifications()

        # Should find notifications for both deadlines
        assert len(notifications) >= 2

        # Check structure of notification data
        for notification in notifications:
            assert "deadline" in notification
            assert "type" in notification
            assert "text" in notification
            assert "settings" in notification
            assert notification["deadline"].title in ["Due in 1 hour", "Due in 1 day"]

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_no_settings(
        self, db_session, sample_deadline
    ):
        """Test getting notifications when user has no settings"""
        service = NotificationService(db_session)

        # Create a deadline that would trigger notification if settings existed
        async with db_session() as session:
            deadline_1h = Deadline(
                user_id=sample_deadline.user_id,
                title="Due in 1 hour",
                deadline_at=datetime.now(timezone.utc) + timedelta(hours=1, minutes=1),
            )
            session.add(deadline_1h)
            await session.commit()

        notifications = await service.get_deadlines_for_notifications()

        # Should be empty because no notification settings
        assert notifications == []

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_already_sent(
        self, db_session, sample_deadline, sample_notification_settings
    ):
        """Test that already sent notifications are not returned"""
        service = NotificationService(db_session)

        # Create a deadline and mark notification as sent
        async with db_session() as session:
            deadline_1h = Deadline(
                user_id=sample_deadline.user_id,
                title="Due in 1 hour",
                deadline_at=datetime.now(timezone.utc) + timedelta(hours=1, minutes=1),
            )
            session.add(deadline_1h)
            await session.commit()
            await session.refresh(deadline_1h)

            # Mark as already sent
            sent_notification = SentNotification(
                deadline_id=deadline_1h.id, notification_type="1_hour"
            )
            session.add(sent_notification)
            await session.commit()

        notifications = await service.get_deadlines_for_notifications()

        # Should not include the already sent notification
        hour_notifications = [n for n in notifications if n["type"] == "1_hour"]
        assert len(hour_notifications) == 0

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_different_timeframes(
        self, db_session, sample_user
    ):
        """Test notifications for different timeframes"""
        service = NotificationService(db_session)

        # Create notification settings for all timeframes
        await service.update_settings(
            sample_user.id,
            notify_1_week=True,
            notify_3_days=True,
            notify_1_day=True,
            notify_3_hours=True,
            notify_1_hour=True,
        )

        # Create deadlines at different timeframes
        async with db_session() as session:
            deadlines_data = [
                ("1 week", datetime.now(timezone.utc) + timedelta(days=7, minutes=1)),
                ("3 days", datetime.now(timezone.utc) + timedelta(days=3, minutes=1)),
                ("1 day", datetime.now(timezone.utc) + timedelta(days=1, minutes=1)),
                ("3 hours", datetime.now(timezone.utc) + timedelta(hours=3, minutes=1)),
                ("1 hour", datetime.now(timezone.utc) + timedelta(hours=1, minutes=1)),
            ]

            for title, deadline_at in deadlines_data:
                deadline = Deadline(
                    user_id=sample_user.id, title=title, deadline_at=deadline_at
                )
                session.add(deadline)

            await session.commit()

        notifications = await service.get_deadlines_for_notifications()

        # Should find notifications for all timeframes
        notification_types = {n["type"] for n in notifications}
        expected_types = {"1_week", "3_days", "1_day", "3_hours", "1_hour"}
        assert notification_types == expected_types

    @pytest.mark.asyncio
    async def test_was_sent_true(self, db_session, sample_deadline):
        """Test checking if notification was sent - already sent"""
        service = NotificationService(db_session)

        # Mark notification as sent
        async with db_session() as session:
            sent_notification = SentNotification(
                deadline_id=sample_deadline.id, notification_type="1_hour"
            )
            session.add(sent_notification)
            await session.commit()

        result = await service._was_sent(sample_deadline.id, "1_hour")

        assert result is True

    @pytest.mark.asyncio
    async def test_was_sent_false(self, db_session, sample_deadline):
        """Test checking if notification was sent - not sent"""
        service = NotificationService(db_session)

        result = await service._was_sent(sample_deadline.id, "1_hour")

        assert result is False

    @pytest.mark.asyncio
    async def test_was_sent_different_type(self, db_session, sample_deadline):
        """Test checking different notification type"""
        service = NotificationService(db_session)

        # Mark 1_hour notification as sent
        async with db_session() as session:
            sent_notification = SentNotification(
                deadline_id=sample_deadline.id, notification_type="1_hour"
            )
            session.add(sent_notification)
            await session.commit()

        # Check for 1_day notification
        result = await service._was_sent(sample_deadline.id, "1_day")

        assert result is False

    @pytest.mark.asyncio
    async def test_mark_was_sent_error(self, db_session, sample_deadline):
        """Test marking notification as sent with error"""
        service = NotificationService(db_session)

        service.session_factory = Mock(side_effect=Exception("Something went wrong"))

        with pytest.raises(Exception):
            await service.mark_as_sent(sample_deadline.id, "1_hour")

        # Verify it was not marked
        result = await service._was_sent(sample_deadline.id, "1_hour")
        assert result is True

        # Verify record does not exist in database
        from sqlalchemy import select

        from db.models import SentNotification

        async with db_session() as session:
            q = select(SentNotification).where(
                SentNotification.deadline_id == sample_deadline.id,
                SentNotification.notification_type == "1_hour",
            )
            sent_record = await session.execute(q)
            assert sent_record.scalar_one_or_none() is None

    @pytest.mark.asyncio
    async def test_mark_as_sent(self, db_session, sample_deadline):
        """Test marking notification as sent"""
        service = NotificationService(db_session)

        await service.mark_as_sent(sample_deadline.id, "1_hour")

        # Verify it was marked
        result = await service._was_sent(sample_deadline.id, "1_hour")
        assert result is True

        # Verify record exists in database
        from sqlalchemy import select

        from db.models import SentNotification

        async with db_session() as session:
            q = select(SentNotification).where(
                SentNotification.deadline_id == sample_deadline.id,
                SentNotification.notification_type == "1_hour",
            )
            sent_record = await session.execute(q)
            assert sent_record.scalar_one_or_none() is not None

    @pytest.mark.asyncio
    async def test_mark_as_sent_multiple_types(self, db_session, sample_deadline):
        """Test marking multiple notification types as sent"""
        service = NotificationService(db_session)

        await service.mark_as_sent(sample_deadline.id, "1_hour")
        await service.mark_as_sent(sample_deadline.id, "1_day")

        # Verify both were marked
        assert await service._was_sent(sample_deadline.id, "1_hour") is True
        assert await service._was_sent(sample_deadline.id, "1_day") is True

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_handles_deadline_errors(
        self, db_session, sample_user, caplog
    ):
        service = NotificationService(db_session)
        caplog.set_level(logging.ERROR)

        now = datetime.now(timezone.utc)

        deadline = Deadline(
            user_id=sample_user.id,
            title="Test deadline",
            deadline_at=now + timedelta(days=1, seconds=10),
        )

        settings = NotificationSettings(
            user_id=sample_user.id,
            notify_1_day=True,
        )

        async with db_session() as session:
            session.add_all([deadline, settings])
            await session.commit()

        with patch.object(service, "_was_sent", side_effect=Exception("Test error")):
            notifications = await service.get_deadlines_for_notifications()

        assert notifications == []

        assert any(
            "Error processing deadline" in record.message for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_get_deadlines_for_notifications_error_handling(
        self, db_session, caplog
    ):
        caplog.set_level(logging.ERROR)

        service = NotificationService(db_session)

        service.session_factory = MagicMock(side_effect=Exception("Database error"))

        with pytest.raises(NotificationError):
            await service.get_deadlines_for_notifications()

        assert any(
            "Failed to get notifications" in record.message
            or "Failed to get deadlines for notifications" in record.message
            for record in caplog.records
        )
