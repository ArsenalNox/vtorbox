import json
import re

from aiogram import Bot, Router, F
from aiogram.filters import and_f, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.questionnaire_kb import QuestionnaireKeyboard
from bot.states.states import EditQuestionnaireState
from bot.utils.buttons import BUTTONS
from bot.utils.handle_data import phone_pattern, email_pattern
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

            await state.update_data(chat_id=message.chat.id)
            await state.update_data(menu_view='questionnaire')

            status_code, user_data = await req_to_api(
                method='get',
                url=f'bot/users/telegram?tg_id={message.chat.id}',
            )

            status_code, questionnaire_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=QUESTIONNAIRE'
            )

            await message.answer(
                questionnaire_msg.format(
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

            status_code, firstname_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=WRITE_YOUR_FIRSTNAME'
            )

            await message.answer(
                firstname_msg,
                reply_markup=self.kb.back_btn()
            )

        @self.router.message(EditQuestionnaireState.first_name)
        async def set_firstname(message: Message, state: FSMContext):
            """Отлавливаем изменение имени"""

            await state.update_data(chat_id=message.chat.id)
            status_code, user_data = await req_to_api(
                method='get',
                url=f'bot/users/telegram?tg_id={message.chat.id}',
            )

            if message.text == BUTTONS['BACK_QUESTIONNAIRE'].strip():
                status_code, back_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=BACK'
                )
                await message.answer(
                    back_msg,
                    reply_markup=self.kb.questionnaire_btn()
                )
                await state.set_state(state=None)
            else:

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

                    status_code, wrong_firstname_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=WRONG_FIRSTNAME'
                    )

                    await message.answer(
                        wrong_firstname_msg
                    )

        @self.router.message(F.text.startswith(BUTTONS['LAST_NAME']))
        async def get_lastname(message: Message, state: FSMContext):
            """Запрашиваем фамилии у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.last_name)

            status_code, lastname_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=WRITE_YOUR_LASTNAME'
            )

            await message.answer(
                lastname_msg,
                reply_markup=self.kb.back_btn()
            )

        @self.router.message(EditQuestionnaireState.last_name)
        async def set_lastname(message: Message, state: FSMContext):
            """Отлавливаем изменение фамилии"""

            await state.update_data(chat_id=message.chat.id)
            status_code, user_data = await req_to_api(
                method='get',
                url=f'bot/users/telegram?tg_id={message.from_user.id}',
            )

            if message.text == BUTTONS['BACK_QUESTIONNAIRE'].strip():
                status_code, back_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=BACK'
                )
                await message.answer(
                    back_msg,
                    reply_markup=self.kb.questionnaire_btn()
                )
                await state.set_state(state=None)
            else:
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

                    status_code, wrong_lastname_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=WRONG_LASTNAME'
                    )

                    await message.answer(
                        wrong_lastname_msg
                    )

        @self.router.message(F.text.startswith(BUTTONS['PHONE_NUMBER']))
        async def get_phone_number(message: Message, state: FSMContext):
            """Запрашиваем номер телефона у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.phone_number)

            status_code, phone_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=WRITE_YOUR_PHONE_NUMBER'
            )

            await message.answer(
                phone_msg,
                reply_markup=self.kb.send_phone()
            )

        @self.router.message(or_f(
            EditQuestionnaireState.phone_number,
            and_f(
                F.content_type.in_({'contact'}),
            EditQuestionnaireState.phone_number))
        )
        async def set_phone_number(message: Message, state: FSMContext):
            """Отлавливаем изменение номера телефона"""

            await state.update_data(chat_id=message.chat.id)
            phone = ''
            check_phone = ''
            if message.contact:
                phone = message.contact.phone_number
            else:
                check_phone = re.search(phone_pattern, message.text)

            if phone or (check_phone and len(message.text) == 11):
                status_code, user_data = await req_to_api(
                    method='get',
                    url=f'bot/users/telegram?tg_id={message.chat.id}',
                )

                # запрос на изменение номера телефона у пользователя в БД
                new_user_data = json.dumps({
                    'telegram_id': message.from_user.id,
                    'phone_number': phone or message.text,
                    'user_id': user_data.get('id')
                })

                status_code, answer = await req_to_api(
                    method='put',
                    url='user',
                    data=new_user_data,
                )
                code_from_message = answer.get('code')
                if code_from_message == 423:
                    status_code, unique_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=PHONE_NUMBER_IS_EXIST'
                    )
                    await message.answer(
                        unique_msg
                    )

                elif code_from_message == 204:
                    status_code, text_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=EMPTY_CHANGE_PHONE'
                    )
                    await message.answer(
                        text_msg
                    )

                await state.set_state(state=None)

                # переходим к выводу анкеты
                await get_questionnaire(
                    message=message,
                    state=state
                )

            elif message.text == BUTTONS['BACK_QUESTIONNAIRE'].strip():
                status_code, back_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=BACK'

                )
                await message.answer(
                    back_msg,
                    reply_markup=self.kb.questionnaire_btn()
                )
                await state.set_state(state=None)
            else:

                status_code, wrong_phone_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=WRONG_PHONE_NUMBER'
                )

                await message.answer(
                    wrong_phone_msg
                )

        @self.router.message(F.text.startswith(BUTTONS['EMAIL']))
        async def get_email(message: Message, state: FSMContext):
            """Запрашиваем email у пользователя"""

            await state.update_data(chat_id=message.chat.id)
            await state.set_state(EditQuestionnaireState.email)

            status_code, email_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=WRITE_YOUR_EMAIL'
            )

            await message.answer(
                email_msg,
                reply_markup=self.kb.back_btn()
            )

        @self.router.message(EditQuestionnaireState.email)
        async def set_email(message: Message, state: FSMContext):
            """Отлавливаем изменение email"""

            await state.update_data(chat_id=message.chat.id)
            check_email = re.search(email_pattern, message.text)
            if check_email:
                status_code, user_data = await req_to_api(
                    method='get',
                    url=f'bot/users/telegram?tg_id={message.chat.id}',
                )

                new_user_data = json.dumps({
                    'telegram_id': message.from_user.id,
                    'email': message.text,
                    'user_id': user_data.get('id')
                })

                status_code, answer = await req_to_api(
                    method='put',
                    url='user',
                    data=new_user_data,
                )
                code_from_message = answer.get('code')
                if code_from_message == 422:
                    status_code, unique_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=EMAIL_IS_EXIST'
                    )
                    await message.answer(
                        unique_msg
                    )

                elif code_from_message == 205:
                    status_code, text_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=EMPTY_CHANGE_EMAIL'
                    )
                    await message.answer(
                        text_msg
                    )

                await state.set_state(state=None)
                # переходим к выводу анкеты
                await get_questionnaire(
                    message=message,
                    state=state
                )

            elif message.text == BUTTONS['BACK_QUESTIONNAIRE'].strip():
                status_code, back_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=BACK'
                )
                await message.answer(
                    back_msg,
                    reply_markup=self.kb.questionnaire_btn()
                )
                await state.set_state(state=None)

            else:

                status_code, wrong_email_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=WRONG_EMAIL'
                )

                await message.answer(
                    wrong_email_msg,
                )
