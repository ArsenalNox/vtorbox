from typing import Union

from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.models import Address


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


async def delete_messages_with_btn(data: dict, state: FSMContext, src: Union[CallbackQuery, Message, Bot]):
    """Удаление сообщений с кнопками"""

    if data.get('msg'):
        await src.bot.edit_message_reply_markup(
            chat_id=data.get('chat_id'),
            message_id=data.get('msg')
        )
        await state.update_data(msg=None)

