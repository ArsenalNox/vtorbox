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
            requests.post(settings.local_url + 'user', data=user_data, headers=HEADERS)

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

            # получаем активную заявку пользователя
            # если есть, то выводим с такой кнопкой show_btn(order_id)
            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )
            await state.set_state(state=None)

        @self.router.callback_query(F.data.startswith('show'))
        async def show_active_order(callback: CallbackQuery, state: FSMContext):
            """Просмотр активной заявки пользователя"""

            order_id = callback.data.split('_')[1]

            # получаем заказ по его id
            await callback.message.answer(
                MESSAGES['ORDER_INFO'],
                reply_markup=self.order_kb.order_menu_btn(order_id)
            )

            await callback.message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )


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
            response = requests.get(settings.local_url + f'users/phone?phone_number={phone}', headers=HEADERS)
            user = response.json()
            if user and response.status_code == http.HTTPStatus.OK:
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
                response = requests.get(settings.local_url + f'users/phone?phone_number={phone}', headers=HEADERS)
                user = response.json()
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
                response = requests.get(settings.local_url + f'users/promocode?promocode={promocode}', headers=HEADERS)
                user = response.json()

                if user and response.status_code == http.HTTPStatus.OK:
                    user_data = {
                        'tg_id': message.from_user.id,
                        'username': message.from_user.username,
                        'fullname': message.from_user.full_name
                    }

                    # регаем пользователя
                    response = requests.post(settings.local_url + f'user', data=user_data, headers=HEADERS)

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
            await state.set_state(state=None)

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )
