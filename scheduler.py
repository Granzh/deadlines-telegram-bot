from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from services.deadline_service import DeadlineService
from services.notification_service import NotificationService
from db.session import Session

assert BOT_TOKEN is not None

bot = Bot(token=BOT_TOKEN)
deadline_service = DeadlineService(Session)
notification_service = NotificationService(Session)


async def check_deadlines():
    """Проверка просроченных дедлайнов"""
    deadlines = await deadline_service.get_due()
    for deadline in deadlines:
        await bot.send_message(
            deadline.user_id,
            f"🔥 Дедлайн *{deadline.title}* просрочен!\n\nСрок был: {deadline.deadline_at}",
        )


async def check_upcoming_deadlines():
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
            await bot.send_message(deadline.user_id, message)
            await notification_service.mark_as_sent(deadline.id, notif_type)
        except Exception as e:
            print(f"Error sending notification: {e}")


def setup_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(check_deadlines, "interval", minutes=1)
    scheduler.add_job(check_upcoming_deadlines, "interval", minutes=1)
    scheduler.start()
