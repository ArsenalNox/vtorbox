import datetime
import pprint
from urllib.parse import quote

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from datetime import datetime

from bot.keyboards.base_keyboards import BaseKeyboard
from bot.utils.buttons import BUTTONS
from bot.utils.handle_data import convert_date, translate_day
from bot.utils.messages import MESSAGES


class OrderKeyboard(BaseKeyboard):

    def choose_date_btn(self, work_days: list[dict]) -> ReplyKeyboardMarkup:
        """Кнопки с выбором дня при создании заявки"""

        builder = ReplyKeyboardBuilder()
        for day in work_days:
            date = convert_date(day.get('date'))
            ru_day = translate_day(day.get('weekday'))
            builder.add(
                KeyboardButton(
                    text=f'{date}({ru_day})'
                )
            )

        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])

        )
        builder.adjust(2)
        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def order_menu_btn(self, order: dict, orders_list: list[dict], index: int) -> InlineKeyboardMarkup:
        """Меню для управление заказом"""

        builder = InlineKeyboardBuilder()
        order_id = order.get('id')
        order_num = order.get('order_num')
        manager_id = order.get('manager_info', {}).get('telegram_id')
        manager_username = order.get('manager_info', {}).get('telegram_username')
        manager_link = f'https://t.me/{manager_username}' if manager_username else f'tg://user?id={manager_id}'

        # ---------------------------Логика вывода стрелочек для переключения--------------------------------------
        try:
            orders_list[index + 1]
        except IndexError:
            pass
        else:
            builder.row(
                InlineKeyboardButton(
                    text=BUTTONS['PREVIOUS'],
                    callback_data=f'previous_{order_id}'
                )
            )

        if index != 0:
            # пытаемся получить следующую запись
            try:
                orders_list[index - 1]
            except IndexError:
                pass
            else:
                builder.add(
                    InlineKeyboardButton(
                        text=BUTTONS['NEXT'],
                        callback_data=f'next_{order_id}'
                    )
                )

        # --------------------------------------------КОНЕЦ----------------------------------------------------

        if order.get('status_data', {}).get('status_name') == 'ожидается оплата':
            builder.row(
                InlineKeyboardButton(
                    text='Оплатить',
                    callback_data=f'payment_{order_id}'
                )
            )

        if order.get('status_data', {}).get('status_name') == 'ожидается подтверждение':
            builder.row(
                InlineKeyboardButton(
                    text='Подтвердить',
                    callback_data=f'approve_{order_id}'
                ),
                InlineKeyboardButton(
                    text='Отказаться',
                    callback_data=f'refuse_{order_id}'
                )
            )

        if order.get('status_data', {}).get('status_name') in ('ожидается подтверждение', 'подтверждена'):
            builder.row(
                InlineKeyboardButton(
                    text='Изменить адрес',
                    callback_data=f'changeaddress_{order_id}'
                )
            )

        if order.get('status_data', {}).get('status_name') in ('создана', 'в работе', 'ожидается подтверждение', 'подтверждена', 'передана курьеру', 'ожидается оплата', 'оплаченна'):
            builder.row(
                InlineKeyboardButton(
                    text='Отменить',
                    callback_data=f'cancel_{order_id}',
                    url=manager_link
                ),
            InlineKeyboardButton(
                text='Связаться с менеджером',
                callback_data=f'manager_{order_id}',
                url=manager_link
            ),
            )

        builder.row(
            InlineKeyboardButton(
                text='История изменения заявки',
                callback_data=f'history_{order_id}_{order_num}'
            ),
        )



        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def address_list_btn(self, address_list: list, flag_to_return: bool = False, is_container_switch_over: bool = True) -> InlineKeyboardMarkup:
        """Список адресов при создании адреса"""

        builder = InlineKeyboardBuilder()
        for address in address_list:
            address_id = address['id']
            builder.row(
                InlineKeyboardButton(
                    text=address['address'],
                    callback_data=f'getaddress_{address_id}_{is_container_switch_over}'
                )

            )

        builder.row(
            InlineKeyboardButton(
                text='Добавить новый адрес',
                callback_data=f'add_address_{flag_to_return}')

        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def choose_container_btn(self, containers_types: list[dict]) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()

        for c_type in containers_types:
            builder.button(
                text=c_type['box_name']
            )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def count_container_btn(self) -> ReplyKeyboardMarkup:
        """Кнопки с цифрами для количества контейнеров при создании заказе"""

        builder = ReplyKeyboardBuilder()

        for i in range(1, 11):

            builder.button(
                text=str(i)
            )

        builder.adjust(4)

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def back_to_order(self, order_id: str) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text=BUTTONS['BACK_TO_ORDER'],
                callback_data=f'backtoorder_{order_id}'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def yes_or_no_btn(self) -> ReplyKeyboardMarkup:
        """Кнопки да/нет для уточнения у юзера"""

        builder = ReplyKeyboardBuilder()

        builder.add(
            KeyboardButton(
                text='Да'
            )
        )
        builder.add(
            KeyboardButton(
                text='Нет'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def order_list(self, orders: list[dict]) -> InlineKeyboardMarkup:
        """Кнопки со списком заявок"""

        builder = InlineKeyboardBuilder()

        for order in orders:
            date = convert_date(order.get('day'))
            id = order.get('id')
            number = order.get('order_num')
            if order.get('status_data', {}).get('status_name') == 'выполнена':
                builder.row(
                    InlineKeyboardButton(
                        text=f'✅ Заявка № {number}, дата: {date}',
                        callback_data=f'order_{id}'
                    )
                )
            else:
                builder.row(
                    InlineKeyboardButton(
                        text=f'⏳ Заявка # {number}, дата: {date}',
                        callback_data=f'order_{id}'
                    )
                )

        builder.row(
            InlineKeyboardButton(
                text='⬅️ Назад',
                callback_data=f'go_to_month_list_order'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def order_list_by_month(self, orders: dict):
        """Кнопки отображения истории заказов по месяцам"""

        builder = InlineKeyboardBuilder()
        for order in orders:
            orders_id = '_'.join(orders[order])
            builder.row(
                InlineKeyboardButton(
                    text=f'{order} ({len(orders[order])})',
                    callback_data=f'ordershistory_{orders_id}'
                )
            )

        return builder.as_markup(
                    resize_keyboard=True,
                    one_time_keyboard=True
                )

    def change_container(self, order_id: str) -> InlineKeyboardMarkup:
        """Кнопки для изменения типа или количество контейнеров"""

        builder = InlineKeyboardBuilder()

        builder.add(
            InlineKeyboardButton(
                text='Тип',
                callback_data='change_container_type'
            )
        )
        builder.add(
            InlineKeyboardButton(
                text='Кол-во',
                callback_data='change_container_count'
            )
        )
        builder.row(
            InlineKeyboardButton(
                text=BUTTONS['BACK_TO_ORDER'],
                callback_data=f'backtoorder_{order_id}'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def empty_comment_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка для пустого комментария"""

        builder = ReplyKeyboardBuilder()
        builder.button(
            text='Без комментария'
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )