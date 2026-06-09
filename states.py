from aiogram.fsm.state import State, StatesGroup

class SearchStates(StatesGroup):
    choosing_mode = State()
    choosing_genre = State()
    entering_actor = State()
    choosing_studio = State()
    showing_results = State()
