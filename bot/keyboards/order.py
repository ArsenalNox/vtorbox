import datetime

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from datetime import datetime

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class OrderKeyboard(BaseKeyboard):


    def choose_date_btn(self, current_time: datetime, is_show_today_button: bool) -> ReplyKeyboardMarkup:
        """Кнопки с выбором дня при создании заявки"""

        choose = ['Сегодня', 'Завтра', 'Послезавтра']

        builder = ReplyKeyboardBuilder()

        # если время больше 13:00, то кнопку 'сегодня не показывать'
        if not is_show_today_button:
            choose = choose[1:]

        for day in choose:
            builder.button(
                text=day
            )

        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])

        )
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

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

    def address_list_btn(self, address_list: list, flag_to_return: bool = False) -> InlineKeyboardMarkup:
        """Список адресов при создании адреса"""

        builder = InlineKeyboardBuilder()
        for address in address_list:
            builder.button(
                text=address,
                callback_data=f'get_address_{address["address_id"]}'
            )

        builder.button(
            text='Добавить новый адрес',
            callback_data=f'add_address_{flag_to_return}'
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def choose_container_btn(self) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()

        builder.button(
            text='Тип 1'
        )
        builder.button(
            text='Тип 2'
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def count_container_btn(self) -> ReplyKeyboardMarkup:
        """Кнопки с цифрами для количества контейнеров при создании заказе"""

        builder = ReplyKeyboardBuilder()

        for i in range(1, 11):

            builder.button(
                text=str(i)
            )

        builder.adjust(4)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
