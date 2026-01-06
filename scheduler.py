import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from services.deadline_service import DeadlineService
from services.notification_service import NotificationService

assert BOT_TOKEN is not None


logger = logging.getLogger(__name__)


async def check_deadlines(bot: Bot, deadline_service: DeadlineService):
    """Проверка просроченных дедлайнов"""
    deadlines = await deadline_service.get_due_unnotified()
    for deadline in deadlines:
        await bot.send_message(
            deadline.user_id,
            f"🔥 Дедлайн *{deadline.title}* просрочен!\n\nСрок был: {deadline.deadline_at}",
            parse_mode="Markdown",
        )
        await deadline_service.mark_overdue_notified(deadline.id)


async def check_upcoming_deadlines(bot: Bot, notification_service: NotificationService):
    """Проверка предстоящих дедлайнов и отправка напоминаний"""
    notifications = await notification_service.get_deadlines_for_notifications()

    for notif in notifications:
        deadline = notif["deadline"]
        notif_text = notif["text"]
        notif_type = notif["type"]

        message = (
            f"⏰ Напоминание!\n\n"
            f"*{deadline.title}*\n"
            f"Срок: {deadline.deadline_at}\n"
            f"Осталось: {notif_text}"
        )

        try:
            await bot.send_message(deadline.user_id, message, parse_mode="Markdown")
            await notification_service.mark_as_sent(deadline.id, notif_type)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")


_scheduler_instance = None


def setup_scheduler(
    bot: Bot,
    deadline_service: DeadlineService,
    notification_service: NotificationService,
):
    global _scheduler_instance
    _scheduler_instance = AsyncIOScheduler(timezone="UTC")
    _scheduler_instance.add_job(
        check_deadlines, "interval", minutes=1, args=[bot, deadline_service]
    )
    _scheduler_instance.add_job(
        check_upcoming_deadlines,
        "interval",
        minutes=1,
        args=[bot, notification_service],
    )
    _scheduler_instance.start()


def get_scheduler_instance():
    """Get the global scheduler instance"""
    return _scheduler_instance
