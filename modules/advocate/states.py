from aiogram.fsm.state import State, StatesGroup

class AdvocateState(StatesGroup):
    waiting_for_players_list = State()
    active_session = State()
