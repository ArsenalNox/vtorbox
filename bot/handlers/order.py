import datetime

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from zoneinfo import ZoneInfo

from bot.handlers.base_handler import Handler
from bot.keyboards.order import OrderKeyboard
from bot.states.states import CreateOrder
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.handle_data import validate_date
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class ApplicationHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = OrderKeyboard()

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
                await state.update_data(order_date=message.text)
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
            status_code, response = req_to_api(
                method='get',
                url=f'user/addresses/all?tg_id={message.from_user.id}',

            )
            address_list = response

            # флаг для возврата к созданию заказа(после того как во время создания заказа пользователь нажмет 'Добавить адрес')
            flag_to_return = True
            await message.answer(
                MESSAGES['CHOOSE_ADDRESS_ORDER'],
                reply_markup=self.kb.address_list_btn(address_list, flag_to_return)
            )

        @self.router.callback_query(F.data.startswith('get_address'))
        async def get_order_address(callback: CallbackQuery, state: FSMContext):

            address_id = callback.data.split('_')[-1]
            # запрос на получение адреса по address_id
            status_code, address = req_to_api(
                method='get',
                url=f'user/addresses/{address_id}?tg_id={callback.message.chat.id}'
            )

            await state.update_data(address=address)

            await callback.message.answer(
                MESSAGES['CHOOSE_CONTAINER'],
                reply_markup=self.kb.choose_container_btn()
            )
            await state.set_state(CreateOrder.container)

        @self.router.message(F.text, CreateOrder.container)
        async def get_container_type(message: Message, state: FSMContext):

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
            print(data)

            await message.answer(
                MESSAGES['ORDER_WAS_CREATED'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['ORDER_HISTORY']))
        async def order_history(message: Message, state: FSMContext):

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['APPLICATIONS_HISTORY']
            )

        @self.router.callback_query(F.data.startswith('show'))
        async def show_active_order(callback: CallbackQuery, state: FSMContext):
            """Просмотр активной заявки пользователя"""

            order_id = callback.data.split('_')[1]

            # получаем заказ по его id

            await callback.message.answer(
                MESSAGES['ORDER_INFO'],
                reply_markup=self.kb.order_menu_btn(order_id)
            )

            await callback.message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )