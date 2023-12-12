from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.services.users import UserService
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

    def add_address_btn(self) -> ReplyKeyboardMarkup:
        """Кпопки в меню адресов"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['ADD_ADDRESS'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['DEFAULT']),
            KeyboardButton(text=BUTTONS['DELETE_ADDRESS'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def send_geo(self) -> ReplyKeyboardMarkup:
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

    def addresses_list_btn(self, tg_id: int, tag: str = 'address'):
        """Inline кнопки со списком адресов пользователя"""

        # получаем все адреса пользователя
        addresses = UserService.get_users_addresses_without_main(tg_id)
        builder = InlineKeyboardBuilder()

        for address in addresses:
            builder.row(
                InlineKeyboardButton(
                    text=address.address,
                    callback_data=f'{tag}_{address.id}'
                )
            )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
