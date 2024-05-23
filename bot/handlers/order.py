import datetime
import json
from urllib.parse import quote

from aiogram import Bot, Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.keyboards.order import OrderKeyboard
from bot.keyboards.questionnaire_kb import QuestionnaireKeyboard
from bot.states.states import CreateOrder, YesOrNo
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn, format_orders_statuses_text
from bot.utils.handle_data import show_order_info, group_orders_by_month, \
    show_active_orders, show_address_date
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class OrderHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = OrderKeyboard()
        self.questionnaire_kb = QuestionnaireKeyboard()
        self.orders_list = []
        self.index = 0

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['CREATE_ORDER']))
        async def create_order(message: Message, state: FSMContext):
            """Создание заявки"""

            await state.update_data(chat_id=message.chat.id)
            await state.update_data(menu_view='menu')
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            # запрос на получение всех адресов данного юзера
            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={message.chat.id}',
            )

            # флаг для возврата к созданию заказа(после того как во время создания заказа пользователь нажмет 'Добавить адрес')
            flag_to_return = True

            status_code, choose_address_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=CHOOSE_ADDRESS_ORDER'
            )

            msg = await message.answer(
                choose_address_msg,
                reply_markup=self.kb.address_list_btn(address_list, flag_to_return)
            )
            await state.update_data(msg=msg.message_id)

            status_code, menu_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=GO_TO_MENU'
            )

            await message.answer(
                menu_msg,
                reply_markup=self.kb.menu_btn()
            )

        @self.router.callback_query(F.data.startswith('getaddress'))
        async def get_order_address(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            address_id = callback.data.split('_')[1]
            is_container_switch_over = callback.data.split('_')[-1]
            # запрос на получение адреса по address_id
            status_code, address = await req_to_api(
                method='get',
                url=f'bot/user/addresses/{address_id}?tg_id={callback.message.chat.id}',
            )

            await state.update_data(address=address)

            if eval(is_container_switch_over):
                await show_address_date(
                    address=address,
                    message=callback.message,
                    kb=self.kb.choose_date_btn,
                    menu_kb=self.kb.start_menu_btn,
                    state=state
                )

            else:
                # если мы перешли сюда из меню изменения адреса при просмотре конкретной заявки
                order_id = data.get('order_id')
                update_order_data = json.dumps(
                    {
                        'address_id': address_id
                    }
                )
                # отправляем запрос на изменение адресу у заказа
                status_code, response = await req_to_api(
                    method='put',
                    url=f'orders/{order_id}',
                    data=update_order_data,
                )

                # получаем заявку по ее id
                status_code, order = await req_to_api(
                    method='get',
                    url=f'orders/{order_id}',
                )

                await show_order_info(
                    self=self,
                    message=callback.message,
                    order=order,
                    state=state
                )

        @self.router.message(CreateOrder.date)
        async def catch_order_date(message: Message, state: FSMContext):

            if message.text == BUTTONS['MENU']:
                await state.set_state(state=None)

                status_code, menu_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=MENU'
                )

                await message.answer(
                    menu_msg,
                    reply_markup=self.kb.start_menu_btn()
                )

            else:

                await state.update_data(chat_id=message.chat.id)
                _date = message.text.split('(')[0]
                date = datetime.datetime.strptime(_date, '%d-%m-%Y').strftime('%Y-%m-%d')
                await state.update_data(order_date=date)

                status_code, comment_order_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=WRITE_COMMENT_ORDER'
                )

                await message.answer(
                    comment_order_msg,
                    reply_markup=self.kb.empty_comment_btn()
                )

                await state.set_state(CreateOrder.comment)

        @self.router.message(CreateOrder.comment)
        async def get_comment_order(message: Message, state: FSMContext):
            """Получаем комментарий к заявке"""

            await state.update_data(chat_id=message.chat.id)
            comment = message.text
            data = await state.get_data()

            # получаем данные из состояния и отправляем запрос в бэк на создание заявки
            create_order_data = json.dumps(
                {
                    "address_id": data.get('address', {}).get('id'),
                    "day": data.get('order_date'),
                    "from_user": str(message.from_user.id),
                    "comment": comment
                }
            )

            await req_to_api(
                method='post',
                url='orders/create',
                data=create_order_data,
            )

            status_code, created_order_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=ORDER_WAS_CREATED'
            )

            await message.answer(
                created_order_msg,
                reply_markup=self.kb.start_menu_btn()
            )

            # переходим в главное меню
            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={message.from_user.id}',
            )

            if orders:
                await show_active_orders(
                    message=message,
                    orders=orders,
                    state=state,
                    self=self
                )

        @self.router.message(F.text.startswith(BUTTONS['ORDER_HISTORY']))
        async def order_history(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            await state.update_data(menu_view='menu')
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={message.from_user.id}',
            )
            if orders:

                self.orders_list = orders
                self.index = len(self.orders_list) - 1
                logger.debug(f'История заявок:::Список заявок у {message.chat.id} = {[i.get("order_num") for i in self.orders_list]}(index={self.index})')

                if len(orders) <= 3:

                    status_code, orders_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=YOUR_ORDERS'
                    )

                    msg = await message.answer(
                        orders_msg,
                        reply_markup=self.kb.order_list(orders)
                    )
                    await state.update_data(msg=msg.message_id)

                else:
                    result = await group_orders_by_month(self.orders_list)

                    status_code, orders_by_month_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=YOUR_ORDERS_BY_MONTH'
                    )

                    msg = await message.answer(
                        orders_by_month_msg,
                        reply_markup=self.kb.order_list_by_month(result)
                    )

                    await state.update_data(msg=msg.message_id)

            else:

                status_code, no_order_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=NO_ORDER'
                )

                await message.answer(
                    no_order_msg,
                    reply_markup=self.kb.start_menu_btn()
                )

            status_code, menu_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=MENU'
            )

            await message.answer(
                menu_msg,
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('ordershistory'))
        async def get_order_by_month(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки заказов за месяц"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            orders_order_num: list[str] = callback.data.split('_')[1:]
            params = ''  # параметр запроса со списком order_num
            for order_num in orders_order_num:
                params += f'order_nums={order_num}&'

            params = params.rstrip('&')

            # запрос на получение заказов по списку id
            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={callback.message.chat.id}&{params}',
            )

            status_code, orders_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=YOUR_ORDERS'
            )

            msg = await callback.message.answer(
                orders_msg,
                reply_markup=self.kb.order_list(orders)
            )
            await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('go_to_month_list_order'))
        async def back_to_list_order_by_month(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={callback.message.chat.id}',
            )
            self.orders_list = orders
            self.index = len(self.orders_list) - 1
            result = await group_orders_by_month(self.orders_list)

            status_code, orders_by_month_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=YOUR_ORDERS_BY_MONTH'
            )

            msg = await callback.message.answer(
                orders_by_month_msg,
                reply_markup=self.kb.order_list_by_month(result)
            )

            await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('show'))
        async def show_active_order(callback: CallbackQuery, state: FSMContext):
            """Просмотр активной заявки пользователя"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            status_code, orders = await req_to_api(
                method='get',
                url=f'users/orders/?tg_id={callback.message.chat.id}',
            )
            self.orders_list = orders
            logger.debug(f'Активные заявки:::Список заявок у {callback.message.chat.id} = {[i.get("order_num") for i in self.orders_list]}(index={self.index})')
            self.index = len(self.orders_list) - 1

            order = self.orders_list[self.index]
            await show_order_info(
                state=state,
                message=callback.message,
                order=order,
                self=self
            )

            status_code, menu_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=MENU'
            )

            await callback.message.answer(
                menu_msg,
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(or_f(F.data.startswith('previous'), F.data.startswith('next')))
        async def get_next_or_previous_order(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            if callback.data.startswith('next'):
                self.index -= 1
            else:
                self.index += 1

            try:

                # выводим данные о заказе
                order = self.orders_list[self.index]
                logger.debug(f'Стрелочки:::Список заявок у {callback.message.chat.id} = {[i.get("id") for i in self.orders_list]}(index={self.index})')

                await show_order_info(
                    state=state,
                    message=callback.message,
                    order=order,
                    self=self
                )

            except IndexError:
                self.index = None

                status_code, menu_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=GO_TO_MENU'
                )

                await callback.message.answer(
                    menu_msg,
                    reply_markup=self.kb.menu_btn()
                )

        @self.router.callback_query(F.data.startswith('payment'))
        async def payment_order(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            await state.update_data(msg=callback.message.message_id)
            data = await state.get_data()
            if data.get('order_msg'):
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('order_msg'),
                    reply_markup=None
                )

            order_id = callback.data.split('_')[-1]
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )
            order_status = order.get('status_data', {}).get('status_name').lower()

            status_code, payment_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=PAYMENT_ORDER'
            )

            await callback.message.answer(
                payment_msg
            )
            status_code, response = await req_to_api(
                method='post',
                url=f'payment?for_order={order_id}'
            )
            logger.debug(f'Получена ссылка для оплаты заказа {order_id}: {response}')

            if isinstance(response[0], dict) and order_status == 'ожидается оплата':
                status_code, link_payment_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=YOUR_LINK_PAYMENT'
                )
                await callback.message.answer(
                    link_payment_msg.format(
                        response[0].get('payment_url')
                    )
                )
                status_code, menu_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=MENU'
                )

                await callback.message.answer(
                    menu_msg,
                    reply_markup=self.kb.start_menu_btn()
                )

            elif order_status != 'ожидается оплата':
                await callback.message.answer(
                    MESSAGES['ORDER_ALREADY_PAID']
                )
                status_code, menu_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=MENU'
                )

                await callback.message.answer(
                    menu_msg,
                    reply_markup=self.kb.start_menu_btn()
                )

            else:
                await callback.message.answer(
                    MESSAGES['PLEASE_ADD_NUMBER_OR_EMAIL'],
                    reply_markup=self.kb.settings_btn()
                )

        @self.router.callback_query(F.data.startswith('history'))
        async def history_order(callback: CallbackQuery, state: FSMContext):
            """История изменения статусов у конкретного заказа"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            order_id = callback.data.split('_')[1]
            order_num = callback.data.split('_')[2]

            # получаем историю изменения статуса у данного заказа
            status_code, orders_statuses = await req_to_api(
                method='get',
                url=f'orders/{order_id}/history?tg_id={callback.message.chat.id}',
            )
            orders_statuses.reverse()

            order_text = format_orders_statuses_text(orders_statuses)

            status_code, history_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=ORDER_HISTORY'
            )

            msg = await callback.message.answer(
                history_msg.format(
                    order_num,
                    order_text
                ),
                reply_markup=self.kb.back_to_order(order_id)
            )

            await state.update_data(msg=msg.message_id)

            status_code, menu_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=MENU'
            )

            await callback.message.answer(
                menu_msg,
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('backtoorder'))
        async def back_to_order(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки 'Назад к просмотру заявки' """

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            order_id = callback.data.split('_')[-1]

            # получаем заявку по ее id
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_order_info(
                state=state,
                message=callback.message,
                order=order,
                self=self
            )

            status_code, menu_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=MENU'
            )

            await callback.message.answer(
                menu_msg,
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(or_f(F.data.startswith('approve'), F.data.startswith('refuse')))
        async def approve_order(callback: CallbackQuery, state: FSMContext):
            """Подтверждение заказа"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            action = callback.data.split('_')[0]
            order_id = callback.data.split('_')[-1]
            await state.update_data(action=action)
            await state.update_data(order_id=order_id)

            status_code, yes_or_no_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=QUESTION_YES_NO'
            )

            msg = await callback.message.answer(
                yes_or_no_msg,
                reply_markup=self.kb.yes_or_no_btn()
            )
            await state.set_state(YesOrNo.question)
            await state.update_data(del_msg=msg.message_id)

        @self.router.message(YesOrNo.question, F.text.lower() == 'да')
        async def catch_question_answer_yes(message: Message, state: FSMContext):

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await state.set_state(state=None)

            if data.get('action') == 'approve':
                status = quote("подтверждена")
            else:
                status = quote("отменена")

            order_id = data.get('order_id')

            # запрос на изменение статуса у заявки на 'подтверждена'
            status_code, result = await req_to_api(
                method='put',
                url=f'orders/{order_id}/status?status_text={status}',
            )

            # получаем заявку по ее id
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_order_info(
                state=state,
                message=message,
                order=order,
                self=self
            )

        @self.router.callback_query(F.data.startswith('order'))
        async def get_order(callback: CallbackQuery, state: FSMContext):

            data = await state.get_data()

            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            await state.update_data(chat_id=callback.message.chat.id)
            order_id = callback.data.split('_')[-1]

            # получаем заявку по ее id
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            # получаем индекс из номера заказа для данного пользователя
            self.index = order.get('user_order_num') - 1

            await show_order_info(
                state=state,
                message=callback.message,
                order=order,
                self=self
            )

        @self.router.callback_query(F.data.startswith('changeaddress'))
        async def change_address_from_order(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            if data.get('order_msg'):
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('order_msg'),
                    reply_markup=None
                )
                await state.update_data(order_msg=None)
                
            order_id = callback.data.split('_')[-1]

            await state.update_data(order_id=order_id)

            # запрос на получение всех адресов данного юзера
            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={callback.message.chat.id}',
            )

            status_code, choose_address_msg = await req_to_api(
                method='get',
                url='bot/messages?message_key=CHOOSE_ADDRESS_ORDER'
            )

            msg = await callback.message.answer(
                choose_address_msg,
                reply_markup=self.kb.address_list_btn(address_list, is_container_switch_over=False)
            )
            await state.update_data(msg=msg.message_id)
