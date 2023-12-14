from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.application_kb import ApplicationKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class ApplicationHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = ApplicationKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['CREATE_APPLICATION']))
        async def create_application(message: Message, state: FSMContext):
            """Создание заявки"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['CREATE_APPLICATION'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['APPLICATIONS_HISTORY']))
        async def applications_history(message: Message, state: FSMContext):
            """Создание заявки"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['APPLICATIONS_HISTORY'],
                reply_markup=self.kb.start_menu_btn()
            )