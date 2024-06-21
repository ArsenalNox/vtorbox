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

    print(json)
    assert requst.status_code == 200
    assert requst.json() is not None


def test_update_order_data():
    pass
