from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData


class CreateList(StatesGroup):
    waiting_for_messages = State()
    table_dump_ready = State()

class NumberCallback(CallbackData, prefix="num"):
    number: int

class RoleSelectCallback(CallbackData, prefix="select_role"):
    role: str