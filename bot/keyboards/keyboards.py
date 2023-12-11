from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.utils.buttons import BUTTONS


class Keyboard:

    def start_menu_btn(self) -> ReplyKeyboardMarkup:
        """Стартовое меню бота"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['CREATE_APPLICATION']),
            KeyboardButton(text=BUTTONS['APPLICATIONS_HISTORY'])
        )

        builder.row(
            KeyboardButton(text=BUTTONS['NOTIFICATIONS']),
            KeyboardButton(text=BUTTONS['SETTINGS']),
            KeyboardButton(text=BUTTONS['ABOUT'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def settings_btn(self) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['MY_ADDRESSES']),
            KeyboardButton(text=BUTTONS['PAYMENTS']),
            KeyboardButton(text=BUTTONS['QUESTIONNAIRE'])
        )
        builder.row(
           KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def add_address_btn(self) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['ADD_ADDRESS'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )