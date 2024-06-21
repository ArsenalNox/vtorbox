from app.tests.test_01_before_main import client, test_globals


def test_login_default_credentials():
    payload = 'username=user3%40example.com&password=string'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    request = client.post("/api/token", content=payload, headers=headers)

    assert request.status_code == 200

    token = request.json()['access_token']
    assert token is not None
    client.headers = {
        'Authorization': f"Bearer {token}"
    }
    refresh_token = request.json()['refresh_token']
    assert refresh_token is not None
    test_globals['refresh_token'] = refresh_token


def test_get_user_info():

    request = client.get("/api/users/me")

    assert request.status_code == 200
    assert request.json()['user_data'] is not None
    assert request.json()['user_data']['roles'] is not None

    test_globals['current_user_id'] = request.json()['user_data']['id']


def test_refresh_access_token():

    headers = {
        'Authorization': f"Bearer {test_globals['refresh_token']}"
    }
    request = client.post('/api/token/refresh', headers=headers)

    assert request.status_code == 200
    assert request.json()['access_token'] is not None
    assert request.json()['refresh_token'] is not None