import re

from aiogram import Bot, Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.keyboards.questionnaire_kb import QuestionnaireKeyboard
from bot.services.users import UserService
from bot.states.states import EditQuestionnaireState
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn, format_questionnaire
from bot.utils.handle_data import fullname_pattern, phone_pattern, email_pattern
from bot.utils.messages import MESSAGES


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
            await message.answer(
                'Данные моей анкеты'
            )
            await message.answer(
                MESSAGES['QUESTIONNAIRE'],
                reply_markup=self.kb.questionnaire_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['FIRST_NAME']))
        async def get_firstname(message: Message, state: FSMContext):
            """Запрашиваем имя у пользователя"""

            await state.set_state(EditQuestionnaireState.first_name)
            await message.answer(
                MESSAGES['WRITE_YOUR_FIRSTNAME'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(EditQuestionnaireState.first_name)
        async def set_firstname(message: Message, state: FSMContext):
            """Отлавливаем изменение имени"""

            # запрос на изменение имени у пользователя

            await state.set_state(state=None)

            # переходим к выводу анкеты
            await get_questionnaire(
                message=message,
                state=state
            )

        @self.router.message(F.text.startswith(BUTTONS['LAST_NAME']))
        async def get_lastname(message: Message, state: FSMContext):
            """Запрашиваем фамилии у пользователя"""

            await state.set_state(EditQuestionnaireState.last_name)
            await message.answer(
                MESSAGES['WRITE_YOUR_LASTNAME'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(EditQuestionnaireState.last_name)
        async def set_lastname(message: Message, state: FSMContext):
            """Отлавливаем изменение фамилии"""

            # запрос на изменение имени у пользователя

            await state.set_state(state=None)

            # переходим к выводу анкеты
            await get_questionnaire(
                message=message,
                state=state
            )

        @self.router.message(F.text.startswith(BUTTONS['PHONE_NUMBER']))
        async def get_phone_number(message: Message, state: FSMContext):
            """Запрашиваем номер телефона у пользователя"""

            await state.set_state(EditQuestionnaireState.phone_number)
            await message.answer(
                MESSAGES['WRITE_YOUR_PHONE_NUMBER'],
                reply_markup=self.kb.send_phone()
            )

        @self.router.message(or_f(EditQuestionnaireState.phone_number, F.content_type.in_({'contact'})))
        async def set_phone_number(message: Message, state: FSMContext):
            """Отлавливаем изменение номера телефона"""

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
                await state.set_state(EditQuestionnaireState.approve_phone)

            elif check_phone and len(message.text) == 11:
                await message.answer(
                    MESSAGES['SEND_SMS']
                )
                await state.set_state(EditQuestionnaireState.approve_phone)

            else:
                await message.answer(
                    MESSAGES['WRONG_PHONE_NUMBER']
                )

        @self.router.message(EditQuestionnaireState.approve_phone)
        async def approve_phone_number(message: Message, state: FSMContext):
            """Подтверждение номера телефона"""

            if message.text == '123':
                # запрос на изменение номера телефона у пользователя в БД

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
                reply_markup=self.kb.questionnaire_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['EMAIL']))
        async def get_email(message: Message, state: FSMContext):
            """Запрашиваем email у пользователя"""

            await state.set_state(EditQuestionnaireState.email)
            await message.answer(
                MESSAGES['WRITE_YOUR_EMAIL'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(EditQuestionnaireState.email)
        async def set_email(message: Message, state: FSMContext):
            """Отлавливаем изменение email"""

            check_email = re.search(email_pattern, message.text)
            if check_email:
                await message.answer(
                    MESSAGES['SEND_EMAIL']
                )
                await state.set_state(EditQuestionnaireState.approve_email)

            else:
                await message.answer(
                    MESSAGES['WRONG_EMAIL'],
                )

        @self.router.message(EditQuestionnaireState.approve_email)
        async def approve_phone_number(message: Message, state: FSMContext):
            """Подтверждение email"""

            if message.text == '123':
                # запрос на изменение email у пользователя в БД

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