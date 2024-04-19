import uuid, os, requests
import time
import datetime
import hashlib

from app import (
    CODER_KEY, CODER_SETTINGS, BOT_TOKEN,
    COURIER_API_ROOT_ENDPOINT as API_ROOT_ENDPOINT,
    SCHEDULER_HOST, SCHEDULER_PORT
    )

token = BOT_TOKEN

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


def send_message_through_bot(receipient_id:int, message, btn=None):
    """
    Отправить сообщение пользователю через тг бота 
    """

    method = 'sendMessage'

    if btn:
        b = {
            "chat_id" : receipient_id,
            "text" : message,
            "parse_mode" : "html",
            "reply_markup" : btn
        }
    else:
        b = {
            "chat_id" : receipient_id,
            "text" : message,
            "parse_mode" : "html"
        }

    try:
        test_request = requests.post(
            url='https://api.telegram.org/bot{0}/{1}'.format(token, method), json=b
        ).json()
        print(test_request)

    except Exception as err:
        print(err)


def generate_y_courier_json(route_data):
    """
    Сгенерировать json для отправки в яндекс.маршрутизацию
    """
    locations = []

    print(route_data.orders)

    time_winow = "07:00-18:00"

    for order in route_data.orders:
        order_d = order.order
        print(f"LAT: {order_d.address.latitude}; LONG: {order_d.address.longitude}, ID: {order_d.order_num}")

        locations.append({
            "id": order_d.order_num,
            "point": {
                "lat": float(order_d.address.latitude),
                "lon": float(order_d.address.longitude)
            },
            "time_window": time_winow,
        })

    payload = {
        "depot": {
            "id": 0,
            "point": {
                "lat": 55.734157,
                "lon": 37.589346
            },
            "time_window": "07:00-18:00"
        },
        "vehicles": [{
                "id": 2
            }
        ],
        "locations": locations,
        "options": {
            "time_zone": 3,
            "quality": "normal"
        }
    }

    print(payload)
    return payload


def get_result_by_id(request_id):
    poll_stop_codes = {
        requests.codes.ok,
        requests.codes.gone,
        requests.codes.internal_server_error
    }

    poll_url = '{}/result/mvrp/{}'.format(API_ROOT_ENDPOINT, request_id)

    response = requests.get(poll_url)
    while response.status_code not in poll_stop_codes:
        time.sleep(1)
        response = requests.get(poll_url)

    # Вывод информации в пользовательском формате.
    if response.status_code != 200:
        print ('Error {}: {}'.format(response.text, response.status_code))
    else:
        print ('Route optimization completed')
        print ('')

        for route in response.json()['result']['routes']:
            print ('Vehicle {} route: {:.2f}km'.format(
                route['vehicle_id'], route['metrics']['total_transit_distance_m'] / 1000))

            # Вывод маршрута в текстовом формате.
            for waypoint in route['route']:
                print ('  {type} {id} at {eta}, {distance:.2f}km driving '.format(
                    type=waypoint['node']['type'],
                    id=waypoint['node']['value']['id'],
                    eta=str(datetime.timedelta(seconds=waypoint['arrival_time_s'])),
                    distance=waypoint['transit_distance_m'] / 1000))

            # Вывод маршрута в формате ссылки на Яндекс Карты.
            yamaps_url = 'https://yandex.ru/maps/?mode=routes&rtext='
            for waypoint in route['route']:
                point = waypoint['node']['value']['point']
                yamaps_url += '{}%2c{}~'.format(point['lat'], point['lon'])

            print ('')
            print ('See route on Yandex.Maps:')
            print (yamaps_url)

            return yamaps_url
    
    return None


def create_tinkoff_token(data_dict: dict, terminal_key)->str:
    """
    Создать токен для запроса на апи тинькофф
    """

    values = {}

    for payment_value in data_dict:
        if (type(data_dict[payment_value]) == dict):
            continue
        values[payment_value] = data_dict[payment_value]

    values['Password'] = terminal_key

    # Concatenate all values in the correct order
    keys = list(values.keys())
    keys.sort()
    values = {i: values[i] for i in keys}
    
    concatenated_values = ''.join([values[key] for key in (values.keys())])
    hash_object = hashlib.sha256(concatenated_values.encode('utf-8'))
    token = hash_object.hexdigest()

    return token


def set_timed_func(func_type, resource_id, time):

    request = requests.get(f'http://{SCHEDULER_HOST}:{SCHEDULER_PORT}/add_timer/{resource_id}/{time}?job_type={func_type}')
    
    return request.status_code
