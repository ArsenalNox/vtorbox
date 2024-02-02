import uuid, os, requests
from dotenv import load_dotenv

load_dotenv()

CODER_KEY = os.getenv("Y_GEOCODER_KEY")
#TODO: Переместить настройки в другой файл
CODER_SETTINGS = f"&format=json&lang=ru_RU&ll=37.618920,55.756994&spn=4.552069,4.400552&rspn=1"

def is_valid_uuid(value):
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