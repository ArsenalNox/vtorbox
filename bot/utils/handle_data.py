import datetime
import pprint
import uuid

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.utils.messages import MESSAGES

fullname_pattern = r"^[а-яА-ЯёЁ\s]+$"
phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
HEADERS = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiNDNmOTZiN2MtYzQxNy00YmUxLTliZTgtODU3YmY5ZGY4YWNiIiwic2NvcGVzIjpbImN1c3RvbWVyIiwiYWRtaW4iLCJtYW5hZ2VyIiwiY291cmllciIsImJvdCJdfQ.aKUiidy6ZQ18QdLeEs8cvHkFjft9wV7eCnzMVObMXqQ'
}


def validate_date(user_date: str) -> bool:
    """Валидация даты при создании заказа"""

    try:
        if datetime.datetime.strptime(user_date, '%d-%m-%Y') or datetime.datetime.strptime(user_date, '%d.%m.%Y'):
            return True
    except ValueError:
        return False


def get_order_data(date_text: str) -> str:
    """В зависимости от тектового значения даты преобразуем в дату datetime"""

    if date_text == 'сегодня':
        date = datetime.datetime.now().strftime('%d-%m-%Y')

    elif date_text == 'завтра':
        date = datetime.datetime.now() + datetime.timedelta(days=1)
        date = date.strftime('%d-%m-%Y')

    else:
        date = datetime.datetime.now() + datetime.timedelta(days=2)
        date = date.strftime('%d-%m-%Y')

    return str(date)


async def show_active_orders(self: 'TextHandler', message: Message, orders: list[dict], state: FSMContext):
    """Показ сообщения с активными заявками"""

    first_order = orders[0]
    await state.set_state(state=None)
    msg = await message.answer(
        MESSAGES['YOU_HAVE_ACTIVE_ORDERS'].format(
            len(orders)
        ),
        reply_markup=self.kb.show_btn(first_order)
    )

    await state.update_data(msg=msg.message_id)


async def show_order_info(self: 'OrderHandler', message: Message, order: dict, state: FSMContext):
    """Вывод 1 конкретной заявки"""

    data = await state.get_data()

    # удаляем клавиатуру у сообщений с историями заявок
    if data.get('msg_order_history'):
        await message.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg_order_history'),
            reply_markup=None
        )

        await state.update_data(msg_order_history=None)

    date = convert_date(order.get('day'))
    order_msg = await message.answer(
        MESSAGES['ORDER_INFO'].format(
            order.get('order_num'),
            order.get('address_data', {}).get('address'),
            date,
            order.get('status_data', {}).get('status_name') + f'({order.get("status_data", {}).get("description")})',
            order.get('box_data', {}).get('box_name'),
            order.get('box_count'),
            '100'

        ),
        reply_markup=self.kb.order_menu_btn(order, self.orders_list, self.index)
    )
    await state.update_data(order_msg=order_msg.message_id)
    await state.update_data(order_msg_text=order_msg.text)


def translate_month(eng_month: str) -> str:
    """Перевод названий месяцев"""

    eng_month = eng_month.lower()
    months = {
        'january': 'Январь',
        'february': 'Февраль',
        'march': 'Март',
        'april': 'Апрель',
        'may': 'Май',
        'june': 'Июнь',
        'july': 'Июль',
        'august': 'Август',
        'september': 'Сентябрь',
        'october': 'Октябрь',
        'november': 'Ноябрь',
        'december': 'Декабрь'
    }

    return months[eng_month]


def translate_day(eng_day: str) -> str:
    """Перевод названий дней"""

    days = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье',
    }

    return days[eng_day]

async def group_orders_by_month(orders_list: list[dict]):
    """Группируем заявки по месяцу"""

    result = {}

    for order in orders_list:
        try:
            datetime_obj = datetime.datetime.strptime(order.get('day'), '%Y-%m-%dT%H:%M:%S')
        except Exception:
            datetime_obj = datetime.datetime.strptime(order.get('day'), '%Y-%m-%dT%H:%M:%S.%f')
        ru_month = translate_month(datetime_obj.strftime('%B')).lower()

        group = f'{ru_month} {datetime_obj.year}'
        if group not in result:
            result[group] = [str(order.get('order_num'))]
        else:
            result[group].append(str(order.get('order_num')))

    return result


def convert_date(date: str) -> str:
    """Преобразовываем дату в формат дд-мм-год """
    try:
        date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    except Exception:
        date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
    date = date_time_obj.strftime('%d-%m-%Y')

    return date


async def show_address_list(self: 'AddressHandler', message: Message, state: FSMContext, address_list: list[dict]):
    """Отображение списка адресов с кнопками(по умолчанию/удалить)"""

    msg = await message.answer(
        MESSAGES['ADD_ADDRESS'],
        reply_markup=self.kb.add_address_btn(self.flag_to_return)
    )
    await state.update_data(msg=msg.message_id)
    msg_ids = {}
    count = 1  # счетчик для порядкового номера адресов
    # отправляем все адреса пользователя с кнопками ('Удалить' и 'По умолчанию')
    # в зависимости от адреса выводим как дефолтный или обычный
    for address in address_list:
        address_text = address.get('address') + address.get('detail', ' ') if address.get('detail') else address.get(
            'address')
        if address['main']:
            msg = await message.answer(
                MESSAGES['ADDRESS_INFO_DEDAULT'].format(
                    count,
                    address_text
                ),
                reply_markup=self.kb.address_delete_default_btn(address)
            )
        else:
            msg = await message.answer(
                MESSAGES['ADDRESS_INFO_NOT_DEDAULT'].format(
                    count,
                    address_text
                ),
                reply_markup=self.kb.address_delete_default_btn(address)
            )
        count += 1
        msg_ids[address['id']] = msg.message_id

    await state.update_data(msg_ids=msg_ids)