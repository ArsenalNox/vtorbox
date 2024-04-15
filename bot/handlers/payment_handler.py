from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

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

            status_code, cards = await req_to_api(
                method='get',
                url=f'payment-data/saved-cards?user_id={message.chat.id}'
            )
            print(cards)

            if cards:
                await message.answer(
                    MESSAGES['PAYMENTS']
                )

                msg_ids = {}
                for card in cards:
                    msg = await message.answer(
                        MESSAGES['CARD_INFO'].format(
                            card.get('pan'),
                            card.get('user', {}).get('email'),
                            card.get('user', {}).get('phone_number')
                        ),
                        reply_markup=self.kb.delete_card_btn(card.get('id'))
                    )
                    msg_ids[card['id']] = msg.message_id

                await state.update_data(msg_ids=msg_ids)

                status_code, menu_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=MENU'
                )

                await message.answer(
                    menu_msg,
                    reply_markup=self.kb.menu_btn()
                )

            else:
                await message.answer(
                    MESSAGES['EMPTY_PAYMENTS'],
                    reply_markup=self.kb.settings_btn()
                )

        @self.router.callback_query(F.data.startswith('delete_card'))
        async def delete_user_card(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            card_id = callback.data.split('_')[-1]

            status_code, cards = await req_to_api(
                method='delete',
                url=f'payment-data/customer-data/removeCard?id={card_id}'
            )

            await callback.message.answer(
                MESSAGES['CARD_WAS_DELETED'],
                reply_markup=self.kb.settings_btn()
            )



