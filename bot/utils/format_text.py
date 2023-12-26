from typing import Union

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, User

from app.models import Address, Users


def format_addresses(addresses: list[Address]) -> str:
    """Формируем текст с адресами пользователя"""

    result = 'Ваши адреса:\n'

    for index, address in enumerate(addresses, 1):
        # если адрес помечен как основной, то добавляем к нему смайл
        if address.main:
            result += f'{index}. <b>{address.address} ✅</b>\n'
        else:
            result += f'{index}. <b>{address.address}</b>\n'

    return result


def format_questionnaire(user: Users):
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



