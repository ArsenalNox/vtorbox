import traceback

import requests
from loguru import logger

from bot.settings import settings

HEADERS = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiODA0ODFlNTctYjk1Zi00MmM3LWExYWYtNjM3NDAxYjkxNTJiIiwic2NvcGVzIjpbImN1c3RvbWVyIiwiYWRtaW4iLCJib3QiLCJtYW5hZ2VyIiwiY291cmllciJdfQ._PUj3bg34h-TJQ6oa5sKI7XRrtON0gKqgPd5y_rrbuE'
}



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
