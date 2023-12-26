import http
import json
import re

import requests
from aiogram import Bot, Router, F

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.keyboards.order import OrderKeyboard
from bot.settings import settings
from bot.states.states import RegistrationUser

from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.handle_data import phone_pattern, HEADERS
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()
        self.order_kb = OrderKeyboard()

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
            req_to_api(
                method='post',
                url='user',
                data=user_data
            )

            await message.answer(
                MESSAGES['START']
            )
            await message.answer(
                MESSAGES['ABOUT']
            )
            # отправка приветственного видео
            # await message.answer_video(
            #     video=
            # )

            # получаем активные заявки пользователя
            # если есть, то выводим с такой кнопкой show_btn(order_id)
            order_id = 1
            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )
            await state.set_state(state=None)
            msg = await message.answer(
                'test',
                reply_markup=self.kb.show_btn(order_id)
            )

            await state.update_data(msg=msg.message_id)

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

            status_code, user = req_to_api(
                method='get',
                url=f'users/phone?phone_number={phone}'
            )

            if user and status_code == http.HTTPStatus.OK:
                await state.set_state(state=None)
                # логика отправки смс кода

            else:
                await message.answer(
                    MESSAGES['PHONE_NOT_FOUND'],
                    reply_markup=self.kb.registration_btn()
                )

        @self.router.message(RegistrationUser.phone)
        async def catch_text_user_phone(message: Message, state: FSMContext):

            data = await state.get_data()
            check_phone = re.search(phone_pattern, message.text)

            if check_phone and len(message.text) == 11:
                phone = message.text

                status_code, user = req_to_api(
                    method='get',
                    url=f'users/phone?phone_number={phone}'
                )

                if user:
                    await state.set_state(state=None)
                    # логика отправки смс кода

                else:
                    await message.answer(
                        MESSAGES['PHONE_NOT_FOUND'],
                        reply_markup=self.kb.registration_btn()
                    )

            else:
                promocode = message.text
                status_code, user = req_to_api(
                    method='get',
                    url=f'users/promocode?promocode={promocode}'
                )

                if user and status_code == http.HTTPStatus.OK:
                    user_data = json.dumps({
                        'tg_id': message.from_user.id,
                        'username': message.from_user.username,
                        'fullname': message.from_user.full_name
                    })

                    # регаем пользователя
                    req_to_api(
                        method='post',
                        url='user',
                        data=user_data
                    )

                    await message.answer(
                        MESSAGES['START'],
                        reply_markup=self.kb.start_menu_btn()
                    )
                    await message.answer(
                        MESSAGES['ABOUT'],
                        reply_markup=self.kb.start_menu_btn()
                    )
                    # отправляем видео о работе сервисе
                    # await message.answer_video(
                    #     video=
                    # )

                elif len(message.text) == 8:
                    await message.answer(
                        MESSAGES['PROMOCODE_NOT_FOUND'],
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
            await state.update_data(selected_day_of_week=[])
            await state.update_data(selected_day_of_month=[])
            await state.set_state(state=None)

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )
