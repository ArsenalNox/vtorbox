import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy import URL, create_engine

from app.models import Base
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
        self.handler.handle()
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    async def main(self):
        """Основная точка входа в бота и его запуск"""
        connection_url = URL.create(
            drivername="postgresql",
            username=os.getenv("POSTGRES_USER"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            database=os.getenv("POSTGRES_DB"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        engine = create_engine(connection_url)
        Base.metadata.create_all(engine)
        await self.start()
        await self.dp.start_polling(self.bot, polling_timeout=100000)


if __name__ == '__main__':
    bot = MainBot()
    print('START BOT')
    asyncio.run(bot.main())
