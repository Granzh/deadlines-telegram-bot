import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from db.models import Deadline, NotificationSettings, SentNotification

from exceptions import (
    DatabaseError,
    NotificationError,
    ValidationError,
)

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_or_create_settings(self, user_id: int) -> NotificationSettings:
        """Get or create notification settings for user"""
        try:
            async with self.session_factory() as session:
                q = select(NotificationSettings).where(
                    NotificationSettings.user_id == user_id
                )
                res = await session.execute(q)
                settings = res.scalar_one_or_none()

                if not settings:
                    settings = NotificationSettings(user_id=user_id)
                    session.add(settings)
                    await session.commit()
                    await session.refresh(settings)
                    logger.info(f"Created notification settings for user {user_id}")

                return settings

        except Exception as e:
            logger.error(
                f"Failed to get/create notification settings for user {user_id}: {e}"
            )
            raise DatabaseError(f"Failed to get notification settings: {e}") from e

    async def update_settings(self, user_id: int, **kwargs) -> NotificationSettings:
        """Update notification settings for user"""
        try:
            # Validate kwargs
            valid_fields = {
                "notify_1_week",
                "notify_3_days",
                "notify_1_day",
                "notify_3_hours",
                "notify_1_hour",
            }

            invalid_fields = set(kwargs.keys()) - valid_fields
            if invalid_fields:
                raise ValidationError(f"Invalid fields: {invalid_fields}")

            async with self.session_factory() as session:
                q = select(NotificationSettings).where(
                    NotificationSettings.user_id == user_id
                )
                res = await session.execute(q)
                settings = res.scalar_one_or_none()

                if not settings:
                    settings = NotificationSettings(user_id=user_id, **kwargs)
                    session.add(settings)
                    logger.info(f"Created notification settings for user {user_id}")
                else:
                    for key, value in kwargs.items():
                        if hasattr(settings, key):
                            setattr(settings, key, value)
                    logger.info(f"Updated notification settings for user {user_id}")

                await session.commit()
                await session.refresh(settings)
                return settings

        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update notification settings for user {user_id}: {e}"
            )
            raise DatabaseError(f"Failed to update notification settings: {e}") from e

    async def get_deadlines_for_notifications(self) -> list[dict]:
        """Get all deadlines that need notifications"""
        try:
            async with self.session_factory() as session:
                now = datetime.now(timezone.utc)

                q = select(Deadline).where(Deadline.deadline_at > now)
                res = await session.execute(q)
                deadlines = list(res.scalars().all())

                logger.debug(f"Checking {len(deadlines)} deadlines for notifications")
                results = []

                for deadline in deadlines:
                    try:
                        settings_q = select(NotificationSettings).where(
                            NotificationSettings.user_id == deadline.user_id
                        )
                        settings_res = await session.execute(settings_q)
                        settings = settings_res.scalar_one_or_none()

                        if not settings:
                            logger.debug(
                                f"No notification settings for user {deadline.user_id}"
                            )
                            continue

                        # Ensure both datetimes are timezone-aware
                        deadline_time = deadline.deadline_at
                        if deadline_time.tzinfo is None:
                            deadline_time = deadline_time.replace(tzinfo=timezone.utc)

                        time_until = deadline_time - now
                        notifications_to_send = []

                        # Check different notification timeframes
                        notification_checks = [
                            (
                                settings.notify_1_week,
                                timedelta(days=7),
                                "1_week",
                                "За неделю",
                            ),
                            (
                                settings.notify_3_days,
                                timedelta(days=3),
                                "3_days",
                                "За 3 дня",
                            ),
                            (
                                settings.notify_1_day,
                                timedelta(days=1),
                                "1_day",
                                "За день",
                            ),
                            (
                                settings.notify_3_hours,
                                timedelta(hours=3),
                                "3_hours",
                                "За 3 часа",
                            ),
                            (
                                settings.notify_1_hour,
                                timedelta(hours=1),
                                "1_hour",
                                "За час",
                            ),
                        ]

                        for (
                            should_notify,
                            timeframe,
                            notif_type,
                            notif_text,
                        ) in notification_checks:
                            if (
                                should_notify
                                and timeframe
                                <= time_until
                                < timeframe + timedelta(minutes=2)
                            ):
                                if not await self._was_sent(deadline.id, notif_type):
                                    notifications_to_send.append(
                                        (notif_type, notif_text)
                                    )

                        for notif_type, notif_text in notifications_to_send:
                            results.append(
                                {
                                    "deadline": deadline,
                                    "type": notif_type,
                                    "text": notif_text,
                                    "settings": settings,
                                }
                            )

                    except Exception as e:
                        logger.error(f"Error processing deadline {deadline.id}: {e}")
                        continue

                logger.info(f"Found {len(results)} notifications to send")
                return results

        except Exception as e:
            logger.error(f"Failed to get deadlines for notifications: {e}")
            raise NotificationError(f"Failed to get notifications: {e}") from e

    async def _was_sent(self, deadline_id: int, notification_type: str) -> bool:
        """Check if notification was already sent"""
        try:
            async with self.session_factory() as session:
                q = select(SentNotification).where(
                    SentNotification.deadline_id == deadline_id,
                    SentNotification.notification_type == notification_type,
                )
                res = await session.execute(q)
                was_sent = res.scalar_one_or_none() is not None

                if was_sent:
                    logger.debug(
                        f"""Notification {notification_type} already
                        sent for deadline {deadline_id}
                        """
                    )

                return was_sent

        except Exception as e:
            logger.error(
                f"""Failed to check if notification
                was sent for deadline {deadline_id}: {e}
                """
            )
            # Return True to avoid duplicate notifications in case of error
            return True

    async def mark_as_sent(self, deadline_id: int, notification_type: str) -> None:
        """Mark notification as sent"""
        try:
            async with self.session_factory() as session:
                notification = SentNotification(
                    deadline_id=deadline_id, notification_type=notification_type
                )
                session.add(notification)
                await session.commit()
                logger.info(
                    f"""Marked notification {notification_type}
                    as sent for deadline {deadline_id}
                    """
                )

        except Exception as e:
            logger.error(
                f"Failed to mark notification as sent for deadline {deadline_id}: {e}"
            )
            raise NotificationError(f"Failed to mark notification as sent: {e}") from e
