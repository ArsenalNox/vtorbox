from urllib.parse import quote

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.handle_data import show_order_info
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class NotificationHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.callback_query(F.data.startswith('confirm_order'))
        async def approve_order(callback: CallbackQuery, state: FSMContext):

            order_id = callback.data.split('_')[-1]

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            status = quote("подтверждена")

            await req_to_api(
                method='put',
                url=f'orders/{order_id}/status?status_text={status}',
            )

            await callback.message.answer(
                MESSAGES['ORDER_WAS_APPROVED'].format(
                    order.get('order_num')
                ),
                reply_markup=self.kb.start_menu_btn()
            )
