import uuid, os, requests
from app import CODER_KEY, CODER_SETTINGS


def is_valid_uuid(value):
    """
    Проверить, является ли строка валидным UUID
    """
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


def get_lang_long_from_text_addres(address):
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={CODER_KEY}&geocode={address}{CODER_SETTINGS}"
    
    data = requests.request("GET", url).json()
    data = dict(data)
    longtitude = 0
    latitude = 0

    try:
        longitude, latitude = str(data.get('response', {}). \
            get('GeoObjectCollection', {}). \
            get('featureMember')[0]. \
            get('GeoObject', {}).\
            get('Point').get('pos')).split()
        return longitude, latitude

    except Exception as err: 
        return None, None