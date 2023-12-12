import pprint

import aiohttp
from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.handlers.base_handler import Handler
from bot.keyboards.keyboards import Keyboard

from bot.services.addresses import AddressService
from bot.services.users import UserService
from bot.settings import settings
from bot.states.states import AddAddressState
from bot.third_party_api.yandex import get_request_to_yandex_geocoder
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import format_addresses, delete_messages_with_btn
from bot.utils.handle_data import get_found_result_geocoder_data, get_coordinates
from bot.utils.messages import MESSAGES


class TextHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = Keyboard()

    def handle(self):
        @self.router.message(F.text.startswith(BUTTONS['CREATE_APPLICATION']))
        async def create_application(message: Message, state: FSMContext):
            """Создание заявки"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['CREATE_APPLICATION'],
                reply_markup=self.kb.start_menu_btn()
            )

            # async with aiohttp.ClientSession() as session:
            #     async with session.get(settings.base_url + 'users') as resp:
            #         print(resp.status)
            #         print(await resp.text())

        @self.router.message(F.text.startswith(BUTTONS['APPLICATIONS_HISTORY']))
        async def applications_history(message: Message, state: FSMContext):
            """Создание заявки"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['APPLICATIONS_HISTORY'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['SETTINGS']))
        async def get_settings(message: Message, state: FSMContext):
            """Получение настроек бота"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['SETTINGS'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['MY_ADDRESSES']))
        async def get_my_addresses(message: Message, state: FSMContext):
            """Получение всех адресов пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            # получаем все адреса текущего пользователя
            addresses = UserService.get_users_addresses(message.chat.id)
            text = format_addresses(addresses)
            await message.answer(
                text,
                reply_markup=self.kb.add_address_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['ADD_ADDRESS']))
        async def get_add_address(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['ADD_ADDRESS'],
                reply_markup=self.kb.send_geo()
            )
            await state.set_state(AddAddressState.address)

        @self.router.message(F.content_type.in_(['location']), AddAddressState.address)
        async def get_new_address_from_geo(message: Message, state: FSMContext):
            """Получение и валидация нового адреса отправлено по геолокации"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            longitude = message.location.longitude
            latitude = message.location.latitude
            print(longitude, latitude)

            # обнуляем состояние
            await state.set_state(state=None)

        @self.router.message(AddAddressState.address)
        async def get_new_address_from_text(message: Message, state: FSMContext):
            """Получение и валидация нового адреса по тексту пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            address = message.text

            data = await get_request_to_yandex_geocoder(address)
            found_result = get_found_result_geocoder_data(data)

            # если есть найденные адреса
            if found_result == 0:
                await message.answer(
                    MESSAGES['EMPTY_ADDRESS_RESULT'],
                    reply_markup=self.kb.add_address_btn()
                )
            else:
                latitude, longitude = get_coordinates(data)

                # создание адреса
                AddressService.create_user_address(
                    address_text=address,
                    latitude=latitude,
                    longitude=longitude,
                    tg_id=message.from_user.id
                )
                await message.answer(
                    MESSAGES['ADDRESS_WAS_ADDED'].format(
                        address
                    )
                )

            # обнуляем состояние
            await state.set_state(state=None)

        @self.router.message(F.text.startswith(BUTTONS['PAYMENTS']))
        async def get_payments(message: Message, state: FSMContext):
            """Получение способов оплаты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['PAYMENTS'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['QUESTIONNAIRE']))
        async def get_questionnaire(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['QUESTIONNAIRE'],
                reply_markup=self.kb.settings_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['NOTIFICATIONS']))
        async def get_notifications(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['NOTIFICATIONS'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['ABOUT']))
        async def get_about_info(message: Message, state: FSMContext):
            """Получение анкеты пользователя"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['ABOUT'],
                reply_markup=self.kb.start_menu_btn()
            )

        @self.router.message(F.text.startswith(BUTTONS['DEFAULT']))
        async def set_default_address(message: Message, state: FSMContext):
            """Установка адреса по умолчанию"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            msg = await message.answer(
                MESSAGES['CHOOSE_DEFAULT_ADDRESS'],
                reply_markup=self.kb.addresses_list_btn(message.from_user.id)
            )
            await state.update_data(msg=msg.message_id)
            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.callback_query(F.data.startswith('address'))
        async def get_address(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки с адресом при установке адреса по умолчанию"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            address_id = callback.data.split('_')[1]

            old_main_address = AddressService.get_main_address(callback.message.chat.id)
            address = AddressService.get_address_by_id(address_id)
            AddressService.mark_address_to_main(address, old_main_address)

            await callback.message.answer(
                MESSAGES['DEFAULT_ADDRESS_IS_SELECTED'].format(
                    address.address
                )
            )

            await get_my_addresses(
                message=callback.message,
                state=state
            )

        @self.router.message(F.text.startswith(BUTTONS['DELETE_ADDRESS']))
        async def delete_address(message: Message, state: FSMContext):
            """Удаление адреса из списка адресов"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            msg = await message.answer(
                MESSAGES['CHOOSE_DELETE_ADDRESS'],
                reply_markup=self.kb.addresses_list_btn(
                    tg_id=message.from_user.id,
                    tag='delete'
                )
            )
            await state.update_data(msg=msg.message_id)
            await message.answer(
                MESSAGES['GO_TO_MENU'],
                reply_markup=self.kb.menu_btn()
            )

        @self.router.callback_query(F.data.startswith('delete'))
        async def delete_address_2(callback: CallbackQuery, state: FSMContext):
            """Отлов кнопки с адресом для удаления"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=callback.message
            )

            address_id = callback.data.split('_')[1]
            AddressService.delete_address_by_id(address_id)

            await get_my_addresses(
                message=callback.message,
                state=state
            )



