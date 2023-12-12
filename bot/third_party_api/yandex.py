import aiohttp

from bot.settings import settings


async def get_request_to_yandex_geocoder(address: str) -> dict:
    """Отправляем запрос на получение координат адреса указанного пользователем"""

    async with aiohttp.ClientSession() as session:
        async with session.get(
                f'https://geocode-maps.yandex.ru/1.x/?apikey={settings.geocoder_yandex_api}&geocode={address}&format=json') as resp:
            data = await resp.json()
            data = dict(data)

    return data