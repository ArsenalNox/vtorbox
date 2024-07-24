from app.tests.test_01_before_main import client, test_globals

from datetime import datetime, timedelta
date_tommorrow = datetime.now() + timedelta(days=1)
date_num_tommorrow = datetime.strftime(date_tommorrow, "%Y-%m-%d")


def test_order_creation():
    json = {
            "address_id": test_globals['user_address_created'],
            "box_count": 1,
            "box_name": "Пакет",
            "day": date_num_tommorrow,
            "from_user": f"{test_globals['created_user_tg_id']}"
        }

    requst = client.post('/api/orders/create', json=json)

    assert requst.status_code == 200
    assert requst.json() is not None
    assert requst.json()['content'] is not None
    assert requst.json()['content']['manager_id'] is not None

    test_globals['order_created'] = requst.json()['content']


def test_update_order_data():
    json = {
        "address_id": test_globals['user_address_created'],
        "box_name": "Фасеточка",
        "box_count": 2,
        "comment": "test_comment_d",
        "comment_courier": "test_comment_courier",
        "comment_manager": "test_comment_manager",
        "day": datetime.strftime(datetime.now(), "%Y-%m-%dT%H:%S:%M"),
    }

    requst = client.put(f'/api/orders/{test_globals["order_created"]["id"]}', json=json)

    print(requst.text)
    print(json)
    assert requst.status_code == 200
    assert requst.json() is not None

    requst = client.get(f'/api/orders/{test_globals["order_created"]["id"]}')
    assert requst.status_code == 200
    assert requst.json() is not None

    for value_to_change in json:
        if value_to_change == "box_name":
            assert requst.json()['box_data']['box_name'] == json['box_name']
            continue
        
        if value_to_change == "box_count":
            assert requst.json()['box_count'] == json['box_count']
            continue

        assert requst.json()[value_to_change] == json[value_to_change]

