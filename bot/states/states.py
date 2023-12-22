from aiogram.fsm.state import State, StatesGroup


class AddAddressState(StatesGroup):
    """Состояния для создания адреса"""

    address = State()


class EditQuestionnaireState(StatesGroup):
    """Состояния для изменения анкеты пользователя"""

    first_name = State()
    last_name = State()
    phone_number = State()
    email = State()
    approve_phone = State()
    approve_email = State()


class RegistrationUser(StatesGroup):
    """Состояния для регистрации пользователей"""

    phone = State()

