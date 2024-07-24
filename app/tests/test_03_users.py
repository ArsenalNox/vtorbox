from app.tests.test_01_before_main import client, test_globals
import random
from faker import Faker
from faker.providers import phone_number

fake = Faker('ru_RU')
fake.add_provider(phone_number)


def test_user_creation():
    name, second_name, patronymic = str(fake.name()).split(' ')
    p_n = f"7905{fake.msisdn()[0:3]}{fake.msisdn()[0:4]}"
    json = {
        "email": fake.email(),
        "password": "test_password",
        "telegram_id": int(f"1{random.randint(1000,10000000)}"),
        "telegram_username": fake.user_name(),
        "phone_number": p_n,
        "firstname": name,
        "secondname": second_name,
        "patronymic": patronymic,
        "role": [
            "customer"
        ]
    }
    request = client.post('/api/users', json=json)
    assert request.status_code == 200
    test_globals['created_user_id'] = request.json()['id']
    test_globals['created_user_tg_id'] = request.json()['telegram_id']
    assert request.json()['email'] is not None

    json = {
        "user_id": test_globals['created_user_id'],
        "allow_messages_from_bot": False,
    }
    request = client.put('/api/user', json=json)
    assert request.status_code == 200


def test_user_profile_edit():
    json = {
        "user_id": test_globals['current_user_id'],
        "telegram_id": 12345,
        "telegram_username": "test_username",
        "phone_number": "+79058855111",
        "firstname": "test_first_name",
        "secondname": "test_second_name",
        "patronymic": "test_patronymic",
        "email": "user3@example.com",
        "allow_messages_from_bot": False,
        "roles": ["bot", "customer", "admin", "manager"],
        "link_code": "TEST_LINK_CODE",
        "additional_info": "TEST_ADD_INFO"
    }

    request = client.put('/api/user', json=json)

    assert request.status_code == 200

    request = client.get('/api/users/me')

    assert request.json()['user_data'] is not None
    data_retrieved = request.json()
    json.pop('user_id')
    json['id'] = test_globals['current_user_id']

    for value_to_change in json:
        if value_to_change == 'roles':
            expected = json['roles']
            actual = data_retrieved['user_data']['roles']
            lacks = set(expected) - set(actual)
            extra = set(actual) - set(expected)
            message = f"Lacks elements {lacks} " if lacks else ''
            message += f"Extra elements {extra}" if extra else ''
            assert not message
            continue

        assert data_retrieved['user_data'][value_to_change] == json[value_to_change]


def test_get_other_user_info_by_tg_id():
    request = client.get(f'/api/bot/users/telegram?tg_id={test_globals["created_user_tg_id"]}')
    assert request.json() is not None
    assert request.json()['id'] == test_globals['created_user_id']


def test_get_other_user_info_by_uuid_id():
    request = client.get(f'/api/user/{test_globals["created_user_id"]}/info')
    assert request.json() is not None
    assert request.json()['id'] == test_globals['created_user_id']


def test_getting_users_by_filter():

    switchable_params = {
        "only_bot_users": False,
        "with_orders": False,
        "with_active_orders": False,
        "witn_inactive_orders": False,
        "has_orders": False,
        "show_deleted": True
    }
    
    params = {
        "limit": 5,
        "page": 0,
    }

    request = client.get('/api/users', params={
        "only_bot_users": False,
        "with_orders": False,
        "with_active_orders": False,
        "witn_inactive_orders": False,
        "has_orders": False,
        "limit": 5,
        "page": 0,
        "show_deleted": True
    })

    assert request.status_code == 200
    assert request.json() is not None

    for param in switchable_params:
        for param_off in switchable_params:
            switchable_params[param_off] = False

        switchable_params[param] = True

        request = client.get('/api/users', params= params | switchable_params)
        assert request.status_code == 200
        assert request.json() is not None

