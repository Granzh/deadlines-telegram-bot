from aiogram import Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from db.session import Session
from services.notification_service import NotificationService

notifications_router = Router()
service = NotificationService(Session)


@notifications_router.message(Command("notifications"))
async def notifications_command(msg: Message):
    settings = await service.get_or_create_settings(msg.from_user.id)

    text = "⚙️ *Настройки уведомлений*\n\n"
    text += "Выбери, когда хочешь получать напоминания:\n\n"

    text += f"{'✅' if settings.notify_on_due else '❌'} При наступлении срока\n"
    text += f"{'✅' if settings.notify_1_hour else '❌'} За 1 час\n"
    text += f"{'✅' if settings.notify_3_hours else '❌'} За 3 часа\n"
    text += f"{'✅' if settings.notify_1_day else '❌'} За 1 день\n"
    text += f"{'✅' if settings.notify_3_days else '❌'} За 3 дня\n"
    text += f"{'✅' if settings.notify_1_week else '❌'} За неделю\n"

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_on_due else '❌'} При наступлении",
                callback_data="notif_toggle:notify_on_due",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_1_hour else '❌'} За 1 час",
                callback_data="notif_toggle:notify_1_hour",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_3_hours else '❌'} За 3 часа",
                callback_data="notif_toggle:notify_3_hours",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_1_day else '❌'} За 1 день",
                callback_data="notif_toggle:notify_1_day",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_3_days else '❌'} За 3 дня",
                callback_data="notif_toggle:notify_3_days",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_1_week else '❌'} За неделю",
                callback_data="notif_toggle:notify_1_week",
            )
        ],
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer(text, reply_markup=keyboard)


@notifications_router.callback_query(lambda c: c.data.startswith("notif_toggle:"))
async def toggle_notification(callback: CallbackQuery):
    assert callback.data is not None
    field = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    settings = await service.get_or_create_settings(user_id)
    current_value = getattr(settings, field)

    await service.update_settings(user_id, **{field: not current_value})

    settings = await service.get_or_create_settings(user_id)

    text = "⚙️ *Настройки уведомлений*\n\n"
    text += "Выбери, когда хочешь получать напоминания:\n\n"

    text += f"{'✅' if settings.notify_on_due else '❌'} При наступлении срока\n"
    text += f"{'✅' if settings.notify_1_hour else '❌'} За 1 час\n"
    text += f"{'✅' if settings.notify_3_hours else '❌'} За 3 часа\n"
    text += f"{'✅' if settings.notify_1_day else '❌'} За 1 день\n"
    text += f"{'✅' if settings.notify_3_days else '❌'} За 3 дня\n"
    text += f"{'✅' if settings.notify_1_week else '❌'} За неделю\n"

    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_on_due else '❌'} При наступлении",
                callback_data="notif_toggle:notify_on_due",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_1_hour else '❌'} За 1 час",
                callback_data="notif_toggle:notify_1_hour",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_3_hours else '❌'} За 3 часа",
                callback_data="notif_toggle:notify_3_hours",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_1_day else '❌'} За 1 день",
                callback_data="notif_toggle:notify_1_day",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_3_days else '❌'} За 3 дня",
                callback_data="notif_toggle:notify_3_days",
            )
        ],
        [
            InlineKeyboardButton(
                text=f"{'✅' if settings.notify_1_week else '❌'} За неделю",
                callback_data="notif_toggle:notify_1_week",
            )
        ],
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(text, reply_markup=keyboard)
    except Exception:
        pass

    await callback.answer("Настройка обновлена!")
