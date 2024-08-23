from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.utils.buttons import BUTTONS


class BaseKeyboard:

    def back_settings_btn(self) -> ReplyKeyboardMarkup:
        """Кпопка назад"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['BACK_SETTINGS'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

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

    def back_btn(self) -> ReplyKeyboardMarkup:
        """Кнопка НАЗАД """

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['BACK_SETTINGS']),
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
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

    def accept_deny_payment_btn(self, text: str, order_id: str, order_menu: str, flag: bool = False) -> InlineKeyboardMarkup:
        """ Кнопки 'Согласен/Не согласен' при оплате заявки """

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f'accept_deny_{order_menu}_{order_id}'
            ),
        )

        builder.row(
            InlineKeyboardButton(
                text='Перейти к оплате',
                callback_data=f'payment_{flag}_{order_id}'
            ),
        )

        if order_menu == 'True':
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

    def leave_door_yes_no_btn(self, order_id: str) -> InlineKeyboardMarkup:
        """ Кнопки Да/Нет при вопросе 'Оставить у двери'  """

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(
                text='Да',
                callback_data=f'leave_door_yes_{order_id}'
            ),
        )
        builder.add(
            InlineKeyboardButton(
                text='Нет',
                callback_data=f'leave_door_no_{order_id}'
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text='Назад',
                callback_data=f'back_leave_door_no_{order_id}'
            ),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def confirm_deny_order(self, order_id: str) -> InlineKeyboardMarkup:
        """ Кнопки подтверждения/отказаться  """

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text='Подтвердить',
                callback_data=f'confirm_order_{order_id}'
            ),
        )
        builder.row(
            InlineKeyboardButton(
                text='Отказаться',
                callback_data=f'deny_order_{order_id}'
            ),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def test_btn(self) -> InlineKeyboardMarkup:
        """ Кнопки подтверждения/отказаться  """

        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text='Подтвердить',
                callback_data=f'test',
                url='tg://user?id=111111'
            ),
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def back_schedule_address_list(self) -> ReplyKeyboardMarkup:
        """Кпопка назад"""

        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=BUTTONS['BACK_SCHEDULE_ADDRESS_LIST'])
        )
        builder.row(
            KeyboardButton(text=BUTTONS['MENU'])
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )

    def all_available_regions_btn(self):
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text='Показать все доступные районы',
                callback_data=f'all_available_regions'
            )
        )

        return builder.as_markup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
