from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.services.users import UserService
from bot.utils.buttons import BUTTONS


class BaseKeyboard:

    def start_menu_btn(self) -> ReplyKeyboardMarkup:
        """Стартовое меню бота"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['CREATE_APPLICATION']),
            KeyboardButton(text=BUTTONS['APPLICATIONS_HISTORY']),
            KeyboardButton(text=BUTTONS['SETTINGS'])
        )

        builder.row(
            KeyboardButton(text=BUTTONS['NOTIFICATIONS']),
            KeyboardButton(text=BUTTONS['ABOUT'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def menu_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка на главное меню"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['MENU']),
        )
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def settings_btn(self) -> ReplyKeyboardMarkup:
        """ Кнопки в настройках бота """
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

    def registration_btn(self) ->ReplyKeyboardMarkup:
        """ Кнопки регистрации """

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['SHARE_PHONE'], request_contact=True),
            KeyboardButton(text=BUTTONS['START_BOT']),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )