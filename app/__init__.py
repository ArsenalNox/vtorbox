from enum import Enum

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


class Scopes(Enum):
    bot = 'bot'
    admin = 'admin'
    customer = 'customer'
    manager = 'manager'
    courier = 'courier'