import json
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

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            order_id = callback.data.split('_')[-1]

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )
            order_status = order.get('status_data', {}).get('status_name')

            if order_status == 'ожидается подтверждение':
                status_code, approve_order_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=ORDER_WAS_APPROVED'
                )

                status = quote("подтверждена")

                await req_to_api(
                    method='put',
                    url=f'orders/{order_id}/status?status_text={status}',
                )

                await callback.bot.edit_message_text(
                    chat_id=data.get('chat_id'),
                    message_id=callback.message.message_id,
                    text=approve_order_msg.format(order.get('order_num')),
                    reply_markup=None
                )

            else:
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=callback.message.message_id,
                    reply_markup=None
                )

        @self.router.callback_query(F.data.startswith('deny_order'))
        async def deny_order(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            order_id = callback.data.split('_')[-1]

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )
            order_status = order.get('status_data', {}).get('status_name')

            if order_status == 'ожидается подтверждение':
                status_code, leave_door_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=LEAVE_DOOR'
                )

                await callback.bot.edit_message_text(
                    chat_id=callback.message.chat.id,
                    message_id=callback.message.message_id,
                    text=leave_door_msg,
                    reply_markup=self.kb.leave_door_yes_no_btn(order_id)
                )

            else:
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=callback.message.message_id,
                    reply_markup=None
                )

        @self.router.callback_query(F.data.startswith('leave_door'))
        async def yes_or_no_leave_door(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            user_choose = callback.data.split('_')[-2]
            order_id = callback.data.split('_')[-1]

            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None
            )

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            if user_choose == 'no':
                status = quote("отменена")

                await req_to_api(
                    method='put',
                    url=f'orders/{order_id}/status?status_text={status}',
                )

                status_code, deny_order_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=ORDER_WAS_DENY'
                )

                await callback.message.answer(
                    deny_order_msg.format(order.get('order_num'))
                )

            else:
                status_code, approve_order_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=ORDER_WAS_APPROVED'
                )

                status = quote("подтверждена")

                await req_to_api(
                    method='put',
                    url=f'orders/{order_id}/status?status_text={status}',
                )
                update_order_data = json.dumps(
                    {
                        'comment': 'Оставят у двери'
                    }
                )

                status_code, response = await req_to_api(
                    method='put',
                    url=f'orders/{order_id}',
                    data=update_order_data,
                )

                await callback.message.answer(
                    approve_order_msg.format(order.get('order_num'))
                )

        @self.router.callback_query(F.data.startswith('back_leave_door'))
        async def back_leave_door(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            order_id = callback.data.split('_')[-1]

            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=self.kb.confirm_deny_order(order_id)
            )




