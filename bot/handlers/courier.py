import json
import pprint
from urllib.parse import quote

from aiogram import Bot, Router, F
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from bot.handlers.base_handler import Handler
from bot.keyboards.courier_kb import CourierKeyboard
from bot.states.states import Courier
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.handle_data import show_courier_order
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
        @self.router.message(or_f(F.text.startswith(BUTTONS['ROUTE']), F.text.startswith(BUTTONS['BACK_ROUTE'])))
        async def get_route(message: Message, state: FSMContext):
            """Получение маршрута для курьера"""

            await state.update_data(chat_id=message.chat.id)
            await state.update_data(menu_view='courier_menu')
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            logger.debug(
                f'Пользователь: {message.chat.id} зашел как курьер')

            # получаем маршрут для данного пользователя по tg_id
            status_code, routes = await req_to_api(
                method='get',
                url=f'bot/routes/?courier_id={message.chat.id}',
            )

            if routes:
                routes = routes[0]

                route_link = routes.get('route_link')
                if route_link is None:
                    route_link = 'https://yandex.ru/maps/'

                status_code, route_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=CURRENT_ROUTE'
                )

                msg = await message.answer(
                    route_msg,
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
            await state.update_data(menu_view='courier_menu')

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            status_code, routes = await req_to_api(
                method='get',
                url=f'bot/routes/?courier_id={callback.message.chat.id}',
            )

            if routes:
                routes = routes[0]

            # меняем клавиатуру на кнопки с точками на карте
            if data.get('courier_msg'):
                msg = await callback.bot.edit_message_reply_markup(
                    chat_id=data.get('chat_id'),
                    message_id=data.get('courier_msg'),
                    reply_markup=await self.kb.points_btn(routes)
                )
                await state.update_data(msg=msg.message_id)

            await callback.message.answer(
                MESSAGES['BACK_TO_ROUTES'],
                reply_markup=self.kb.back_btn()
            )

        @self.router.callback_query(F.data.startswith('point'))
        async def get_point_info(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            order_id = callback.data.split('_')[-1]
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )
            await state.update_data(order_id=order_id)

            await show_courier_order(
                order_id=order_id,
                order=order,
                state=state,
                message=callback.message,
                self=self
            )

        @self.router.callback_query(F.data.startswith('finished'))
        async def mark_point_like_finished(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            order_id = callback.data.split('_')[-1]

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            if data.get('courier_msg'):
                await callback.bot.edit_message_text(
                    text=MESSAGES['ARE_YOU_SURE'].format(order.get('order_num')),
                    chat_id=data.get('chat_id'),
                    message_id=data.get('courier_msg'),
                    reply_markup=self.kb.yes_or_no_btn(order_id)
                )

        @self.router.callback_query(F.data.startswith('courier_yes'))
        async def mark_point_like_finished(callback: CallbackQuery, state: FSMContext):
            """Отмечаем точку маршрута как обработанную"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            order_id = callback.data.split('_')[-1]

            status = quote("ожидается оплата")
            await req_to_api(
                method='put',
                url=f'orders/{order_id}/status?status_text={status}',
            )

            logger.debug(
                f'Пользователь: {callback.message.chat.id} отметил заявку: {order_id} как Ожидается Оплата')

            status_code, routes = await req_to_api(
                method='get',
                url=f'bot/routes/?courier_id={callback.message.chat.id}',
            )

            if routes:
                routes = routes[0]

                msg = await callback.message.answer(
                    MESSAGES['BACK_TO_ORDER_LIST'],
                    reply_markup=await self.kb.points_btn(routes)
                )
                await state.update_data(msg=msg.message_id)

            await callback.message.answer(
                MESSAGES['BACK_TO_ROUTES'],
                reply_markup=self.kb.back_btn()
            )

        @self.router.callback_query(F.data.startswith('courier_no'))
        async def no_sure_courier_save(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            order_id = callback.data.split('_')[-1]

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_courier_order(
                order_id=order_id,
                order=order,
                state=state,
                message=callback.message,
                self=self
            )

        @self.router.callback_query(F.data.startswith('not_finished'))
        async def get_comment_to_not_finished_point(callback: CallbackQuery, state: FSMContext):
            """Запрашиваем комментарий к необработанной точке маршрута"""

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            order_id = callback.data.split('_')[-1]
            await state.update_data(order_id=order_id)

            await callback.message.answer(
                MESSAGES['COMMENT_TO_POINT']
            )

            await state.set_state(Courier.point)

        @self.router.callback_query(F.data.startswith('container_type'))
        async def change_container_type(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            order_id = callback.data.split('_')[-1]

            status_code, box_types = await req_to_api(
                method='get',
                url='boxes'
            )

            msg = await callback.message.answer(
                MESSAGES['CHOOSE_BOX_TYPE'],
                reply_markup=self.kb.choose_box_type(box_types, order_id)
            )
            await state.update_data(msg=msg.message_id)
            await state.set_state(state=Courier.container_type)

        @self.router.callback_query(F.data.startswith('box_id'), Courier.container_type)
        async def set_container_type(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            status_code, box_types = await req_to_api(
                method='get',
                url='boxes'
            )
            box_id = callback.data.split('_')[-1]
            container_type = [c.get('box_name') for c in box_types if c.get('id') == box_id]
            container_type = container_type[0]

            await state.set_state(state=None)

            order_id = data.get('order_id')

            order_update_data = json.dumps(
                {
                    'box_name': container_type
                }
            )
            await req_to_api(
                method='put',
                url=f'orders/{order_id}',
                data=order_update_data
            )

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_courier_order(
                order_id=order_id,
                order=order,
                state=state,
                message=callback.message,
                self=self
            )

        @self.router.callback_query(F.data.startswith('container_count'))
        async def change_container_count(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            order_id = callback.data.split('_')[-1]

            msg = await callback.message.answer(
                MESSAGES['CHOOSE_BOX_COUNT'],
                reply_markup=self.kb.choose_box_count(order_id)
            )
            await state.update_data(msg=msg.message_id)
            await state.set_state(state=Courier.container_count)

        @self.router.callback_query(F.data.startswith('box_count'), Courier.container_count)
        async def set_container_count(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            container_count = callback.data.split('_')[-1]

            await state.set_state(state=None)

            order_id = data.get('order_id')

            order_update_data = json.dumps(
                {
                    'box_count': container_count
                }
            )
            await req_to_api(
                method='put',
                url=f'orders/{order_id}',
                data=order_update_data
            )

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_courier_order(
                order_id=order_id,
                order=order,
                state=state,
                message=callback.message,
                self=self
            )

        @self.router.message(Courier.point)
        async def get_comment_to_not_finished_point(message: Message, state: FSMContext):
            """Получаем текст комментария к необработанной заявки"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            order_id = data.get('order_id')
            comment = message.text

            # запрос на отметку данной точки, как НЕ обработанной
            status = quote("отменена")
            await req_to_api(
                method='put',
                url=f'orders/{order_id}/status?status_text={status}',
            )

            logger.debug(
                f'Пользователь: {message.chat.id} отметил заявку: {order_id} как ОТМЕНЕНА')

            update_order_data = json.dumps(
                {
                    'comment_courier': comment
                }
            )
            await req_to_api(
                method='put',
                url=f'orders/{order_id}',
                data=update_order_data,
            )

            status_code, routes = await req_to_api(
                method='get',
                url=f'bot/routes/?courier_id={message.chat.id}',
            )

            if routes:
                routes = routes[0]

            msg = await message.answer(
                MESSAGES['BACK_TO_ORDER_LIST'],
                reply_markup=await self.kb.points_btn(routes)
            )
            await state.update_data(msg=msg.message_id)

            await message.answer(
                MESSAGES['BACK_TO_ROUTES'],
                reply_markup=self.kb.back_btn()
            )

        @self.router.callback_query(F.data.startswith('back_order_list'))
        async def back_order_list(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            status_code, routes = await req_to_api(
                method='get',
                url=f'bot/routes/?courier_id={callback.message.chat.id}',
            )

            if routes:
                routes = routes[0]

            msg = await callback.message.answer(
                MESSAGES['BACK_TO_ORDER_LIST'],
                reply_markup=await self.kb.points_btn(routes)
            )
            await state.update_data(msg=msg.message_id)

        @self.router.callback_query(F.data.startswith('cancel_change'))
        async def cancel_change_order(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            order_id = callback.data.split('_')[-1]
            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_courier_order(
                order_id=order_id,
                order=order,
                state=state,
                message=callback.message,
                self=self
            )

        @self.router.callback_query(F.data.startswith('write_courier_comment'))
        async def write_courier_comment(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            order_id = callback.data.split('_')[-1]
            await state.update_data(order_id=order_id)

            await callback.bot.edit_message_reply_markup(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                reply_markup=None
            )

            await callback.message.answer(
                MESSAGES['WRITE_COURIER_COMMENT']
            )
            await state.set_state(Courier.comment)

        @self.router.message(Courier.comment)
        async def get_courier_comment(message: Message, state: FSMContext):
            data = await state.get_data()
            order_id = data.get('order_id')

            await state.set_state(state=None)

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            update_order_data = json.dumps(
                {
                    'comment_courier': message.text
                }
            )
            await req_to_api(
                method='put',
                url=f'orders/{order_id}',
                data=update_order_data,
            )

            await message.answer(
                MESSAGES['YOUR_COMMENT_WAS_SAVED']
            )

            status_code, order = await req_to_api(
                method='get',
                url=f'orders/{order_id}',
            )

            await show_courier_order(
                order_id=order_id,
                order=order,
                state=state,
                message=message,
                self=self
            )
