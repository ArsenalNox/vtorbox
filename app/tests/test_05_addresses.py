from app.tests.test_01_before_main import client, test_globals


def test_geocoder_accuracy():
    params = {
        'lat': 53.123,
        'long': 51.234
    }

    request = client.get('/api/bot/address/check', params=params)

    assert request.status_code == 422
    assert request.json() is not None

    assert request.json()['message'] == 'Адресс находится вне рабочей области проекта'
    assert request.json()['address'] == None

    params = [
        {
            'lat': 55.796429,
            'long': 37.709039
        },
        {
            'lat': 55.715616,
            'long': 37.525681
        }
    ]

    for param in params:
        request = client.get('/api/bot/address/check', params=param)

        assert request.status_code == 200
        assert request.json() is not None

        assert 'Россия, Москва' in request.json()['message']
        assert request.json()['addresses'] is not None

    params = {
        "text": "Г. Оренбург, пр. Победы 155"
    }
    request = client.get('/api/bot/address/check/text', params=params)

    assert request.status_code == 422
    assert request.json() is not None

    assert request.json()['message'] == 'Адрес находится вне рабочей области проекта'


def test_address_creation():
    json = {
        "address": "Ул. Тверская 4",
        "comment": "Злая собака, много тараканов",
        "detail": "8-53. Домофон 53 и кнопка \"вызов\".",
        "district": "МО",
        "main": "true"
    }

    request = client.post('/api/bot/user/addresses', json=json, params={'tg_id': test_globals['created_user_tg_id']})

    assert request.status_code == 200
    assert request.json() is not None
    assert request.json()['region']['name_full'] == 'Тверской район'

    test_globals['user_address_created'] = request.json()['id']


def test_address_update():
    json = {
        "interval_type": "week_day",
        "selected_day_of_week": [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "sunday",
            "saturday",
        ]
    }

    request = client.put(
            f"/api/bot/user/addresses/{test_globals['user_address_created']}/schedule", 
            json=json, 
            params={'tg_id': test_globals['created_user_tg_id']}
        )

    assert request.status_code == 200
    assert request.json() is not None

    for w_day in json['selected_day_of_week']:
        assert w_day in request.json()['interval']