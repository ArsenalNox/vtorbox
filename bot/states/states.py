from aiogram.fsm.state import State, StatesGroup


class AddAddressState(StatesGroup):
    """Состояния для создания адреса"""

    address = State()


class EditQuestionnaireState(StatesGroup):
    """Состояния для изменения анкеты пользователя"""

    fullname = State()
    comment = State()
    phone_number = State()
    email = State()
