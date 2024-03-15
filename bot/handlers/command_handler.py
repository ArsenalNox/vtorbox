import http
import json
import time

import aiohttp
import requests
from aiogram import Bot, Router, F
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard

from bot.settings import settings
from bot.states.states import RegistrationUser
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.handle_data import HEADERS
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.message(or_f(Command('start'), F.text == BUTTONS['START']))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            await state.update_data(chat_id=message.chat.id)

            promocode_in_msg = message.text.split()[-1]

            if not promocode_in_msg:
                promocode_in_msg = ''

            # ищем пользователя из БД по промокоду и затем добавляем ему данные телеграмма в БД
            status_code, user = await req_to_api(
                method='get',
                url=f'bot/users/promocode?promocode={promocode_in_msg}',
            )

            if user and status_code == http.HTTPStatus.OK:
                user_data = json.dumps({
                    'tg_id': message.from_user.id,
                    'username': message.from_user.username,
                    'fullname': message.from_user.full_name,
                    'promocode': promocode_in_msg
                })

                # обновляем данные пользователя данными из телеграма
                await req_to_api(
                    method='put',
                    url='bot/users/botclient/link',
                    data=user_data,
                )

                await message.answer(
                    MESSAGES['START']
                )
                await message.answer(
                    MESSAGES['ABOUT']
                )
                await message.answer(
                    MESSAGES['MENU'],
                    reply_markup=self.kb.start_menu_btn()
                )

            else:
                status_code, user = await req_to_api(
                    method='get',
                    url=f'user/me?tg_id={message.from_user.id}'
                )

                if not user or user == {'message': 'Not found'}:
                    user_data = json.dumps({
                        'tg_id': message.from_user.id,
                        'username': message.from_user.username,
                        'fullname': message.from_user.full_name
                    })

                    # создаем пользователя
                    await req_to_api(
                        method='post',
                        url='bot/user',
                        data=user_data,
                    )

                    status_code, user = await req_to_api(
                        method='get',
                        url=f'user/me?tg_id={message.from_user.id}'
                    )

                if user.get('roles'):
                    if 'courier' in user.get('roles'):
                        await message.answer(
                            MESSAGES['COURIER'],
                            reply_markup=self.kb.courier_btn()
                        )

                else:
                    await message.answer(
                        MESSAGES['REGISTRATION_MENU'],
                        reply_markup=self.kb.registration_btn()
                    )
                    await state.set_state(RegistrationUser.phone)

                # сохраняем в состояние chat_id
                await state.update_data(chat_id=message.chat.id)
