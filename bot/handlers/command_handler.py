from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.base_handler import Handler


class CommandHandler(Handler):
    def __init__(self, bot: Bot):
        super().__init__(bot)
        self.router = Router()

    def handle(self):
        @self.router.message(Command('start'))
        async def start(message: Message, state: FSMContext):
            """Отлов команды /start"""

            await message.answer('Hi')
