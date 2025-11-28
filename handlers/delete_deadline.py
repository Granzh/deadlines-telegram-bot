from aiogram import Router
from aiogram.types import CallbackQuery

from services.deadline_service import DeadlineService

delete_deadline_router = Router()

service = DeadlineService()


@delete_deadline_router.callback_query(lambda c: c.data.startswith("delete:"))
async def delete_deadline(callback: CallbackQuery):
    try:
        deadline_id = int(callback.data.split(":", 1)[1])
    except:
        await callback.answer("Invalid deadline ID", show_alert=True)
        return

    ok = await service.delete(deadline_id)
    if not ok:
        await callback.answer("Failed to delete deadline", show_alert=True)
        return

    try:
        await callback.message.edit_text("Deadline deleted")
    except Exception:
        pass

    await callback.answer()
