from aiogram import Bot, Router, F

from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard

from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):

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



