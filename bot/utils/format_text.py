import datetime
import pprint
import traceback
from typing import Union

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User



def format_addresses(addresses: list['Address']) -> str:
    """Формируем текст с адресами пользователя"""

    result = 'Ваши адреса:\n'

    for index, address in enumerate(addresses, 1):
        # если адрес помечен как основной, то добавляем к нему смайл
        if address.main:
            result += f'{index}. <b>{address.address} ✅</b>\n'
        else:
            result += f'{index}. <b>{address.address}</b>\n'

    return result


def format_questionnaire(user: 'Users'):
    """Формируем анкету пользователя"""

    result = '<b>Ваша анкета</b>: \n\n'
    fullname = user.full_name if user.full_name else 'Не задано'
    additional_info = user.additional_info if user.additional_info else 'Не задано'
    phone_number = user.phone_number if user.phone_number else 'Не задано'
    email = user.email if user.email else 'Не задано'
    result += f'Имя Фамилия: <b>{fullname}</b>\n' \
              f'Номер телефона: <b>{phone_number}</b>\n' \
              f'Email: <b>{email}</b>\n' \
              f'Доп.информация: <i>{additional_info}</i>'

    return result


async def delete_messages_with_btn(data: dict, state: FSMContext, src: Message):
    """Удаление сообщений с кнопками"""

    try:
        if data.get('msg'):
            await src.bot.edit_message_reply_markup(
                chat_id=data.get('chat_id'),
                message_id=data.get('msg'),
                reply_markup=None
            )
            await state.update_data(msg=None)
    except Exception as e:
        await state.update_data(msg=None)

    if data.get('active_msg'):
        await src.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('active_msg'),
            reply_markup=None
        )
        await state.update_data(active_msg=None)

    if data.get('msg_ids'):
        for address_id, msg_id in data.get('msg_ids').items():
            await src.bot.edit_message_reply_markup(
                chat_id=data.get('chat_id'),
                message_id=msg_id
            )
        await state.update_data(msg_ids=[])

    if data.get('order_msg'):
        try:
            await src.bot.delete_message(
                chat_id=data.get('chat_id'),
                message_id=data.get('order_msg')
            )
        except Exception:
            await src.bot.edit_message_text(
                text='---',
                chat_id=data.get('chat_id'),
                message_id=data.get('order_msg'),
                reply_markup=None
            )
        await state.update_data(order_msg=None)

    if data.get('container_msg'):
        await src.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('container_msg'),
            reply_markup=None
        )
        await state.update_data(container_msg=None)

    if data.get('courier_msg'):
        await src.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('courier_msg'),
            reply_markup=None
        )
        await state.update_data(courier_msg=None)


def format_orders_statuses_text(orders_statuses: list[list[str]]) -> str:
    """Форматрируем текст для вывода изменения статуса конкретной заявки"""

    text = ''
    count = 1
    for status in orders_statuses:
        date_time_obj = datetime.datetime.strptime(status[0], '%Y-%m-%dT%H:%M:%S.%f')
        date = date_time_obj.strftime('%d-%m-%Y %H:%M')
        tmp = f'{count}. {date} - <i>{status[1]}({status[2]})</i>\n'
        count += 1

        text += tmp

    return text


def format_schedule_text(type_interval: str, interval: list[str | int]) -> str:
    """Форматируем текст для вывода распианий адресов"""
    result = ''
    if type_interval == 'week_day':
        result += 'Вывоз по дням недели: '
        for day in interval:
            ru_day = translate_day(day)
            result += ru_day + ' '

    elif type_interval == 'month_day':
        result += f'Вывоз по дням месяца: {", ".join(interval)}'

    elif type_interval == 'on_request':
        result += 'Вывоз по запросу'

    if not result:
        return 'Не задано'

    return result


def format_available_addresses(
        addresses: list[dict]
):
    result = []

    for address in addresses:
        result.append(address.get('name_full'))

    return result


def convert_address_for_text(
        addresses: list[str],
        show_all: bool = False
):
    result = ''

    if show_all:
        for address in addresses:
            result += f'<b>{address}</b>\n '

        return result

    if len(addresses) > 7:
        for address in addresses[:7]:
            result += f'<b>{address}</b>, '
        result = result.rstrip(', ')
        result += ' <b>и др.</b>'
    else:
        result = ' более чем в 7 районах '

    return result


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
