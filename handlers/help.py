from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

help_router = Router()

HELP_TEXT = """
📌 Список доступных команд

/start – запуск бота
/help – список команд

/add - добавить новый дедлайн
/list - список дедлайнов
"""


@help_router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(HELP_TEXT)
