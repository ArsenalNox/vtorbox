fullname_pattern = r"^[а-яА-ЯёЁ\s]+$"
phone_pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
email_pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


def get_found_result_geocoder_data(data: dict) -> int:
    """Получаем количество нахождений по адресу, введенному пользователем"""

    return int(
        data.get('response', {}).
        get('GeoObjectCollection', {}).
        get('metaDataProperty', {}).
        get('GeocoderResponseMetaData', {}).
        get('found', {})
    )


def get_coordinates(data: dict) -> tuple[str, str]:
    """Получение координат из данных геокодера"""
    coordinates_data = data.get('response', {}). \
        get('GeoObjectCollection', {}). \
        get('featureMember')[0]. \
        get('GeoObject', {}).\
        get('Point').get('pos')
    longitude, latitude = coordinates_data.split()

    return latitude, longitude


def get_address_name(data: dict) -> str:
    """Получение название адреса из данных yandex геокодер"""

    address = data.get('response', {}). \
        get('GeoObjectCollection', {}). \
        get('featureMember')[0]. \
        get('GeoObject', {}). \
        get('metaDataProperty', {}). \
        get('GeocoderMetaData', {}). \
        get('text')

    return address
