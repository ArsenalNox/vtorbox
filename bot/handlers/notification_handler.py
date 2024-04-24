from urllib.parse import quote

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.requests_to_api import req_to_api


class NotificationHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.callback_query(F.data.startswith('confirm_order'))
        async def approve_order(callback: CallbackQuery, state: FSMContext):

            data = await state.get_data()
            order_id = callback.data.split('_')[-1]

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            status_code, approve_order_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=ORDER_WAS_APPROVED'
            )

            await callback.bot.edit_message_text(
                chat_id=data.get('chat_id'),
                message_id=callback.message.message_id,
                text=approve_order_msg.format(order.get('order_num')),
                reply_markup=None
            )

            status = quote("подтверждена")

            await req_to_api(
                method='put',
                url=f'orders/{order_id}/status?status_text={status}',
            )
