import http
import json
import pprint
import re

import requests
from aiogram import Bot, Router, F

from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.keyboards.order import OrderKeyboard
from bot.settings import settings
from bot.states.states import RegistrationUser, SMSEmail

from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.handle_data import phone_pattern, show_active_orders
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

            await state.set_state(state=None)
            await state.update_data(chat_id=message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
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
            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={message.from_user.id}',
            )

            if orders and status_code == 200:
                await show_active_orders(
                    orders=orders,
                    self=self,
                    message=message,
                    state=state
                )

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(RegistrationUser.phone, F.content_type.in_({'contact'}))
        async def catch_user_phone_number(message: Message, state: FSMContext):
            """Отлавливаем номер телефона юзера"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            phone = message.contact.phone_number

            status_code, user = await req_to_api(
                method='get',
                url=f'bot/users/phone?phone_number={phone}',
            )

            if user and status_code == http.HTTPStatus.OK:
                await state.set_state(state=None)
                # логика отправки смс кода
                await message.answer(
                    MESSAGES['SEND_SMS']
                )
                await state.set_state(SMSEmail.code)

            else:
                await message.answer(
                    MESSAGES['PHONE_NOT_FOUND'],
                    reply_markup=self.kb.registration_btn()
                )
                await state.set_state(RegistrationUser.phone)

        @self.router.message(SMSEmail.code)
        async def get_sms_code(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(state=None)

            code = message.text

            if code == '123':
                await message.answer(
                    'Отлично! Код верный',
                    reply_markup=self.kb.start_menu_btn()
                )

                await state.set_state(state=None)

                status_code, orders = await req_to_api(
                    method='get',
                    url=f'users/orders/?tg_id={message.from_user.id}',
                )

                if orders:
                    await show_active_orders(
                        message=message,
                        orders=orders,
                        state=state,
                        self=self
                    )
            else:
                await message.answer(
                    'Код неверный!',
                    reply_markup=self.kb.registration_btn()
                )
                await state.set_state(RegistrationUser.phone)

        @self.router.message(RegistrationUser.phone)
        async def catch_text_user_phone(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            check_phone = re.search(phone_pattern, message.text)

            if check_phone and len(message.text) == 11:
                phone = message.text

                status_code, user = await req_to_api(
                    method='get',
                    url=f'bot/users/phone?phone_number={phone}',
                )

                if user and status_code == http.HTTPStatus.OK:
                    await state.set_state(state=None)
                    # логика отправки смс кода
                    await message.answer(
                        MESSAGES['SEND_SMS']
                    )
                    await state.set_state(SMSEmail.code)

                else:
                    await message.answer(
                        MESSAGES['PHONE_NOT_FOUND'],
                        reply_markup=self.kb.registration_btn()
                    )

            else:
                promocode = message.text
                status_code, user = await req_to_api(
                    method='get',
                    url=f'bot/users/promocode?promocode={promocode}',
                )

                if user and status_code == http.HTTPStatus.OK:
                    user_data = json.dumps({
                        'tg_id': message.from_user.id,
                        'username': message.from_user.username,
                        'fullname': message.from_user.full_name
                    })

                    # регаем пользователя
                    await req_to_api(
                        method='post',
                        url='bot/user',
                        data=user_data,
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

                else:
                    await message.answer(
                        MESSAGES['PROMOCODE_NOT_FOUND'],
                        reply_markup=self.kb.registration_btn()
                    )

        @self.router.message(F.text.startswith(BUTTONS['SETTINGS']))
        async def get_settings(message: Message, state: FSMContext):
            """Получение настроек бота"""

            await state.update_data(chat_id=message.chat.id)
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

            await state.update_data(chat_id=message.chat.id)
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

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={message.from_user.id}',
            )

            if orders:
                await show_active_orders(
                    message=message,
                    orders=orders,
                    state=state,
                    self=self
                )

            await state.update_data(chat_id=message.chat.id)
            await state.update_data(selected_day_of_week=[])
            await state.update_data(selected_day_of_month=[])
            await state.set_state(state=None)

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text)
        async def any_text(message: Message):
            await message.answer(
                MESSAGES['ANY_TEXT'],
                reply_markup=self.kb.start_menu_btn()
            )
