from aiogram.fsm.state import State, StatesGroup
from aiogram.filters.callback_data import CallbackData


class RevealState(StatesGroup):
    waiting_for_number_or_forward = State()

class RoleCallback(CallbackData, prefix="role"):
    role_key: str

class NumberCallback(CallbackData, prefix="num"):
    number: int

class TemplateSelectCallback(CallbackData, prefix="select_tmpl"):
    idx: int