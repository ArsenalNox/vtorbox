from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.notification_kb import NotificationKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class NotificationHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = NotificationKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['NOTIFICATIONS']))
        async def get_notifications(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['NOTIFICATIONS'],
                reply_markup=self.kb.start_menu_btn()
            )
