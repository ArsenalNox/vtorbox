from bot.handlers.command_handler import CommandHandler


class MainHandler:

    def __init__(self, bot):
        """Создание всех хендлеров"""

        self.bot = bot
        self.command_handler = CommandHandler(self.bot)

    def handle(self):
        """Регистрация хендлеров на отлавливание сообщений"""

        self.command_handler.handle()
