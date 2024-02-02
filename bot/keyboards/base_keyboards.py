from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.utils.buttons import BUTTONS


class BaseKeyboard:

    def start_menu_btn(self) -> ReplyKeyboardMarkup:
        """Меню управление заказами"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['CREATE_ORDER']),
            KeyboardButton(text=BUTTONS['ORDER_HISTORY'])

        )

        builder.row(
            KeyboardButton(text=BUTTONS['SETTINGS']),
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

    def start_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка на /start"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['START']),
        )
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def settings_btn(self) -> ReplyKeyboardMarkup:
        """ Кнопки в настройках бота """
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['QUESTIONNAIRE']),
            KeyboardButton(text=BUTTONS['SCHEDULE'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MY_ADDRESSES']),
            KeyboardButton(text=BUTTONS['PAYMENTS'])
        )
        builder.row(
           KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def registration_btn(self) -> ReplyKeyboardMarkup:
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

    def show_btn(self, first_order: dict) -> InlineKeyboardMarkup:
        """ Кнопки 'Просмотреть' на активной заявки """

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=BUTTONS['SHOW'],
                callback_data=f'show_{first_order["id"]}'
            ),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def courier_btn(self) -> ReplyKeyboardMarkup:
        """ Кнопка 'Маршрут' для курьера """

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(
                text=BUTTONS['ROUTE'],
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
