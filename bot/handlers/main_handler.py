import aiohttp

from bot.handlers.command_handler import CommandHandler
from bot.handlers.text_handler import TextHandler
from bot.handlers.address_handler import AddressHandler
from bot.handlers.questionnaire_handler import QuestionnaireHandler
from bot.handlers.order import ApplicationHandler
from bot.handlers.payment_handler import PaymentHandler
from bot.handlers.schedule import NotificationHandler


class MainHandler:

    def __init__(self, bot):
        """Создание всех хендлеров"""

        self.bot = bot
        self.command_handler = CommandHandler(self.bot)
        self.text_handler = TextHandler(self.bot)
        self.address_handler = AddressHandler(self.bot)
        self.questionnaire_handler = QuestionnaireHandler(self.bot)
        self.application_handler = ApplicationHandler(self.bot)
        self.payment_handler = PaymentHandler(self.bot)
        self.notification_handler = NotificationHandler(self.bot)

    def handle(self):
        """Регистрация хендлеров на отлавливание сообщений"""

        self.command_handler.handle()
        self.text_handler.handle()
        self.address_handler.handle()
        self.questionnaire_handler.handle()
        self.application_handler.handle()
        self.payment_handler.handle()
        self.notification_handler.handle()
