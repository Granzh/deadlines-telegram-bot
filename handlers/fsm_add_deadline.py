from aiogram.fsm.state import State, StatesGroup


class AddDeadlineFSM(StatesGroup):
    title = State()
    datetime = State()
