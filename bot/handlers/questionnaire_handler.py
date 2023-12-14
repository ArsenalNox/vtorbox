import re

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
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

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            user = UserService.get_user_by_tg_id(message.chat.id)
            text = format_questionnaire(
                user=user
            )

            await message.answer(
                text,
                reply_markup=self.kb.questionnaire_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['EDIT_QUESTIONNAIRE']))
        async def edit_questionnaire(message: Message, state: FSMContext):
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['WRITE_YOUR_FULLNAME']
            )
            await state.set_state(EditQuestionnaireState.fullname)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(F.text, EditQuestionnaireState.fullname)
        async def get_new_fullname(message: Message, state: FSMContext):
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            check_fullname = re.search(fullname_pattern, message.text)

            if check_fullname:
                msg = await message.answer(
                    MESSAGES['WRITE_YOUR_COMMENT'],
                    reply_markup=self.kb.empty_comment_btn()
                )
                await state.update_data(msg=msg.message_id)
                # сохраняем новое имя
                await state.update_data(new_fullname=message.text)
                await state.set_state(EditQuestionnaireState.comment)

            else:
                await message.answer(
                    MESSAGES['WRONG_QUESTIONNAIRE_DATA']
                )

        @self.router.message(F.text, EditQuestionnaireState.comment)
        async def get_new_comment(message: Message, state: FSMContext):
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            new_fullname = data.get('new_fullname')
            comment = message.text

            user = UserService.get_user_by_tg_id(message.from_user.id)

            # меняем данные у пользователя
            UserService.change_user_data(
                new_fullname=new_fullname,
                comment=comment,
                user=user
            )

            # обнуляем состояния
            await state.set_state(state=None)

            # после обновления данных переходим к самой анкете
            await get_questionnaire(
                message=message,
                state=state
            )

        @self.router.callback_query(F.data.startswith('empty_comment'))
        async def change_user_data_without_comment(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            new_fullname = data.get('new_fullname')

            # обнуляем состояния
            await state.set_state(state=None)

            user = UserService.get_user_by_tg_id(callback.message.chat.id)

            # меняем данные у пользователя
            UserService.change_user_data(
                new_fullname=new_fullname,
                user=user,
                comment='delete'
            )

            # после обновления данных переходим к самой анкете
            await get_questionnaire(
                message=callback.message,
                state=state
            )

        @self.router.message(F.text.startswith(BUTTONS['PHONE_NUMBER']))
        async def edit_phone_number(message: Message, state: FSMContext):
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['WRITE_YOUR_PHONE_NUMBER']
            )
            await state.set_state(EditQuestionnaireState.phone_number)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(F.text, EditQuestionnaireState.phone_number)
        async def get_new_phone_number(message: Message, state: FSMContext):
            check_phone = re.search(phone_pattern, message.text)

            if check_phone and len(message.text) == 11:
                user = UserService.get_user_by_tg_id(message.from_user.id)

                UserService.change_user_data(
                    user=user,
                    phone_number=message.text
                )

                # обнуляем состояния
                await state.set_state(state=None)

                # после обновления данных переходим к самой анкете
                await get_questionnaire(
                    message=message,
                    state=state
                )

            else:
                await message.answer(
                    MESSAGES['WRONG_QUESTIONNAIRE_DATA']
                )

        @self.router.message(F.text.startswith(BUTTONS['EMAIL']))
        async def edit_email(message: Message, state: FSMContext):
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['WRITE_YOUR_EMAIL']
            )
            await state.set_state(EditQuestionnaireState.email)

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(F.text, EditQuestionnaireState.email)
        async def get_new_email(message: Message, state: FSMContext):
            check_email = re.search(email_pattern, message.text)

            if check_email:
                user = UserService.get_user_by_tg_id(message.from_user.id)

                UserService.change_user_data(
                    user=user,
                    email=message.text
                )

                # обнуляем состояния
                await state.set_state(state=None)

                # после обновления данных переходим к самой анкете
                await get_questionnaire(
                    message=message,
                    state=state
                )

            else:
                await message.answer(
                    MESSAGES['WRONG_QUESTIONNAIRE_DATA']
                )
