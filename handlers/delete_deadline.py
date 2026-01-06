from aiogram import Router
from aiogram.types import CallbackQuery

from exceptions import (
    CallbackDataError,
)
from services.deadline_service import DeadlineService
from utils.error_handler import handle_callback_errors

delete_deadline_router = Router()


@delete_deadline_router.callback_query(lambda c: c.data.startswith("delete:"))
@handle_callback_errors("Ошибка при удалении дедлайна")
async def delete_deadline(callback: CallbackQuery, deadline_service: DeadlineService):
    """Handle deadline deletion"""
    if not callback.data or ":" not in callback.data:
        raise CallbackDataError(callback.data or "empty")

    try:
        deadline_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        raise CallbackDataError(f"Invalid deadline ID: {callback.data}")

    await deadline_service.delete(deadline_id, callback.from_user.id)

    # Try to edit the message, but don't fail if we can't
    if callback.message and hasattr(callback.message, "edit_text"):
        try:
            await callback.message.edit_text("✅ Дедлайн удален", parse_mode="Markdown")
        except Exception:
            # Message might be too old or already edited
            pass

    await callback.answer("Дедлайн удален", parse_mode="Markdown")
