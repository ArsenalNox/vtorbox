from aiogram.fsm.state import State, StatesGroup


class AddAddressState(StatesGroup):
    """Состояния для создания адреса"""

    address = State()
