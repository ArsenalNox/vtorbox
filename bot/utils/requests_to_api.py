import traceback

import requests
from loguru import logger

from bot.settings import settings
from bot.utils.handle_data import HEADERS


async def req_to_api(method: str, url: str, data: str = None) -> tuple[int, dict] | tuple[bool, bool]:
    """Запрос к бэку"""

    if method == 'get':
        response = requests.get(settings.base_url + url, headers=HEADERS)

    elif method == 'post':
        response = requests.post(settings.base_url + url, data=data, headers=HEADERS)

    elif method == 'put':
        response = requests.put(settings.base_url + url, data=data, headers=HEADERS)

    # delete
    else:
        response = requests.delete(settings.base_url + url, headers=HEADERS)
    try:
        result = response.json()

        return response.status_code, result

    except Exception as e:
        logger.warning(e)
        logger.warning(traceback.format_exc())

        return False, False
