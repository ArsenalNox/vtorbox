from aiogram import Bot, Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.courier_kb import CourierKeyboard
from bot.states.states import Courier
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class CourierHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = CourierKeyboard()
        self.orders_list = None
        self.index = 0

    def handle(self):
        @self.router.message(or_f(F.text.startswith(BUTTONS['ROUTE']), F.data.startswith(BUTTONS['BACK_ROUTE'])))
        async def get_route(message: Message, state: FSMContext):
            """Получение маршрута для курьера"""

            # получаем маршрут для данного пользователя по tg_id
            await state.update_data(chat_id=message.chat.id)
            status_code, routes = await req_to_api(
                method='get',
                url=f'',
            )
            route_link = 'https://yandex.ru/maps/'

            if routes:
                msg = await message.answer(
                    MESSAGES['CURRENT_ROUTE'],
                    reply_markup=self.kb.routes_menu(route_link)
                )
                await state.update_data(courier_msg=msg.message_id)

            else:
                await message.answer(
                    MESSAGES['NO_ROUTES'],
                    reply_markup=self.kb.courier_btn()
                )

        @self.router.callback_query(F.data.startswith('points_route'))
        async def get_points_route(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()

            # получаем маршрут для данного пользователя по tg_id

            status_code, routes = await req_to_api(
                method='get',
                url=f'',
            )

            # меняем клавиатуру на кнопки с точками на карте
            if data.get('courier_msg'):
                await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('courier_msg'),
                    reply_markup=self.kb.points_btn(routes)
                )

            await callback.message.answer(
                MESSAGES['BACK_TO_ROUTES'],
                reply_markup=self.kb.back_btn()
            )

        @self.router.callback_query(F.data.startswith('point'))
        async def get_point_info(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            point_id = callback.data.split('_')[-1]
            await state.update_data(point_id=point_id)

            # находим по id всю информацию по конкретной точке маршрута

            # получаем информацию по точке
            await callback.message.answer(
                MESSAGES['ROUTE_INFO'].format(point_id),
                reply_markup=self.kb.points_menu_btn()
            )

        @self.router.callback_query(F.data.startswith('finished'))
        async def mark_point_like_finished(callback: CallbackQuery, state: FSMContext):
            """Отмечаем точку маршрута как обработанную"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            point_id = data.get('point_id')

            # запрос на отметку данной точки, как обработанной
            status_code, routes = await req_to_api(
                method='get',
                url=f'',
            )

            await callback.message.answer(
                MESSAGES['BACK_TO_ROUTES'],
                reply_markup=self.kb.back_btn()
            )

        @self.router.callback_query(F.data.startswith('not_finished'))
        async def get_comment_to_not_finished_point(callback: CallbackQuery, state: FSMContext):
            """Запрашиваем комментарий к необработанной точке маршрута"""

            await state.update_data(chat_id=callback.message.chat.id)
            await callback.message.answer(
                MESSAGES['COMMENT_TO_POINT']
            )

            await state.set_state(Courier.point)

        @self.router.message(Courier.point)
        async def get_comment_to_not_finished_point(message: Message, state: FSMContext):
            """Получаем текст комментария к необработанной заявки"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            point_id = data.get('point_id')
            comment = message.text

            # запрос на отметку данной точки, как НЕ обработанной
            status_code, routes = await req_to_api(
                method='get',
                url=f'',
            )

            await message.answer(
                MESSAGES['BACK_TO_ROUTES'],
                reply_markup=self.kb.back_btn()
            )





