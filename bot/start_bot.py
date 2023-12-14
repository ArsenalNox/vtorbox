import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import URL, create_engine

from app.models import Base, engine
from bot.handlers.main_handler import MainHandler
from bot.settings import settings


class MainBot:

    def __init__(self):
        self.bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.handler = MainHandler(self.bot)

    async def start(self):
        """Подключение всех роутеров/старт отлова сообщений/логгирование"""

        self.dp.include_router(self.handler.command_handler.router)
        self.dp.include_router(self.handler.text_handler.router)
        self.dp.include_router(self.handler.address_handler.router)
        self.dp.include_router(self.handler.questionnaire_handler.router)
        self.dp.include_router(self.handler.application_handler.router)
        self.dp.include_router(self.handler.payment_handler.router)
        self.dp.include_router(self.handler.notification_handler.router)
        self.handler.handle()
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    async def main(self):
        """Основная точка входа в бота и его запуск"""

        Base.metadata.create_all(engine)
        await self.start()
        await self.dp.start_polling(self.bot, polling_timeout=100000)


if __name__ == '__main__':
    bot = MainBot()
    print('START BOT')
    asyncio.run(bot.main())
