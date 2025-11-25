import dateparser
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from services.deadline_service import DeadlineService

from .fsm_add_deadline import AddDeadlineFSM

router = Router()
service = DeadlineService()


@router.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer("Welcome to the deadline bot!")


@router.message(F.text == "/add")
async def add_start(msg: Message, state: FSMContext):
    await msg.answer("Enter the title of the deadline:")
    await state.set_state(AddDeadlineFSM.title)


@router.message(AddDeadlineFSM.title)
async def add_title(msg: Message, state: FSMContext):
    await state.update_data(title=msg.text)
    await msg.answer("Введи дату в формате ДД.ММ.ГГГГ ЧЧ:ММ")
    await state.set_state(AddDeadlineFSM.datetime)


@router.message(AddDeadlineFSM.datetime)
async def add_datetime(msg: Message, state: FSMContext):
    dt = dateparser.parse(msg.text, settings={"PREFER_DATES_FROM": "future"})

    if not dt:
        await msg.anser("Не понял дату(")
        return

    from datetime import timezone

    dt = dt.replace(tzinfo=timezone.utc)

    data = await state.get_data()
    await service.create(user_id=msg.from_user.id, title=data["title"], dt=dt)

    await msg.answer(f"Дедлайн успешно добавлен! Сработает в {dt}")
    await state.clear()
