import json
import re

import requests
from aiogram import Bot, Router, F

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.settings import settings
from bot.states.states import RegistrationUser

from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.handle_data import phone_pattern
from bot.utils.messages import MESSAGES


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['START_BOT']))
        async def start_bot_user(message: Message, state: FSMContext):
            """Старт бота для нового юзера бота"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            user_data = json.dumps({
                'tg_id': message.from_user.id,
                'username': message.from_user.username,
                'fullname': message.from_user.full_name
            })

            # создаем пользователя
            requests.post(settings.local_url + 'create-user', data=user_data)

            await message.answer(
                MESSAGES['START'],
                reply_markup=self.kb.start_menu_btn()
            )


            # отправка приветственного видео
            # await message.answer_video(
            #     video=
            # )

        @self.router.message(RegistrationUser.phone, F.content_type.in_({'contact'}))
        async def catch_user_phone_number(message: Message, state: FSMContext):
            """Отлавливаем номер телефона юзера"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            phone = message.contact.phone_number
            response = requests.get(settings.local_url + f'search-user-by-phone?phone={phone}')
            user = response.json()
            if user:
                await state.set_state(state=None)
                # логика отправки смс кода

            else:
                await message.answer(
                    MESSAGES['PHONE_NOT_FOUND'],
                    reply_markup=self.kb.registration_btn()
                )

        @self.router.message(RegistrationUser.phone)
        async def catch_text_user_phone(message: Message, state: FSMContext):
            check_phone = re.search(phone_pattern, message.text)

            if check_phone and len(message.text) == 11:
                phone = message.text
                response = requests.get(settings.local_url + f'search-user-by-phone?phone={phone}')
                user = response.json()
                if user:
                    await state.set_state(state=None)
                    # логика отправки смс кода

                else:
                    await message.answer(
                        MESSAGES['PHONE_NOT_FOUND'],
                        reply_markup=self.kb.registration_btn()
                    )
                await state.set_state(state=None)
            else:
                await message.answer(
                    MESSAGES['WRITE_YOUR_PHONE_NUMBER'],
                    reply_markup=self.kb.registration_btn()
                )

        @self.router.message(F.text.startswith(BUTTONS['SETTINGS']))
        async def get_settings(message: Message, state: FSMContext):
            """Получение настроек бота"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['SETTINGS'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['ABOUT']))
        async def get_about_info(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['ABOUT'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['MENU']))
        async def get_menu(message: Message, state: FSMContext):
            """Переход в главное меню"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(state=None)

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )
