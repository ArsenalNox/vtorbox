import pprint

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.requests_to_api import req_to_api


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

    async def points_btn(self, routes: dict) -> InlineKeyboardMarkup:
        """Кпопки с точками маршрута"""

        builder = InlineKeyboardBuilder()
        orders = routes.get('orders')

        for order in orders:
            order_id = order.get('order_id')
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            order_address = order.get('address_data', {}).get('address')
            order_comment = order.get('address_data', {}).get('comment') if order.get('address_data', {}).get('comment') else ' '
            status = order.get('status_data', {}).get('status_name')
            if status == 'передана курьеру':
                builder.row(
                    InlineKeyboardButton(text=f"⏳ {order_address} {order_comment}",
                                         callback_data=f'point_{order_id}')
                )
            elif status == 'отменена':
                builder.row(
                    InlineKeyboardButton(text=f"🔴 {order_address} {order_comment}",
                                         callback_data=f'point_{order_id}')
                )

            elif status == 'обработанна':
                builder.row(
                    InlineKeyboardButton(text=f"🟢 {order_address} {order_comment}",
                                         callback_data=f'point_{order_id}')
                )


        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def points_menu_btn(self, point_id: str) -> InlineKeyboardMarkup:
        """Отметка точки как обработана/не обработана"""

        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(text='Тип',
                                 callback_data=f'container_type_{point_id}')
        )
        builder.add(
            InlineKeyboardButton(text='Количество',
                                 callback_data=f'container_count_{point_id}')
        )

        builder.row(
            InlineKeyboardButton(text='Обработан',
                                 callback_data=f'finished_{point_id}')
        )
        builder.row(
            InlineKeyboardButton(text='Не обработан',
                                 callback_data=f'not_finished_{point_id}')
        )
        builder.row(
            InlineKeyboardButton(text='Назад к списку заявок',
                                 callback_data=f'back_order_list')
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

    def choose_box_type(self, box_types: list[dict]) -> ReplyKeyboardMarkup:

        builder = ReplyKeyboardBuilder()

        for box in box_types:
            builder.row(
                KeyboardButton(text=box.get('box_name'))
            )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def choose_box_count(self) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()

        for number in range(1, 11):
            builder.row(
                KeyboardButton(text=str(number))
            )

        builder.adjust(4)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
