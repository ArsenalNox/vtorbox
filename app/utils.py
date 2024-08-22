import uuid, os, requests
import time
import datetime
import hashlib
import httpx


from app import (
    CODER_KEY, CODER_SETTINGS, BOT_TOKEN,
    COURIER_API_ROOT_ENDPOINT as API_ROOT_ENDPOINT,
    SCHEDULER_HOST, SCHEDULER_PORT, COURIER_KEY, logger
    )

token = BOT_TOKEN

def is_valid_uuid(value):
    """
    Проверить, является ли строка валидным UUID
    """
    try:
        uuid.UUID(str(value))
        return True
    except ValueError as err:
        return False


async def get_lang_long_from_text_addres(address):
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={CODER_KEY}&geocode={address}{CODER_SETTINGS}"
    
    async with httpx.AsyncClient() as client:
        data = await client.get(url)
        data = data.json()

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


async def get_addresses_collection_from_text_address(address: str):
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={CODER_KEY}&geocode={address}{CODER_SETTINGS}"
    print(url)
    async with httpx.AsyncClient() as client:
        data = await client.get(url)
        data = data.json()
    print(data)
    # address_collection = data.get('response', {}). \
        # get('GeoObjectCollection', {}). \
        # get('featureMember')

    address_collection = data['response']['GeoObjectCollection']['featureMember']

    return_data = {}
    print(len(address_collection))
    for addr in address_collection:

        obj_type = addr['GeoObject']['metaDataProperty']['GeocoderMetaData']['kind']
        obj_text = addr['GeoObject']['metaDataProperty']['GeocoderMetaData']['text']
        print(obj_type, obj_text)

        if obj_type not in return_data:
            return_data[obj_type] = []
        
        if len(return_data[obj_type]) >= 5:
            continue

        return_data[obj_type].append(obj_text)

    return return_data


async def send_message_through_bot(receipient_id:int, message, btn=None):
    """
    Отправить сообщение пользователю через тг бота 
    """

    method = 'sendMessage'

    logger.debug("Sending message...")
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
        async with httpx.AsyncClient() as client:
            test_request = await client.post(
                url='https://api.telegram.org/bot{0}/{1}'.format(token, method), json=b
            )
            test_request = test_request.json()
            logger.debug("Message request responce data: ")
            logger.debug(test_request)

    except Exception as err:
        logger.error("An error occured, message not sent: {err}")


def generate_y_courier_json(route_data, vehicles=None):
    """
    Сгенерировать json для отправки в яндекс.маршрутизацию
    """
    locations = []

    time_winow = "10:00-20:00"

    for order in route_data.orders:
        try:
            order_d = order.order
        except Exception as err:
            order_d = order
        
        print(f" ID: {order_d.order_num} LAT: {order_d.address.latitude}; LONG: {order_d.address.longitude}")
        order_d_time_window = time_winow
        if order_d.time_window:
            order_d_time_window = order_d.time_window
        print(F"Order {order_d.order_num}, time window: {order_d_time_window}")

        locations.append({
            "id": order_d.order_num,
            "point": {
                "lon": float(order_d.address.longitude),
                "lat": float(order_d.address.latitude)
            },
            "time_window": order_d_time_window,
            "hard_window": True
        })

    payload_vehicles = [
            {
                "id": "courier-1",
                "ref": "c_id_internal-1",
                "shifts": [
                    {
                        "id": "day",
                        "time_window": "10:00-20:00",
                        "balanced_group_id": "group_1"
                    }
                ]
            }]

    if vehicles:
        payload_vehicles = vehicles

    payload = {
        "depot": {
            "id": 0,
            "point": {
                "lat": 55.734157,
                "lon": 37.589346
            },
            "time_window": "10:00-20:00"
        },
        "vehicles": payload_vehicles,
        "locations": locations,
        "options": {
            "time_zone": 3,
            "quality": "normal",
            "balanced_groups": [
                {
                    "id": "group_1"
                }
            ]
        }
    }

    # print(payload)
    return payload


