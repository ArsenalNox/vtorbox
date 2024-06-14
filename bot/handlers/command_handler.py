import http
import json

from aiogram import Bot, Router, F
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard

from bot.states.states import RegistrationUser
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.requests_to_api import req_to_api


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.message(or_f(Command('start'), F.text == BUTTONS['START']))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            await state.update_data(chat_id=message.chat.id)

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )
            await state.update_data(chat_id=message.chat.id)

            promocode_in_msg = message.text.split()[-1]

            if not promocode_in_msg:
                promocode_in_msg = ''

            # ищем пользователя из БД по промокоду и затем добавляем ему данные телеграмма в БД
            status_code, user = await req_to_api(
                method='get',
                url=f'bot/users/promocode?promocode={promocode_in_msg}',
            )

            if user and status_code == http.HTTPStatus.OK:
                user_data = json.dumps({
                    'tg_id': message.from_user.id,
                    'username': message.from_user.username,
                    'firstname': message.from_user.first_name,
                    'secondname': message.from_user.last_name,
                    'promocode': promocode_in_msg
                })

                # обновляем данные пользователя данными из телеграма
                await req_to_api(
                    method='put',
                    url='bot/users/botclient/link',
                    data=user_data,
                )

                status_code, start_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=START'
                )
                status_code, about_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=ABOUT'
                )

                status_code, menu_msg = await req_to_api(
                    method='get',
                    url='bot/messages?message_key=MENU'
                )

                await message.answer(
                    start_msg
                )
                await message.answer(
                    about_msg
                )
                await message.answer(
                    menu_msg,
                    reply_markup=self.kb.start_menu_btn()
                )

            else:
                status_code, user = await req_to_api(
                    method='get',
                    url=f'user/me?tg_id={message.chat.id}'
                )

                print(f'{user=}')

                if user and user != {'message': 'Not found'} and 'courier' not in user.get('roles'):
                    status_code, menu_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=MENU'
                    )

                    await message.answer(
                        menu_msg,
                        reply_markup=self.kb.start_menu_btn()
                    )

                elif user and user != {'message': 'Not found'} and 'courier' in user.get('roles'):
                    status_code, courier_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=COURIER'
                    )
                    await message.answer(
                        courier_msg,
                        reply_markup=self.kb.courier_btn()
                    )

                else:
                    user_data = json.dumps({
                        'tg_id': message.from_user.id,
                        'username': message.from_user.username,
                        'firstname': message.from_user.first_name,
                        'secondname': message.from_user.last_name
                    })

                    # создаем пользователя
                    await req_to_api(
                        method='post',
                        url='bot/user',
                        data=user_data,
                    )

                    status_code, register_msg = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=REGISTRATION_MENU'
                    )
                    await message.answer(
                        register_msg,
                        reply_markup=self.kb.registration_btn()
                    )
                    await state.set_state(RegistrationUser.phone)
                    await state.update_data(menu_view='registration')


