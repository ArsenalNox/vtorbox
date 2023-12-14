import pprint

import aiohttp

from bot.settings import settings
from bot.utils.handle_data import get_address_name


async def get_request_to_yandex_geocoder(address: str) -> dict:
    """Отправляем запрос на получение координат адреса указанного пользователем"""

    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'https://geocode-maps.yandex.ru/1.x/?apikey={settings.geocoder_yandex_api}&geocode={address}&format=json') as resp:
            data = await resp.json()
            data = dict(data)

    return data


async def get_address_by_coordinates(longitude: str, latitude: str) -> str:
    """Получение название адреса по его координатам"""

    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'https://geocode-maps.yandex.ru/1.x/?apikey={settings.geocoder_yandex_api}&geocode={longitude},{latitude}&format=json') as resp:
            data = await resp.json()
            data = dict(data)

    address = get_address_name(data)

    return address
