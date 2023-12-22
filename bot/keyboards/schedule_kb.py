from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard


class ScheduleKeyboard(BaseKeyboard):

    def change_schedule_btn(self) -> ReplyKeyboardMarkup:
        """Кпопки для изменения расписаний вызова"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text='По запросу'),
            KeyboardButton(text='По расписанию')
        )

        builder.row(
            KeyboardButton(text='Назад'),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def schedule_period_btn(self) -> ReplyKeyboardMarkup:
        """Выбор периода для создания пользовательского расписания"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text='Дни недели'),
            KeyboardButton(text='Дни месяца')
        )

        builder.row(
            KeyboardButton(text='Назад'),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )


