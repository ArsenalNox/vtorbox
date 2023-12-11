import time

import aiohttp
import requests
from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler
from bot.keyboards.keyboards import Keyboard
from bot.settings import settings
from bot.utils.buttons import BUTTONS
from bot.utils.messages import MESSAGES


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()
        self.kb = Keyboard()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            await message.answer(
                MESSAGES['START'],
                reply_markup=self.kb.start_menu_btn()
            )

            # async with aiohttp.ClientSession() as session:
            #     async with session.get(settings.base_url + 'users') as resp:
            #         print(resp.status)
            #         print(await resp.text())

        @self.router.message(F.text.startswith(BUTTONS['MENU']))
        async def get_menu(message: Message, state: FSMContext):
            """Переход в главное меню"""

            await message.answer(
                MESSAGES['MENU'],
                reply_markup=self.kb.start_menu_btn()
            )


