from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN
from services.deadline_service import DeadlineService

bot = Bot(token=BOT_TOKEN)
service = DeadlineService()


async def check_deadlines():
    deadlines = await service.get_due()
    for deadline in deadlines:
        await bot.send_message(
            deadline.user_id, f"Your deadline {deadline.title} is overdue!"
        )
        await service.mark_notified(deadline.id)


def setup_scheduler():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(check_deadlines, "interval", minutes=1)
    scheduler.start()
