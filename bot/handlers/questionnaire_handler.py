import json
import re

import requests
from aiogram import Bot, Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.keyboards.questionnaire_kb import QuestionnaireKeyboard
from bot.settings import settings
from bot.states.states import EditQuestionnaireState
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn, format_questionnaire
from bot.utils.handle_data import fullname_pattern, phone_pattern, email_pattern, HEADERS
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class QuestionnaireHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = QuestionnaireKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['QUESTIONNAIRE']))
        async def get_questionnaire(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            # получаем анкету по tg_id
            await state.update_data(chat_id=message.chat.id)
            status_code, user_data = await req_to_api(
                method='get',
                url=f'bot/users/telegram?tg_id={message.from_user.id}',
            )

            await message.answer(
                MESSAGES['QUESTIONNAIRE'].format(
                    user_data.get('firstname') if user_data.get('firstname') else 'Не задано',
                    user_data.get('secondname') if user_data.get('secondname') else 'Не задано',
                    user_data.get('phone_number') if user_data.get('phone_number') else 'Не задано',
                    user_data.get('email') if user_data.get('email') else 'Не задано'
                ),
                reply_markup=self.kb.questionnaire_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['FIRST_NAME']))
        async def get_firstname(message: Message, state: FSMContext):
            """Запрашиваем имя у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.first_name)
            await message.answer(
                MESSAGES['WRITE_YOUR_FIRSTNAME'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(EditQuestionnaireState.first_name)
        async def set_firstname(message: Message, state: FSMContext):
            """Отлавливаем изменение имени"""

            await state.update_data(chat_id=message.chat.id)
            status_code, user_data = await req_to_api(
                method='get',
                url=f'bot/users/telegram?tg_id={message.from_user.id}',
            )

            # запрос на изменение имени у пользователя
            if message.text.isalpha():
                new_user_data = json.dumps({
                    'telegram_id': message.from_user.id,
                    'firstname': message.text,
                    'user_id': user_data.get('id')
                })

                await req_to_api(
                    method='put',
                    url='user',
                    data=new_user_data,
                )

                await state.set_state(state=None)

                # переходим к выводу анкеты
                await get_questionnaire(
                    message=message,
                    state=state
                )
            else:
                await message.answer(
                    MESSAGES['WRONG_FIRSTNAME']
                )

        @self.router.message(F.text.startswith(BUTTONS['LAST_NAME']))
        async def get_lastname(message: Message, state: FSMContext):
            """Запрашиваем фамилии у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.last_name)
            await message.answer(
                MESSAGES['WRITE_YOUR_LASTNAME'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(EditQuestionnaireState.last_name)
        async def set_lastname(message: Message, state: FSMContext):
            """Отлавливаем изменение фамилии"""

            await state.update_data(chat_id=message.chat.id)
            status_code, user_data = await req_to_api(
                method='get',
                url=f'bot/users/telegram?tg_id={message.from_user.id}',
            )

            # запрос на изменение имени у пользователя
            if message.text.isalpha():
                new_user_data = json.dumps({
                    'telegram_id': message.from_user.id,
                    'secondname': message.text,
                    'user_id': user_data.get('id')
                })

                await req_to_api(
                    method='put',
                    url='user',
                    data=new_user_data,
                )

                await state.set_state(state=None)

                # переходим к выводу анкеты
                await get_questionnaire(
                    message=message,
                    state=state
                )
            else:
                await message.answer(
                    MESSAGES['WRONG_LASTNAME']
                )

        @self.router.message(F.text.startswith(BUTTONS['PHONE_NUMBER']))
        async def get_phone_number(message: Message, state: FSMContext):
            """Запрашиваем номер телефона у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.phone_number)
            await message.answer(
                MESSAGES['WRITE_YOUR_PHONE_NUMBER'],
                reply_markup=self.kb.send_phone()
            )

        @self.router.message(or_f(EditQuestionnaireState.phone_number, F.content_type.in_({'contact'})))
        async def set_phone_number(message: Message, state: FSMContext):
            """Отлавливаем изменение номера телефона"""

            await state.update_data(chat_id=message.chat.id)
            phone = ''
            check_phone = ''
            if message.contact:
                phone = message.contact.phone_number
            else:
                check_phone = re.search(phone_pattern, message.text)

            if phone:
                await message.answer(
                    MESSAGES['SEND_SMS']
                )
                await state.update_data(phone_number=phone)
                await state.set_state(EditQuestionnaireState.approve_phone)

            elif check_phone and len(message.text) == 11:
                await message.answer(
                    MESSAGES['SEND_SMS']
                )
                await state.update_data(phone_number=message.text)
                await state.set_state(EditQuestionnaireState.approve_phone)

            else:
                await message.answer(
                    MESSAGES['WRONG_PHONE_NUMBER']
                )

        @self.router.message(EditQuestionnaireState.approve_phone)
        async def approve_phone_number(message: Message, state: FSMContext):
            """Подтверждение номера телефона"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            if message.text == '123':

                status_code, user_data = await req_to_api(
                    method='get',
                    url=f'bot/users/telegram?tg_id={message.from_user.id}',
                )

                # запрос на изменение номера телефона у пользователя в БД
                new_user_data = json.dumps({
                    'telegram_id': message.from_user.id,
                    'phone_number': data.get('phone_number'),
                    'user_id': user_data.get('id')
                })

                await req_to_api(
                    method='put',
                    url='user',
                    data=new_user_data,
                )

                await state.set_state(state=None)
                # переходим к выводу анкеты
                await get_questionnaire(
                    message=message,
                    state=state
                )
            else:
                await message.answer(
                    MESSAGES['WRONG_CODE']
                )
                await get_questionnaire(
                    message=message,
                    state=state
                )

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.questionnaire_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['EMAIL']))
        async def get_email(message: Message, state: FSMContext):
            """Запрашиваем email у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.email)
            await message.answer(
                MESSAGES['WRITE_YOUR_EMAIL'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(EditQuestionnaireState.email)
        async def set_email(message: Message, state: FSMContext):
            """Отлавливаем изменение email"""

            await state.update_data(chat_id=message.chat.id)
            check_email = re.search(email_pattern, message.text)
            if check_email:
                await message.answer(
                    MESSAGES['SEND_EMAIL']
                )
                await state.update_data(email=message.text)
                await state.set_state(EditQuestionnaireState.approve_email)

            else:
                await message.answer(
                    MESSAGES['WRONG_EMAIL'],
                )

        @self.router.message(EditQuestionnaireState.approve_email)
        async def approve_phone_number(message: Message, state: FSMContext):
            """Подтверждение email"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()

            if message.text == '123':
                # запрос на изменение email у пользователя в БД
                status_code, user_data = await req_to_api(
                    method='get',
                    url=f'bot/users/telegram?tg_id={message.from_user.id}',
                )

                new_user_data = json.dumps({
                    'telegram_id': message.from_user.id,
                    'email': data.get('email'),
                    'user_id': user_data.get('id')
                })

                await req_to_api(
                    method='put',
                    url='user',
                    data=new_user_data,
                )

                await state.set_state(state=None)
                # переходим к выводу анкеты
                await get_questionnaire(
                    message=message,
                    state=state
                )
            else:
                await message.answer(
                    MESSAGES['WRONG_CODE']
                )
                await message.answer(
                    MESSAGES['MENU'],
                    reply_markup=self.kb.start_menu_btn()
                )
