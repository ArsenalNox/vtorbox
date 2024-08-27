import asyncio
import pprint
import traceback

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import ErrorEvent
from loguru import logger

from bot.handlers.main_handler import MainHandler
from bot.keyboards.base_keyboards import BaseKeyboard
from bot.keyboards.courier_kb import CourierKeyboard
from bot.settings import settings
from bot.states.states import RegistrationUser
from bot.utils.handle_data import show_active_orders
from bot.utils.logger import warning_log_write, debug_log_write
from bot.utils.messages import MESSAGES
from bot.utils.requests_to_api import req_to_api


class MainBot:

    def __init__(self):
        self.bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
        # self.storage = RedisStorage.from_url('redis://redis:6379/0')
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        self.handler = MainHandler(self.bot)
        self.kb = BaseKeyboard()
        self.courier_kb = CourierKeyboard()

    async def start_logging(self):
        """Начала логгирования"""

        debug_log_write()
        warning_log_write()

    async def catch_errors(self):
        """Отлов всех ошибок в хендлерах и логгирование"""

        @self.dp.errors()
        async def catch_error(event: ErrorEvent, state: FSMContext):
            try:
                error_data: dict = event.model_dump()
                error = error_data.get('exception')
                if error_data.get('update', {}).get('message'):
                    chat_id = error_data.get('update', {}).get('message', {}).get('from_user', {}).get('id')
                else:
                    chat_id = error_data.get('update', {}).get('callback_query', {}).get('from_user', {}).get(
                        'id')
                error_text = f'User: {chat_id}, err: {error}'

                logger.warning(error_text)
                logger.warning(traceback.format_exc())

                status_code, user = await req_to_api(
                    method='get',
                    url=f'user/me?tg_id={chat_id}',
                )
                message = event.update.message
                if not message:
                    message = event.update.callback_query.message

                if user.get('id') and 'courier' not in user.get('roles'):
                    status_code, text = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=MENU'
                    )

                    status_code, orders = await req_to_api(
                        method='get',
                        url=f'users/orders/?tg_id={chat_id}&show_only_active=true',
                    )

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=MESSAGES['ERROR']
                    )
                    if orders and status_code == 200:
                        await show_active_orders(
                            orders=orders,
                            self=self,
                            message=message,
                            state=state
                        )
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=self.kb.start_menu_btn()
                    )

                elif user.get('id') and 'courier' in user.get('roles'):
                    status_code, routes = await req_to_api(
                        method='get',
                        url=f'bot/routes/?courier_id={chat_id}',
                    )
                    route_link = 'https://yandex.ru/maps/'
                    if routes:
                        routes = routes[0]

                        route_link = routes.get('route_link')
                        if route_link is None:
                            route_link = 'https://yandex.ru/maps/'

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=MESSAGES['ERROR']
                    )

                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=MESSAGES['CURRENT_ROUTE'],
                        reply_markup=self.courier_kb.routes_menu(route_link))

                else:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=MESSAGES['ERROR']
                    )
                    status_code, text = await req_to_api(
                        method='get',
                        url='bot/messages?message_key=MENU'
                    )
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=self.kb.start_menu_btn()
                    )

            except Exception as e:
                logger.warning(e)
                logger.warning(traceback.format_exc())

                await self.bot.send_message(
                    chat_id=chat_id,
                    text=MESSAGES['MENU'],
                    reply_markup=self.kb.start_menu_btn()
                )

    async def start(self):
        """Подключение всех роутеров/старт отлова сообщений/логгирование"""

        self.dp.include_router(self.handler.command_handler.router)
        self.dp.include_router(self.handler.address_handler.router)
        self.dp.include_router(self.handler.questionnaire_handler.router)
        self.dp.include_router(self.handler.order_handler.router)
        self.dp.include_router(self.handler.payment_handler.router)
        self.dp.include_router(self.handler.schedule_handler.router)
        self.dp.include_router(self.handler.notification_handler.router)
        self.dp.include_router(self.handler.courier_handler.router)
        self.dp.include_router(self.handler.text_handler.router)
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
