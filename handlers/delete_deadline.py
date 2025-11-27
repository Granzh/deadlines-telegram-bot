from operator import call

from aiogram import Router
from aiogram.types import CallbackQuery

from services.deadline_service import DeadlineService

delete_deadline_router = Router()

service = DeadlineService()


@delete_deadline_router.callback_query(lambda c: c.data.startswith("delete:"))
async def delete_deadline(callback: CallbackQuery):
    deadline_id = int(callback.data.split(":")[1])

    await service.delete(deadline_id)

    await callback.message.edit_text("Deadline deleted!")
    await callback.answer()
