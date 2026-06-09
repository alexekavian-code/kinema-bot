from aiogram.fsm.state import State, StatesGroup


class SearchStates(StatesGroup):
    choosing_mode = State()
    choosing_genre = State()
    entering_actor = State()
    choosing_studio = State()
    choosing_country = State()
    choosing_decade = State()
    entering_search = State()
    showing_results = State()
    showing_favorites = State()
