from aiogram.fsm.state import State, StatesGroup


class AddAddressState(StatesGroup):
    """Состояния для создания адреса"""

    address = State()
    detail = State()
    comment = State()


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


class CreateOrder(StatesGroup):
    """Состояния для создания заявки"""

    date = State()
    address = State()
    comment = State()


class YesOrNo(StatesGroup):
    """Вопрос уточнение да/нет"""

    question = State()


class ChangeOrder(StatesGroup):
    """Изменение заказа по типу или количеству контейнеров"""

    container_type = State()
    container_count = State()


class Courier(StatesGroup):
    """Отлов комментария к необработанной точке маршрута"""

    point = State()


class SMSEmail(StatesGroup):
    """Отлов кода из смс/email"""

    code = State()
