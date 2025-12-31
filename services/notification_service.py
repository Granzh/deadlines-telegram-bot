from datetime import datetime, timedelta

from sqlalchemy import select

from db.models import Deadline, NotificationSettings, SentNotification
from db.session import Session


class NotificationService:
    async def get_or_create_settings(self, user_id: int):
        async with Session() as session:
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

            return settings

    async def update_settings(self, user_id: int, **kwargs):
        async with Session() as session:
            q = select(NotificationSettings).where(
                NotificationSettings.user_id == user_id
            )
            res = await session.execute(q)
            settings = res.scalar_one_or_none()

            if not settings:
                settings = NotificationSettings(user_id=user_id, **kwargs)
                session.add(settings)
            else:
                for key, value in kwargs.items():
                    if hasattr(settings, key):
                        setattr(settings, key, value)

            await session.commit()
            await session.refresh(settings)
            return settings

    async def get_deadlines_for_notifications(self):
        async with Session() as session:
            now = datetime.now()

            q = select(Deadline).where(Deadline.deadline_at > now)
            res = await session.execute(q)
            deadlines = res.scalars().all()

            results = []
            for deadline in deadlines:
                settings_q = select(NotificationSettings).where(
                    NotificationSettings.user_id == deadline.user_id
                )
                settings_res = await session.execute(settings_q)
                settings = settings_res.scalar_one_or_none()

                if not settings:
                    continue

                time_until = deadline.deadline_at - now

                notifications_to_send = []

                if settings.notify_1_week and timedelta(
                    days=7
                ) <= time_until < timedelta(days=7, minutes=2):
                    if not await self._was_sent(deadline.id, "1_week"):
                        notifications_to_send.append(("1_week", "За неделю"))

                if settings.notify_3_days and timedelta(
                    days=3
                ) <= time_until < timedelta(days=3, minutes=2):
                    if not await self._was_sent(deadline.id, "3_days"):
                        notifications_to_send.append(("3_days", "За 3 дня"))

                if settings.notify_1_day and timedelta(
                    days=1
                ) <= time_until < timedelta(days=1, minutes=2):
                    if not await self._was_sent(deadline.id, "1_day"):
                        notifications_to_send.append(("1_day", "За день"))

                if settings.notify_3_hours and timedelta(
                    hours=3
                ) <= time_until < timedelta(hours=3, minutes=2):
                    if not await self._was_sent(deadline.id, "3_hours"):
                        notifications_to_send.append(("3_hours", "За 3 часа"))

                if settings.notify_1_hour and timedelta(
                    hours=1
                ) <= time_until < timedelta(hours=1, minutes=2):
                    if not await self._was_sent(deadline.id, "1_hour"):
                        notifications_to_send.append(("1_hour", "За час"))

                for notif_type, notif_text in notifications_to_send:
                    results.append(
                        {
                            "deadline": deadline,
                            "type": notif_type,
                            "text": notif_text,
                            "settings": settings,
                        }
                    )

            return results

    async def _was_sent(self, deadline_id: int, notification_type: str) -> bool:
        async with Session() as session:
            q = select(SentNotification).where(
                SentNotification.deadline_id == deadline_id,
                SentNotification.notification_type == notification_type,
            )
            res = await session.execute(q)
            return res.scalar_one_or_none() is not None

    async def mark_as_sent(self, deadline_id: int, notification_type: str):
        async with Session() as session:
            notification = SentNotification(
                deadline_id=deadline_id, notification_type=notification_type
            )
            session.add(notification)
            await session.commit()
