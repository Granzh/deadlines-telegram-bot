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
/edit - редактировать дедлайн
/delete - удалить дедлайн

/notifications - настроить уведомления

💡 Система уведомлений поддерживает напоминания:
• При наступлении срока
• За 1 час
• За 3 часа
• За 1 день
• За 3 дня
• За неделю
"""


@help_router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(HELP_TEXT)
