import time

import aiohttp
import requests
from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.base_keyboards import BaseKeyboard

from bot.services.users import UserService
from bot.settings import settings
from bot.utils.buttons import BUTTONS
from bot.utils.format_text import delete_messages_with_btn
from bot.utils.messages import MESSAGES


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = BaseKeyboard()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            data = await state.get_data()
            await delete_messages_with_btn(
                state=state,
                data=data,
                src=message
            )

            await message.answer(
                MESSAGES['START'],
                reply_markup=self.kb.start_menu_btn()
            )

            # сохраняем в состояние chat_id
            await state.update_data(chat_id=message.from_user.id)

            # создаем пользователя
            UserService.create_user(
                tg_id=message.from_user.id,
                username=message.from_user.username,
                fullname=message.from_user.full_name
            )
