import dateparser
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from handlers.fsm_edit_deadline import EditDeadlineFSM
from services.deadline_service import DeadlineService
from utils.error_handler import handle_errors
from db.session import Session

edit_deadline_router = Router()
service = DeadlineService(Session)


@edit_deadline_router.message(Command("edit"))
@handle_errors("Ошибка при загрузке дедлайнов")
async def edit_deadline_command(msg: Message):
    """Handle edit command - show list of deadlines to edit"""
    assert msg.from_user is not None
    deadlines = await service.list_for_user(msg.from_user.id)

    if not deadlines:
        await msg.answer("У вас нет дедлайнов для редактирования!")
        return

    text_lines = ["Выбери дедлайн для редактирования:", " "]
    buttons = []

    for i, d in enumerate(deadlines, start=1):
        status = "⏰"
        text_lines.append(f"{i}. {status} {d.title} - {d.deadline_at}")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ {i}. {d.title}", callback_data=f"edit:{d.id}"
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer("\n".join(text_lines), reply_markup=keyboard)


@edit_deadline_router.callback_query(lambda c: c.data.startswith("edit:"))
async def choose_edit_field(callback: CallbackQuery, state: FSMContext):
    try:
        deadline_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer("Invalid deadline ID", show_alert=True)
        return

    deadline = await service.get_by_id(deadline_id, callback.from_user.id)
    if not deadline:
        await callback.answer("Deadline not found", show_alert=True)
        return

    await state.update_data(deadline_id=deadline_id)

    buttons = [
        [
            InlineKeyboardButton(
                text="📝 Изменить название", callback_data="edit_field:title"
            )
        ],
        [
            InlineKeyboardButton(
                text="📅 Изменить дату", callback_data="edit_field:datetime"
            )
        ],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="edit_field:cancel")],
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    try:
        await callback.message.edit_text(
            f"Что хочешь изменить в дедлайне?\n\n"
            f"*{deadline.title}*\n"
            f"Срок: {deadline.deadline_at}",
            reply_markup=keyboard,
        )
    except Exception:
        await callback.message.answer(
            f"Что хочешь изменить в дедлайне?\n\n"
            f"*{deadline.title}*\n"
            f"Срок: {deadline.deadline_at}",
            reply_markup=keyboard,
        )

    await callback.answer()
    await state.set_state(EditDeadlineFSM.choose_field)


@edit_deadline_router.callback_query(lambda c: c.data.startswith("edit_field:"))
async def process_field_choice(callback: CallbackQuery, state: FSMContext):
    field = callback.data.split(":", 1)[1]

    if field == "cancel":
        await state.clear()
        try:
            await callback.message.edit_text("Редактирование отменено")
        except Exception:
            await callback.message.answer("Редактирование отменено")
        await callback.answer()
        return

    if field == "title":
        try:
            await callback.message.edit_text("Введи новое название дедлайна:")
        except Exception:
            await callback.message.answer("Введи новое название дедлайна:")
        await state.set_state(EditDeadlineFSM.edit_title)
    elif field == "datetime":
        try:
            await callback.message.edit_text(
                "Введи новую дату в формате ДД.ММ.ГГГГ ЧЧ:ММ:"
            )
        except Exception:
            await callback.message.answer(
                "Введи новую дату в формате ДД.ММ.ГГГГ ЧЧ:ММ:"
            )
        await state.set_state(EditDeadlineFSM.edit_datetime)

    await callback.answer()


@edit_deadline_router.message(EditDeadlineFSM.edit_title)
async def process_new_title(msg: Message, state: FSMContext):
    data = await state.get_data()
    deadline_id = data.get("deadline_id")

    if not deadline_id:
        await msg.answer("Ошибка: дедлайн не найден")
        await state.clear()
        return

    ok = await service.update(deadline_id, title=msg.text)
    if ok:
        await msg.answer(f"Название успешно изменено на: *{msg.text}*")
    else:
        await msg.answer("Не удалось обновить дедлайн")

    await state.clear()


@edit_deadline_router.message(EditDeadlineFSM.edit_datetime)
async def process_new_datetime(msg: Message, state: FSMContext):
    dt = dateparser.parse(msg.text, settings={"PREFER_DATES_FROM": "future"})

    if not dt:
        await msg.answer("Не понял дату(")
        return

    from datetime import timezone

    dt = dt.replace(tzinfo=timezone.utc)

    data = await state.get_data()
    deadline_id = data.get("deadline_id")

    if not deadline_id:
        await msg.answer("Ошибка: дедлайн не найден")
        await state.clear()
        return

    ok = await service.update(deadline_id, dt=dt)
    if ok:
        await msg.answer(f"Дата успешно изменена на: {dt}")
    else:
        await msg.answer("Не удалось обновить дедлайн")

    await state.clear()
