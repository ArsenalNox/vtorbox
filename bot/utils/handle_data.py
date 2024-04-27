import datetime
import pprint
import uuid
from typing import Union

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states.states import CreateOrder
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api

fullname_pattern = r"^[а-яА-ЯёЁ\s]+$"
phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


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

    status_code, active_order_msg = await req_to_api(
        method='get',
        url='bot/messages?message_key=YOU_HAVE_ACTIVE_ORDERS'
    )

    msg = await message.answer(
        active_order_msg.format(
            len(orders)
        ),
        reply_markup=self.kb.show_btn(first_order)
    )

    await state.update_data(msg=msg.message_id)


async def show_order_info(self: 'OrderHandler', message: Message, order: dict, state: FSMContext):
    """Вывод 1 конкретной заявки"""


    data = await state.get_data()

    if data.get('order_msg'):
        await message.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('order_msg')
        )
        await state.update_data(order_msg=None)

    # удаляем клавиатуру у сообщений с историями заявок
    if data.get('msg_order_history'):
        await message.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg_order_history'),
            reply_markup=None
        )

        await state.update_data(msg_order_history=None)

    date = convert_date(order.get('day'))
    created_at = convert_date(order.get('date_created'))
    if order.get('box_data') and order.get('box_count'):
        box_count = order.get('box_count', 'Не задано')
        box_name = order.get('box_data', {}).get('box_name', 'Не задано')
        order_sum = f"{int(order.get('box_data', {}).get('pricing_default')) * int(order.get('box_count'))} руб."
    else:
        order_sum = 'Рассчитывается...'
        box_count = 'Не задано'
        box_name = 'Не задано'

    order_comment = order.get('comment')
    address_comment = order.get('address_data', {}).get('comment')

    status_code, order_info_msg = await req_to_api(
        method='get',
        url='bot/messages?message_key=ORDER_INFO'
    )
    order_msg = await message.answer(
        order_info_msg.format(
            order.get('order_num'),
            order.get('address_data', {}).get('address'),
            address_comment if address_comment != 'Без комментария' else '-',
            date,
            order_comment if order_comment != 'Без комментария' else '-',
            order.get('status_data', {}).get('status_name') + f'({order.get("status_data", {}).get("description", "")})',
            box_name,
            box_count,
            order_sum,
            created_at

        ),
        reply_markup=self.kb.order_menu_btn(order, self.orders_list, self.index)
    )
    await state.update_data(order_msg=order_msg.message_id)
    await state.update_data(order_msg_text=order_msg.text)


async def show_courier_order(order_id, order: dict, message: Message, self: 'CourierHandler', state: FSMContext):
    if order.get('box_data') and order.get('box_count'):
        box_count = order.get('box_count', 'Не задано')
        box_name = order.get('box_data', {}).get('box_name', 'Не задано')
    else:
        box_count = 'Не задано'
        box_name = 'Не задано'

    status_code, route_info_msg = await req_to_api(
        method='get',
        url='bot/messages?message_key=ROUTE_INFO'
    )

    status_code, back_routes_msg = await req_to_api(
        method='get',
        url='bot/messages?message_key=BACK_TO_ROUTES'
    )

    msg = await message.answer(
        route_info_msg.format(
            order.get('order_num'),
            order.get('address_data', {}).get('address'),
            order.get('user_data', {}).get('firstname') + ' ' + order.get('user_data', {}).get('secondname'),
            order.get('user_data', {}).get('phone_number') if order.get('user_data', {}).get(
                'phone_number') else 'Не указан',
            box_name,
            box_count
        ),
        reply_markup=self.kb.points_menu_btn(order_id)
    )
    await state.update_data(msg=msg.message_id)

    await message.answer(
        back_routes_msg,
        reply_markup=self.kb.back_btn()
    )


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
    """Перевод названий дней с англ на русском"""

    eng_day = eng_day.lower()
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


def translate_day_reverse(ru_day: str) -> str:
    """Перевод названий дней с русского на англ"""

    ru_day = ru_day.lower()
    days = {
        'понедельник': 'monday',
        'вторник ': 'tuesday',
        'среда': 'wednesday',
        'четверг': 'thursday',
        'пятница': 'friday',
        'суббота': 'saturday',
        'воскресенье': 'sunday',
    }

    return days[ru_day]


def convert_date(date: str, format: str = '%d-%m-%Y') -> str:
    """Преобразовываем дату в формат дд-мм-год """
    try:
        date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    except Exception:
        date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%f')
    date = date_time_obj.strftime(format)

    return date


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


async def show_address_list(self: 'AddressHandler', message: Message, state: FSMContext, address_list: list[dict]):
    """Отображение списка адресов с кнопками(по умолчанию/удалить)"""

    status_code, add_address_msg = await req_to_api(
        method='get',
        url='bot/messages?message_key=ADD_ADDRESS'
    )

    msg = await message.answer(
        add_address_msg,
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

            status_code, default_address_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=ADDRESS_INFO_DEDAULT'
            )

            msg = await message.answer(
                default_address_msg.format(
                    count,
                    address_text
                ),
                reply_markup=self.kb.address_delete_default_btn(address)
            )
        else:
            status_code, no_default_address_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=ADDRESS_INFO_NOT_DEDAULT'
            )

            msg = await message.answer(
                no_default_address_msg.format(
                    count,
                    address_text
                ),
                reply_markup=self.kb.address_delete_default_btn(address)
            )
        count += 1
        msg_ids[address['id']] = msg.message_id

    await state.update_data(msg_ids=msg_ids)


async def show_address_date(message: Message, address: 'Address',
                            kb: 'OrderKeyboard', menu_kb: 'OrderKeyboard',state: FSMContext):
    work_dates = address.get('work_dates')
    if work_dates:

        status_code, choose_date_msg = await req_to_api(
            method='get',
            url='bot/messages?message_key=CHOOSE_DATE_ORDER'
        )

        await message.answer(
            choose_date_msg,
            reply_markup=kb(work_dates)
        )
        await state.set_state(CreateOrder.date)

    else:
        status_code, no_work_days_msg = await req_to_api(
            method='get',
            url='bot/messages?message_key=NO_WORK_DAYS_FOR_ADDRESS'
        )

        await message.answer(
            no_work_days_msg,
            reply_markup=menu_kb()
        )
