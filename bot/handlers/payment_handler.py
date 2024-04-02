from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.payment_kb import PaymentKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class PaymentHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = PaymentKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['PAYMENTS']))
        async def get_payments(message: Message, state: FSMContext):
            """Получение способов оплаты пользователя"""

            await state.update_data(chat_id=message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            status_code, payment_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=PAYMENTS'
            )

            await message.answer(
                payment_msg,
                reply_markup=self.kb.settings_btn()
            )