from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS


class CourierKeyboard(BaseKeyboard):

    def routes_menu(self, route_link: str) -> InlineKeyboardMarkup:
        """Кпопки для курьера с картой и точками маршрута"""

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text='Точки маршрута',
                                 callback_data=f'points_route')
        )
        builder.row(
            InlineKeyboardButton(text='Карта маршрута',
                                 callback_data=f'map_route',
                                 url=route_link)
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def points_btn(self, routes: list[dict]) -> InlineKeyboardMarkup:
        """Кпопки с точками маршрута"""

        builder = InlineKeyboardBuilder()
        point_id = 1
        for route in routes:
            builder.row(
                InlineKeyboardButton(text=route.get('name'),
                                     callback_data=f'point_{point_id}')
            )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def points_menu_btn(self) -> InlineKeyboardMarkup:
        """Отметка точки как обработана/не обработана"""

        builder = InlineKeyboardBuilder()

        builder.row(
            InlineKeyboardButton(text='Обработан',
                                 callback_data='finished')
        )
        builder.row(
            InlineKeyboardButton(text='Не обработан',
                                 callback_data='not_finished')
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def back_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка назад к меню курьера"""

        builder = ReplyKeyboardBuilder()

        builder.row(
            KeyboardButton(text=BUTTONS['BACK_ROUTE'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
