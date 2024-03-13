import json

import requests
from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.address_kb import AddressKeyboard
from bot.keyboards.order import OrderKeyboard

from bot.settings import settings
from bot.states.states import AddAddressState, CreateOrder
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn, format_addresses
from bot.utils.handle_data import HEADERS, show_address_list, show_address_date
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class AddressHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = AddressKeyboard()
        self.order_kb = OrderKeyboard()
        self.flag_to_return = False

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['MY_ADDRESSES']))
        async def get_my_addresses(message: Message, state: FSMContext):
            """Получение всех адресов пользователя"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            self.flag_to_return = False
            # запрос на получение всех адресов у юзера

            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={message.from_user.id}',
            )

            await show_address_list(
                message=message,
                state=state,
                address_list=address_list,
                self=self
            )

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.callback_query(F.data.startswith('add_address'))
        async def get_new_address(callback: CallbackQuery, state: FSMContext):
            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            # флаг для возврата к созданию заказа(после того как во время заказа пользователь нажмет 'Добавить адрес')
            self.flag_to_return = callback.data.split('_')[-1]

            await callback.message.answer(
                MESSAGES['ADD_NEW_ADDRESS'],
                reply_markup=self.kb.send_geo_btn()
            )

            await state.set_state(AddAddressState.address)

        @self.router.message(F.content_type.in_(['location']), AddAddressState.address)
        async def get_new_address_from_geo(message: Message, state: FSMContext):
            """Получение и валидация нового адреса отправлено по геолокации"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            longitude = str(message.location.longitude)
            latitude = str(message.location.latitude)
            await state.update_data(longitude=longitude)
            await state.update_data(latitude=latitude)

            await message.answer(
                MESSAGES['WRITE_YOUR_DETAIL_ADDRESS']
            )
            await state.set_state(AddAddressState.detail)

        @self.router.message(F.text, AddAddressState.detail)
        async def get_detail_address(message: Message, state: FSMContext):
            """Получение доп информации об адресе (подъезд, квартира)"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            detail = message.text
            await state.update_data(detail=detail)

            await message.answer(
                MESSAGES['WRITE_COMMENT_ADDRESS'],
                reply_markup=self.kb.empty_comment_btn()
            )

            await state.set_state(state=AddAddressState.comment)

        @self.router.message(F.text, AddAddressState.comment)
        async def get_comment_address(message: Message, state: FSMContext):
            """Получение комментария к адресу и создание адреса в БД"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await state.set_state(state=None)

            # получаем данные из состояния и отправляем запрос в бек на создание адреса
            address_data = json.dumps(
                {
                    "address": data.get('address'),
                    "detail": data.get('detail'),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                }
            )
            print(address_data)

            status_code, response = await req_to_api(
                method='post',
                url=f'bot/user/addresses?tg_id={message.from_user.id}',
                data=address_data,
            )
            await state.update_data(address=response)

            # если не удалось найти такой адрес, то выводим сообщение
            if response.get('message'):
                await message.answer(
                    MESSAGES['WRONG_ADDRESS'],
                    reply_markup=self.kb.settings_btn()
                )

            elif eval(self.flag_to_return):
                address = response
                await show_address_date(
                    address=address,
                    message=message,
                    kb=self.order_kb.choose_date_btn,
                    state=state
                )

                self.flag_to_return = False
            else:
                # переход к списку адресов
                await get_my_addresses(
                    message=message,
                    state=state
                )

        @self.router.message(F.text, AddAddressState.address)
        async def get_new_address_from_text(message: Message, state: FSMContext):
            """Получение и валидация нового адреса по тексту пользователя"""

            await state.update_data(chat_id=message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await state.update_data(address=message.text)
            await state.set_state(AddAddressState.comment)

            await message.answer(
                MESSAGES['WRITE_COMMENT_ADDRESS'],
                reply_markup=self.kb.empty_comment_btn()
            )

        @self.router.callback_query(F.data.startswith('delete_address'))
        async def delete_address(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            address_id = callback.data.split('_')[-1]

            # запрос в бек на удаление адреса по его id
            await req_to_api(
                method='delete',
                url=f'bot/user/addresses/{address_id}?tg_id={callback.message.chat.id}',
            )

            # удаляем сообщения с адресом
            if data.get('msg_ids'):
                for address_id_temp, msg_id in data.get('msg_ids').items():
                    await callback.bot.delete_message(
                        chat_id=data.get('chat_id'),
                        message_id=msg_id
                    )

                await state.update_data(msg_ids={})

            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={callback.message.chat.id}',
            )

            msg = await callback.message.answer(
                MESSAGES['ADD_ADDRESS'],
                reply_markup=self.kb.add_address_btn(self.flag_to_return)
            )
            await state.update_data(msg=msg.message_id)

            msg_ids = {}
            # отправляем все адреса пользователя с кнопками ('Удалить' и 'По умолчанию')
            # если адрес установлен по умолчанию, то добавляем текст и 1 кнопка только
            for address in address_list:
                if address.get('main'):
                    msg = await callback.message.answer(
                        address['address'] + '(по умолчанию)',
                        reply_markup=self.kb.address_delete_default_btn(address)
                    )
                    msg_ids[address['id']] = msg.message_id
                else:
                    msg = await callback.message.answer(
                        address['address'],
                        reply_markup=self.kb.address_delete_default_btn(address)
                    )
                    msg_ids[address['id']] = msg.message_id

            await state.update_data(msg_ids=msg_ids)

        @self.router.callback_query(F.data.startswith('default_address'))
        async def default_address(callback: CallbackQuery, state: FSMContext):

            await state.update_data(chat_id=callback.message.chat.id)
            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )
            address_id = callback.data.split('_')[-1]

            # удаляем сообщения с адресом
            if data.get('msg_ids'):
                for address_id_temp, msg_id in data.get('msg_ids').items():
                    await callback.bot.delete_message(
                        chat_id=data.get('chat_id'),
                        message_id=msg_id
                    )

                await state.update_data(msg_ids={})

            status_code, address = await req_to_api(
                method='get',
                url=f'bot/user/addresses/{address_id}?tg_id={callback.message.chat.id}',
            )

            # запрос в бек на установку по умолчанию по его id
            address_data = json.dumps(
                {
                    "address": address['address'],
                    "main": True,
                }
            )
            await req_to_api(
                method='put',
                url=f'bot/user/addresses/{address_id}?tg_id={callback.message.chat.id}',
                data=address_data,
            )

            # выводим список адресов после изменения адреса по умолчанию
            status_code, address_list = await req_to_api(
                method='get',
                url=f'bot/user/addresses/all?tg_id={callback.message.chat.id}',
            )

            await show_address_list(
                message=callback.message,
                state=state,
                address_list=address_list,
                self=self
            )
