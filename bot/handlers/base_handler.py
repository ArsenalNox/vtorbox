import abc

from aiogram import Bot


class Handler(metaclass=abc.ABCMeta):
    """Абстрактный класс хендлера"""

    def __init__(self, bot: Bot):
        self.bot = bot

    @abc.abstractmethod
    async def handle(self):
        pass
