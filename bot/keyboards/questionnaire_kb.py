from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class QuestionnaireKeyboard(BaseKeyboard):

    def questionnaire_btn(self) -> ReplyKeyboardMarkup:
        """Кпопки в меню анкеты"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['FIRST_NAME']),
            KeyboardButton(text=BUTTONS['LAST_NAME'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['PHONE_NUMBER']),
            KeyboardButton(text=BUTTONS['EMAIL'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU']),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def send_phone(self) -> ReplyKeyboardMarkup:
        """Кпопка для отправки телефона"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text='Отправить номер телефона', request_contact=True)
        )

        builder.row(
            KeyboardButton(text=BUTTONS['MENU']),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

