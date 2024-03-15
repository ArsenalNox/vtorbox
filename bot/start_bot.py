import asyncio
import pprint
import traceback

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent
from loguru import logger

from bot.handlers.main_handler import MainHandler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.settings import settings
from bot.utils.logger import warning_log_write, debug_log_write
from bot.utils.messages import MESSAGES


class MainBot:

    def __init__(self):
        self.bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
        self.dp = Dispatcher(storage=MemoryStorage())
        self.handler = MainHandler(self.bot)
        self.kb = BaseKeyboard()

    async def start_logging(self):
        """Начала логгирования"""

        debug_log_write()
        warning_log_write()

    async def catch_errors(self):
        """Отлов всех ошибок в хендлерах и логгирование"""

        @self.dp.errors()
        async def catch_error(event: ErrorEvent):
            try:
                error_data: dict = event.model_dump()
                chat_id = error_data.get('update', {}).get('message', {}).get('from_user', {}).get('id')
                error = error_data.get('exception')
                error_text = f'User: {chat_id}, err: {error}'

                logger.warning(error_text)
                logger.warning(traceback.format_exc())

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=MESSAGES['ERROR_IN_HANDLER'],
                    reply_markup=self.kb.start_btn()
                )
            except Exception as e:
                logger.warning(e)
                logger.warning(traceback.format_exc())


    async def start(self):
        """Подключение всех роутеров/старт отлова сообщений/логгирование"""

        self.dp.include_router(self.handler.command_handler.router)
        self.dp.include_router(self.handler.text_handler.router)
        self.dp.include_router(self.handler.address_handler.router)
        self.dp.include_router(self.handler.questionnaire_handler.router)
        self.dp.include_router(self.handler.order_handler.router)
        self.dp.include_router(self.handler.payment_handler.router)
        self.dp.include_router(self.handler.schedule_handler.router)
        self.dp.include_router(self.handler.notification_handler.router)
        self.dp.include_router(self.handler.courier_handler.router)
        self.handler.handle()
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    async def main(self):
        """Основная точка входа в бота и его запуск"""

        await self.start_logging()
        await self.catch_errors()
        await self.start()
        await self.dp.start_polling(self.bot, polling_timeout=100000)


if __name__ == '__main__':
    bot = MainBot()
    print('START BOT')
    asyncio.run(bot.main())
