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
            elif status == 'ожидается оплата':
                builder.row(
                    InlineKeyboardButton(text=f"💸 {order_address} {order_comment}",
                                         callback_data=f'point_{order_id}')
                )

            else:
                builder.row(
                    InlineKeyboardButton(text=f"{order_address} {order_comment}",
                                         callback_data=f'point_{order_id}')
                )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def points_menu_btn(self, order: dict, point_id: str) -> InlineKeyboardMarkup:
        """Отметка точки как обработана/не обработана"""

        builder = InlineKeyboardBuilder()
        status = order.get('status_data', {}).get('status_name')
        container_type = order.get('box_data', {}).get('box_name') if order.get('box_data') is not None else None
        container_count = order.get('box_count') if order.get('box_count') is not None else None

        builder.add(
            InlineKeyboardButton(text='Тип',
                                 callback_data=f'container_type_{point_id}')
        )
        builder.add(
            InlineKeyboardButton(text='Количество',
                                 callback_data=f'container_count_{point_id}')
        )

        if status != 'ожидается оплата' and container_type and container_count:
            builder.row(
                InlineKeyboardButton(text='Обработан',
                                     callback_data=f'finished_{point_id}')
            )
            if status != 'отменена':
                builder.row(
                    InlineKeyboardButton(text='Не обработан',
                                         callback_data=f'not_finished_{point_id}')
                )

        builder.row(
            InlineKeyboardButton(text='Оставить комментарий',
                                 callback_data=f'write_courier_comment_{point_id}')
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

    def choose_box_type(self, box_types: list[dict], order_id: str) -> InlineKeyboardMarkup:

        builder = InlineKeyboardBuilder()

        for box in box_types:
            builder.add(
                InlineKeyboardButton(
                    text=box.get('box_name'),
                    callback_data=f'box_id_{box.get("id")}'
                )
            )

        builder.adjust(2)

        builder.row(
            InlineKeyboardButton(
                text='Отменить изменения',
                callback_data=f'cancel_change_{order_id}'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def choose_box_count(self, order_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for number in range(1, 9):
            builder.add(
                InlineKeyboardButton(
                    text=str(number),
                    callback_data=f'box_count_{number}'
                )
            )

        builder.adjust(4)
        builder.row(
            InlineKeyboardButton(
                text='Отменить изменения',
                callback_data=f'cancel_change_{order_id}'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def yes_or_no_btn(self, order_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(text='Да',
                                 callback_data=f'courier_yes_{order_id}')
        )
        builder.add(
            InlineKeyboardButton(text='Нет',
                                 callback_data=f'courier_no_{order_id}')
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )


