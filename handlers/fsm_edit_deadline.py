from aiogram.fsm.state import State, StatesGroup


class EditDeadlineFSM(StatesGroup):
    choose_field = State()
    edit_title = State()
    edit_datetime = State()
