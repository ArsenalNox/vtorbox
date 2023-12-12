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
