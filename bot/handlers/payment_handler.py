from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.payment_kb import PaymentKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class PaymentHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = PaymentKeyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['PAYMENTS']))
        async def get_payments(message: Message, state: FSMContext):
            """Получение способов оплаты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['PAYMENTS'],
                reply_markup=self.kb.settings_btn()
            )