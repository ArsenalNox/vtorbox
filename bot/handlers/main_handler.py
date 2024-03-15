import aiohttp

from bot.handlers.command_handler import CommandHandler
from bot.handlers.text_handler import TextHandler
from bot.handlers.address_handler import AddressHandler
from bot.handlers.questionnaire_handler import QuestionnaireHandler
from bot.handlers.order import OrderHandler
from bot.handlers.payment_handler import PaymentHandler
from bot.handlers.schedule import ScheduleHandler
from bot.handlers.notification_handler import NotificationHandler
from bot.handlers.courier import CourierHandler


class MainHandler:

    def __init__(self, bot):
        """Создание всех хендлеров"""

        self.bot = bot
        self.command_handler = CommandHandler(self.bot)
        self.text_handler = TextHandler(self.bot)
        self.address_handler = AddressHandler(self.bot)
        self.questionnaire_handler = QuestionnaireHandler(self.bot)
        self.order_handler = OrderHandler(self.bot)
        self.payment_handler = PaymentHandler(self.bot)
        self.schedule_handler = ScheduleHandler(self.bot)
        self.notification_handler = NotificationHandler(self.bot)
        self.courier_handler = CourierHandler(self.bot)

    def handle(self):
        """Регистрация хендлеров на отлавливание сообщений"""

        self.command_handler.handle()
        self.text_handler.handle()
        self.address_handler.handle()
        self.questionnaire_handler.handle()
        self.order_handler.handle()
        self.payment_handler.handle()
        self.schedule_handler.handle()
        self.notification_handler.handle()
        self.courier_handler.handle()
