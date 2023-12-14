from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class QuestionnaireKeyboard(BaseKeyboard):

    def questionnaire_btn(self) -> ReplyKeyboardMarkup:
        """Кпопки в меню анкеты"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['EDIT_QUESTIONNAIRE'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['PHONE_NUMBER']),
            KeyboardButton(text=BUTTONS['EMAIL'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def empty_comment_btn(self) -> InlineKeyboardMarkup:
        """Кнопка для пустого комментария в анкете"""

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text='Не добавлять комментарий',
                callback_data='empty_comment'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

