import datetime
import json
import pprint
from urllib.parse import quote

from aiogram import Bot, Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.order import OrderKeyboard
from bot.states.states import CreateOrder, YesOrNo, ChangeOrder
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn, format_orders_statuses_text
from bot.utils.handle_data import validate_date, get_order_data, show_order_info, group_orders_by_month, \
    show_active_orders
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class OrderHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = OrderKeyboard()
        self.orders_list = None
        self.index = 0

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['CREATE_ORDER']))
        async def create_order(message: Message, state: FSMContext):
            """Создание заявки"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['CREATE_ORDER']
            )

            # получаем текущее время для отображения кнопки 'сегодня'
            current_time = datetime.datetime.now()
            deadline = datetime.datetime.strptime('13:00', "%H:%M")
            is_show_today_button = True if current_time < deadline else False

            await message.answer(
                MESSAGES['CHOOSE_DATE_ORDER'],
                reply_markup=self.kb.choose_date_btn(current_time, is_show_today_button)
            )

            await state.set_state(CreateOrder.date)

        @self.router.message(CreateOrder.date)
        async def get_date_order(message: Message, state: FSMContext):

            if message.text.lower() in ['сегодня', 'завтра', 'послезавтра']:

                date = get_order_data(message.text.lower())
                await state.update_data(order_date=date)
                await get_address_order(
                    message=message,
                    state=state
                )
            else:
                check_date = validate_date(message.text)
                if check_date:
                    await state.update_data(order_date=message.text)
                    await get_address_order(
                        message=message,
                        state=state
                    )

                else:
                    await message.answer(
                        MESSAGES['WRONG_ORDER_DATE']
                    )

            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(CreateOrder.address)
        async def get_address_order(message: Message, state: FSMContext):

            # запрос на получение всех адресов данного юзера
            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={message.from_user.id}',
            )

            # флаг для возврата к созданию заказа(после того как во время создания заказа пользователь нажмет 'Добавить адрес')
            flag_to_return = True
            msg = await message.answer(
                MESSAGES['CHOOSE_ADDRESS_ORDER'],
                reply_markup=self.kb.address_list_btn(address_list, flag_to_return)
            )
            await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('getaddress'))
        async def get_order_address(callback: CallbackQuery, state: FSMContext):
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
                # запрос на получение типов контейнера из БД
                status_code, containers_types = await req_to_api(
                    method='get',
                    url=f'boxes',
                )

                await callback.message.answer(
                    MESSAGES['CHOOSE_CONTAINER'],
                    reply_markup=self.kb.choose_container_btn(containers_types)
                )
                await state.set_state(CreateOrder.container)

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

        @self.router.message(F.text, CreateOrder.container)
        async def get_container_type(message: Message, state: FSMContext):

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await state.update_data(container=message.text)
            await message.answer(
                MESSAGES['CHOOSE_COUNT_CONTAINER'],
                reply_markup=self.kb.count_container_btn()
            )
            await state.set_state(CreateOrder.count_container)

        @self.router.message(F.text, CreateOrder.count_container)
        async def get_count_container(message: Message, state: FSMContext):
            """Получаем количество контейнров и создаем заказ"""

            await state.update_data(count_container=message.text)
            data = await state.get_data()

            # получаем данные из состояния и отправляем запрос в бэк на создание заявки
            create_order_data = json.dumps(
                {
                    "address_id": data.get('address', {}).get('id'),
                    "box_count": data.get('count_container'),
                    "box_name": data.get('container'),
                    "day": data.get('order_date'),
                    "from_user": str(message.from_user.id)
                }
            )

            await req_to_api(
                method='post',
                url='orders/create',
                data=create_order_data,
            )

            await message.answer(
                MESSAGES['ORDER_WAS_CREATED'],
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

                if len(orders) <= 1:
                    msg = await message.answer(
                        MESSAGES['YOUR_ORDERS'],
                        reply_markup=self.kb.order_list(orders)
                    )
                    await state.update_data(msg_order_history=msg.message_id)

                else:
                    result = await group_orders_by_month(self.orders_list)
                    msg = await message.answer(
                        MESSAGES['YOUR_ORDERS_BY_MONTH'],
                        reply_markup=self.kb.order_list_by_month(result)
                    )

                    await state.update_data(msg=msg.message_id)

            else:
                await message.answer(
                    MESSAGES['NO_ORDER'],
                    reply_markup=self.kb.start_menu_btn()
                )

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('ordershistory'))
        async def get_order_by_month(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки заказов за месяц"""

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

            msg = await callback.message.answer(
                MESSAGES['YOUR_ORDERS'],
                reply_markup=self.kb.order_list(orders)
            )
            await state.update_data(msg_order_history=msg.message_id)

        @self.router.callback_query(F.data.startswith('show'))
        async def show_active_order(callback: CallbackQuery, state: FSMContext):
            """Просмотр активной заявки пользователя"""

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

            order = self.orders_list[self.index]
            await show_order_info(
                state=state,
                message=callback.message,
                order=order,
                self=self
            )
            await callback.message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(or_f(F.data.startswith('previous'), F.data.startswith('next')))
        async def get_next_or_previous_order(callback: CallbackQuery, state: FSMContext):
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

                await show_order_info(
                    state=state,
                    message=callback.message,
                    order=order,
                    self=self
                )

            except IndexError:
                self.index = None

                await callback.message.answer(
                    MESSAGES['GO_TO_MENU'],
                    reply_markup=self.kb.menu_btn()
                )

        @self.router.callback_query(F.data.startswith('payment'))
        async def payment_order(callback: CallbackQuery, state: FSMContext):

            order_id = callback.data.split('_')[-1]
            link = 'https://google.com'
            await callback.message.answer(
                MESSAGES['PAYMENT_ORDER'].format(
                    order_id,
                    link
                )
            )

            await callback.message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.callback_query(F.data.startswith('history'))
        async def history_order(callback: CallbackQuery, state: FSMContext):
            """История изменения статусов у конкретного заказа"""

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

            order_text = format_orders_statuses_text(orders_statuses)

            msg = await callback.message.answer(
                MESSAGES['ORDER_HISTORY'].format(
                    order_num,
                    order_text
                ),
                reply_markup=self.kb.back_to_order(order_id)
            )

            await state.update_data(msg=msg.message_id)

            await callback.message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('backtoorder'))
        async def back_to_order(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки 'Назад к просмотру заявки' """

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

            await callback.message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.callback_query(or_f(F.data.startswith('approve'), F.data.startswith('refuse')))
        async def approve_order(callback: CallbackQuery, state: FSMContext):
            """Подтверждение заказа"""

            data = await state.get_data()

            action = callback.data.split('_')[0]
            order_id = callback.data.split('_')[-1]
            await state.update_data(action=action)
            await state.update_data(order_id=order_id)

            msg = await callback.message.answer(
                MESSAGES['QUESTION_YES_NO'],
                reply_markup=self.kb.yes_or_no_btn()
            )
            await state.set_state(YesOrNo.question)
            await state.update_data(del_msg=msg.message_id)

        @self.router.message(YesOrNo.question, F.text.lower() == 'да')
        async def catch_question_answer_yes(message: Message, state: FSMContext):

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

            await message.bot.edit_message_reply_markup(
                chat_id=data.get('chat_id'),
                message_id=data.get('order_msg'),
                reply_markup=self.kb.order_menu_btn(order, self.orders_list, self.index)
            )

        @self.router.callback_query(F.data.startswith('order'))
        async def get_order(callback: CallbackQuery, state: FSMContext):
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

            msg = await callback.message.answer(
                MESSAGES['CHOOSE_ADDRESS_ORDER'],
                reply_markup=self.kb.address_list_btn(address_list, is_container_switch_over=False)
            )
            await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('changecontainer'))
        async def change_container_from_order(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()
            order_id = callback.data.split('_')[-1]

            if data.get('order_msg'):
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('order_msg'),
                    reply_markup=None
                )

            await state.update_data(order_id=order_id)

            container_msg = await callback.message.answer(
                MESSAGES['CHOOSE_CHANGE_CONTAINER'],
                reply_markup=self.kb.change_container(order_id)
            )
            await state.update_data(container_msg=container_msg.message_id)

        @self.router.callback_query(F.data.startswith('change_container_type'))
        async def change_container_type_from_order(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            if data.get('container_msg'):
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('container_msg'),
                    reply_markup=None
                )
                await state.update_data(container_msg=None)

            # запрос на получение типов контейнера из БД
            status_code, containers_types = await req_to_api(
                method='get',
                url=f'boxes',
            )

            await callback.message.answer(
                MESSAGES['CHOOSE_CONTAINER'],
                reply_markup=self.kb.choose_container_btn(containers_types)
            )

            await state.set_state(ChangeOrder.container_type)

        @self.router.message(ChangeOrder.container_type)
        async def catch_container_type_from_order(message: Message, state: FSMContext):

            data = await state.get_data()

            await state.set_state(state=None)

            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            order_id = data.get('order_id')
            update_order_data = json.dumps(
                {
                    'box_name': message.text
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
                message=message,
                order=order,
                state=state
            )

        @self.router.callback_query(F.data.startswith('change_container_count'))
        async def change_container_count_from_order(callback: CallbackQuery, state: FSMContext):
            data = await state.get_data()

            if data.get('container_msg'):
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('container_msg'),
                    reply_markup=None
                )
                await state.update_data(container_msg=None)

            await callback.message.answer(
                MESSAGES['CHOOSE_COUNT_CONTAINER'],
                reply_markup=self.kb.count_container_btn()
            )

            await state.set_state(ChangeOrder.container_count)

        @self.router.message(ChangeOrder.container_count)
        async def catch_container_count_from_order(message: Message, state: FSMContext):

            data = await state.get_data()
            await state.set_state(state=None)

            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            order_id = data.get('order_id')

            update_order_data = json.dumps(
                {
                    'box_count': message.text
                }
            )

            # отправляем запрос на изменение количества контейнеров у заказа
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
                message=message,
                order=order,
                state=state
            )
