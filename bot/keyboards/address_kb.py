from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class AddressKeyboard(BaseKeyboard):

    def add_address_btn(self, flag_to_return: bool) -> InlineKeyboardMarkup:
        """Кпопки для добавления адреса"""

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text='➕ Добавить адрес',
                                 callback_data=f'add_address_{flag_to_return}')
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def address_delete_default_btn(self, address: dict) -> InlineKeyboardMarkup:
        """Кнопки для удаления и установки по дефолту для адреса"""

        builder = InlineKeyboardBuilder()
        if address.get('main'):
            builder.row(
                InlineKeyboardButton(text='❌ Удалить адрес',
                                     callback_data=f'delete_address_{address.get("id")}')
            )
        else:
            builder.row(
                InlineKeyboardButton(text='❌ Удалить адрес',
                                     callback_data=f'delete_address_{address.get("id")}')
            )
            builder.row(
                InlineKeyboardButton(text='🔘 Установить по умолчанию',
                                     callback_data=f'default_address_{address.get("id")}')
            )

        builder.adjust(2)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def send_geo_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка для отправки геопозиции"""

        builder = ReplyKeyboardBuilder()
        builder.button(
            text='📍Отправить геопозицию',
            request_location=True
        )
        builder.button(
            text=BUTTONS['MENU']
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def empty_comment_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка для пустого комментария"""

        builder = ReplyKeyboardBuilder()
        builder.button(
            text='Без комментария'
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def yes_or_no_btn(self) -> InlineKeyboardMarkup:

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text='Да',
                callback_data='found_address_yes'
            )
        )
        builder.add(
            InlineKeyboardButton(
                text='Нет',
                callback_data='found_address_no'
            )
        )
        builder.row(
            InlineKeyboardButton(
                text='Ввести адрес вручную',
                callback_data='manually_address'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def yes1_or_no1_btn(self) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text='Да',
                callback_data='save_address_yes'
            )
        )
        builder.add(
            InlineKeyboardButton(
                text='Нет',
                callback_data='save_address_no'
            )
        )
        builder.row(
            InlineKeyboardButton(
                text='Ввести адрес вручную',
                callback_data='manually_address'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
