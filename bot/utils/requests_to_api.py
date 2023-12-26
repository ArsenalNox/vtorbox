from json import JSONDecodeError

import requests

from bot.settings import settings
from bot.utils.handle_data import HEADERS


def req_to_api(method: str, url: str, data: str = None) -> tuple[int, dict] | tuple[bool, bool]:
    """Зарпос к бэку"""
    if method == 'get':
        response = requests.get(settings.base_url + url, headers=HEADERS)

    elif method == 'post':
        response = requests.post(settings.base_url + url, data=data, headers=HEADERS)

    elif method == 'put':
        response = requests.put(settings.base_url + url, data=data, headers=HEADERS)

    elif method == 'delete':
        response = requests.delete(settings.base_url + url, headers=HEADERS)
    try:
        result = response.json()

        return response.status_code, result

    except JSONDecodeError:
        return False, False
