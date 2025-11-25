import asyncio

from aiogram import Bot, Dispatcher

from bot.handlers import router
from config import BOT_TOKEN
from db.session import init_db
from scheduler import setup_scheduler


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    await init_db()
    setup_scheduler()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
