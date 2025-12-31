from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Deadline(Base):
    __tablename__ = "deadlines"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String)
    deadline_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True)
    notify_on_due: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_1_hour: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_3_hours: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_1_day: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_3_days: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_1_week: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class SentNotification(Base):
    __tablename__ = "sent_notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    deadline_id: Mapped[int] = mapped_column(Integer, ForeignKey("deadlines.id"))
    notification_type: Mapped[str] = mapped_column(String)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
