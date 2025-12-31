import dateparser
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from handlers.fsm_add_deadline import AddDeadlineFSM
from services.deadline_service import DeadlineService

router = Router()
service = DeadlineService()


@router.message(Command("add"))
async def add_start(msg: Message, state: FSMContext):
    await msg.answer("Enter the title of the deadline:")
    await state.set_state(AddDeadlineFSM.title)


@router.message(Command("list"))
async def list_deadlines(msg: Message):
    deadlines = await service.list_for_user(msg.from_user.id)

    if not deadlines:
        await msg.answer("Нет дедлайнов!")
        return

    text_lines = ["Твои дедлайны:", " "]

    for i, d in enumerate(deadlines, start=1):
        status = "Не горит"
        text_lines.append(
            f"*{i}.* {status} *{d.title} \n{d.deadline_at.strftime('%d.%m.%Y %H:%M')}"
        )

    await msg.answer("\n".join(text_lines))


@router.message(Command("delete"))
async def delete_deadline_command(msg: Message):
    deadlines = await service.list_for_user(msg.from_user.id)

    if not deadlines:
        await msg.answer("Нет дедлайнов для удаления!")
        return

    text_lines = ["Выбери дедлайн для удаления:", " "]
    buttons = []

    for i, d in enumerate(deadlines, start=1):
        status = "⏰"
        text_lines.append(f"{i}. {status} {d.title} - {d.deadline_at}")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ {i}. {d.title}", callback_data=f"delete:{d.id}"
                )
            ]
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await msg.answer("\n".join(text_lines), reply_markup=keyboard)


@router.message(AddDeadlineFSM.title)
async def add_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Введи дату в формате ДД.ММ.ГГГГ ЧЧ:ММ")
    await state.set_state(AddDeadlineFSM.datetime)


@router.message(AddDeadlineFSM.datetime)
async def add_datetime(msg: Message, state: FSMContext):
    dt = dateparser.parse(msg.text, settings={"PREFER_DATES_FROM": "future"})

    if not dt:
        await msg.answer("Не понял дату(")
        return

    from datetime import timezone

    dt = dt.replace(tzinfo=timezone.utc)

    data = await state.get_data()
    await service.create(user_id=msg.from_user.id, title=data["title"], dt=dt)

    await msg.answer(f"Дедлайн успешно добавлен! Сработает в {dt}")
    await state.clear()
