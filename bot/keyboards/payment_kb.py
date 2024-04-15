from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard


class PaymentKeyboard(BaseKeyboard):

    def delete_card_btn(self, card_id: str) -> InlineKeyboardMarkup:
        """Удаление карты оплаты пользователя"""

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text='Удалить',
                                 callback_data=f'delete_card_{card_id}')
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )