import os

from enum import Enum
from dotenv import load_dotenv
import logging

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES')

CODER_KEY = os.getenv("Y_GEOCODER_KEY")
COURIER_KEY = os.getenv("Y_COURIER_KEY")

CODER_SETTINGS = f"&format=json&lang=ru_RU&ll=37.618920,55.756994&spn=4.552069,4.400552&rspn=1"
BOT_TOKEN = os.getenv("BOT_TOKEN")
COURIER_API_ROOT_ENDPOINT = 'https://courier.yandex.ru/vrs/api/v1'

T_BOT_URL="https://t.me/VtorBoxRuBot"

TIKOFF_API_URL_TEST="https://securepay.tinkoff.ru/v2"
# TIKOFF_API_URL_TEST="https://rest-api-test.tinkoff.ru/v2"

SCHEDULER_HOST=os.getenv('SCHEDULER_HOST')
SCHEDULER_PORT=os.getenv('SCHEDULER_PORT')

# BASE_HOST_URL_NOTIFY='http://5.253.62.213:8000/api/payment/notify/auto'
BASE_HOST_URL_NOTIFY='http://94.41.188.133:8000/api/payment/notify/auto'

class Tags(Enum):
    users = "users"
    admins = "admins"
    managers = "managers"
    couriers = "couriers"
    addresses = "adresses"
    orders = "orders"
    bot = "bot"
    boxes = "boxes"
    roles = "roles"
    regions = "regions"
    routes = "routes"
    settings = "settings"
    payments = "payments"
    statistics = 'statistics'
    statuses = 'statuses'
    notifications = 'notifications'

class Scopes(Enum):
    bot = 'bot'
    admin = 'admin'
    customer = 'customer'
    manager = 'manager'
    courier = 'courier'

logger = logging.getLogger('uvicorn.error')