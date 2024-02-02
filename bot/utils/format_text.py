import datetime
import pprint
from typing import Union

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from bot.utils.handle_data import translate_month, translate_day


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

    if data.get('msg'):
        await src.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg')
        )
        await state.update_data(msg=None)

    if data.get('msg_ids'):
        for address_id, msg_id in data.get('msg_ids').items():
            await src.bot.edit_message_reply_markup(
                chat_id=data.get('chat_id'),
                message_id=msg_id
            )
        await state.update_data(msg_ids=[])

    if data.get('order_msg'):
        await src.bot.delete_message(
            chat_id=data.get('chat_id'),
            message_id=data.get('order_msg')
        )
        await state.update_data(order_msg=None)

    if data.get('container_msg'):
        await src.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('container_msg'),
            reply_markup=None
        )
        await state.update_data(container_msg=None)


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