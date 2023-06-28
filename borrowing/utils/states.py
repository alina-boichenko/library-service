from aiogram.dispatcher.filters.state import State, StatesGroup


class LibraryStates(StatesGroup):
    START = State()
    EMAIL = State()
