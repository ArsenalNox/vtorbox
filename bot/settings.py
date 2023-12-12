import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Настройки всего приложения bot"""

    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN')
        self.base_url = os.getenv('BASE_URL')
        self.geocoder_yandex_api = os.getenv('GEOCODER_YANDEX_API')


settings = Settings()
