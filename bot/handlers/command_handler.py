import json
import time

import aiohttp
import requests
from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard

from bot.services.users import UserService
from bot.settings import settings
from bot.states.states import RegistrationUser
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            # получаем промокод из сообщения пользователя
            promocode_in_msg = message.text.split()[1:]
            if not promocode_in_msg:
                promocode_in_msg = ['']

            # ищем пользователя из БД по промокоду и затем добавляем ему данные телеграмма в БД
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.local_url + f'search-user-by-promocode?promocode={promocode_in_msg[0]}') as resp:
                    user = await resp.json()

            if user:
                user_data = json.dumps({
                    'user_id': user['id'],
                    'tg_id': message.from_user.id,
                    'username': message.from_user.username,
                    'fullname': message.from_user.full_name
                })

                # обновляем данные пользователя данными из телеграма
                requests.post(settings.local_url + 'add-user-data-from-site', data=user_data)

                await message.answer(
                    MESSAGES['START'],
                    reply_markup=self.kb.start_menu_btn()
                )

            else:
                user_data = json.dumps({
                    'tg_id': message.from_user.id,
                    'username': message.from_user.username,
                    'fullname': message.from_user.full_name
                })

                # создаем пользователя
                requests.post(settings.local_url + 'create-user', data=user_data)

                await message.answer(
                    MESSAGES['REGISTRATION_MENU'],
                    reply_markup=self.kb.registration_btn()
                )
                await state.set_state(RegistrationUser.phone)

                # сохраняем в состояние chat_id
                await state.update_data(chat_id=message.from_user.id)