async def get_result_by_id(request_id):
    poll_stop_codes = {
        requests.codes.ok,
        requests.codes.gone,
        requests.codes.internal_server_error
    }

    poll_url = '{}/result/mvrp/{}'.format(API_ROOT_ENDPOINT, request_id)

    async with httpx.AsyncClient() as client:
        response = client.get(poll_url)

    urls = []
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


            return yamaps_url
    
    return None


async def gen_intermediate_route(request_id):
    """
    Генерирует один промежуточный маршрут, исходя из результатов которого формируются остальные маршруты
    """
    poll_stop_codes = {
        requests.codes.ok,
        requests.codes.gone,
        requests.codes.internal_server_error
    }

    poll_url = '{}/result/mvrp/{}'.format(API_ROOT_ENDPOINT, request_id)

    async with httpx.AsyncClient() as client:
        response = await client.get(poll_url)

        while response.status_code not in poll_stop_codes:
            time.sleep(1)
            response = await client.get(poll_url)

    waypoints = []
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

                waypoints.append({
                    "order_num": waypoint['node']['value']['id'],
                    "eta": str(datetime.timedelta(seconds=waypoint['arrival_time_s']))
                })

    return waypoints


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


async def set_timed_func(func_type, resource_id, time):

    async with httpx.AsyncClient() as client:
        request = await client.get(f'http://{SCHEDULER_HOST}:{SCHEDULER_PORT}/add_timer/{resource_id}/{time}?job_type={func_type}')
    
    return request.status_code


async def generate_time_intervals(route_data):
    from datetime import datetime
    import datetime as dt 
    import requests
    from time import sleep
    from sqlalchemy import desc, asc, desc, or_
    from app.models import Session, engine, Orders, Address
    from sqlalchemy.orm import joinedload

    time_ranges = [
        ['10:00','13:00'],
        ['13:00', '16:00'],
        ['16:00', '20:00'],
    ]

    order_list_generated = []
    #Получаем временные интервалы заявок
    async def set_route_generation_task(route_data):
        payload = generate_y_courier_json(route_data)

        async with httpx.AsyncClient() as client:
            response = client.post(
                API_ROOT_ENDPOINT + '/add/mvrp',
                params={'apikey': COURIER_KEY}, json=payload)

        print(response.status_code)
        return response.json()
        

    return_data = await set_route_generation_task(route_data)
    print(return_data)
    print(return_data['status'])
    print('completed' in return_data['status'])

    waypoints = []

    if not 'completed' in return_data['status']:
        date_queued = datetime.fromtimestamp(return_data['status']['queued'])
        date_estimate = datetime.fromtimestamp(return_data['status']['estimate'])
        print(f"Job queued. Estimate completion : {date_estimate}, in ({(date_estimate-date_queued).total_seconds()})")
        sleep((date_estimate-date_queued).total_seconds())
        waypoints = await gen_intermediate_route(return_data['id'])
    else:
        print("Job completed")
        waypoints = await gen_intermediate_route(return_data['id'])

    with Session(engine, expire_on_commit=False) as session:
        for wp in waypoints:
            order_q = session.query(Orders).options(
                    joinedload(Orders.user),
                    joinedload(Orders.address)
                ).filter_by(order_num = wp['order_num']).enable_eagerloads(False).first()

            if not order_q:
                continue

            order_q.user.telegram_id
            order_q.address

            print(f"Order {order_q.order_num} found in db, ETA: {wp['eta']}")
            #Записываем сгенерированный временной интервал
            #TODO: Оверрайд? 
            for time_range in time_ranges:
                start = dt.time(int(time_range[0].split(':')[0]), 0, 0)
                end = dt.time(int(time_range[1].split(':')[0]), 0, 0)
                x = dt.time(int(wp['eta'].split(":")[0]), int(wp['eta'].split(":")[0]))
                in_interval = False
                if start <= end:
                    in_interval = start <= x <= end
                else:
                    in_interval = start <= x or x <= end

                if in_interval:
                    print(start, end)
                    order_q.time_window = f"{start}-{end}"
            
            if order_q.time_window == None:
                    order_q.time_window = "10:00-13:00"

            order_list_generated.append(order_q)
            

        #TODO: Обновление статуса
        session.commit()
    
    return order_list_generated