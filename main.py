import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN
from db.session import init_db
from handlers.base_handlers import router
from handlers.delete_deadline import delete_deadline_router
from handlers.help import help_router
from handlers.start_router import start_router
from scheduler import setup_scheduler


async def main():
    bot = Bot(BOT_TOKEN)
    dp = Dispatcher()

    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Список команд"),
        BotCommand(command="add", description="Добавить дедлайн"),
        BotCommand(command="list", description="Список дедлайнов"),
        BotCommand(command="delete", description="Удалить дедлайн"),
    ]

    dp.include_router(router)
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(delete_deadline_router)

    await bot.set_my_commands(commands)

    await init_db()
    setup_scheduler()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
