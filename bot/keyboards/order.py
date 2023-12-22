from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class OrderKeyboard(BaseKeyboard):
    def order_menu_btn(self, order_id: int) -> InlineKeyboardMarkup:
        """Меню для управление заказом"""

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=BUTTONS['PREVIOUS'],
                callback_data=f'previous_{order_id}'
            ),
            InlineKeyboardButton(
                text='Оплатить',
                callback_data=f'payment_{order_id}'
            ),
            InlineKeyboardButton(
                text=BUTTONS['NEXT'],
                callback_data=f'next_{order_id}'
            )

        )

        builder.row(
            InlineKeyboardButton(
                text='Подтвердить',
                callback_data=f'approve_{order_id}'
            ),

            InlineKeyboardButton(
                text='Отказаться',
                callback_data=f'refuse_{order_id}'
            ),
            InlineKeyboardButton(
                text='Отменить',
                callback_data=f'cancel_{order_id}'
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text='Изменить адрес',
                callback_data=f'changeaddress_{order_id}'
            ),
            InlineKeyboardButton(
                text='Изменить тип/кол-во контейнеров',
                callback_data=f'changecontainer_{order_id}'
            ),
        )

        builder.row(
            InlineKeyboardButton(
                text='История изменения заявки',
                callback_data=f'history_{order_id}'
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text='Назад к списку',
                callback_data=f'backlist_{order_id}'
            ),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
