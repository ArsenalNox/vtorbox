import requests, json

from bot.utils.messages import MESSAGES

backend_host = '5.253.62.213'
api_url = f'http://{backend_host}:8000/api'

s = requests.Session()

def authorize(username='user3@example.com', password='string'):

    url = f"{api_url}/token"
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    }

    payload = f'username={username}&password={password}'
    
    response = requests.request("POST", url, headers=headers, data=payload)

    json_data = response.json()

    s.headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Bearer {json_data["access_token"]}'
    }

    print(response.json())


def get_settings():
    url = f'{api_url}/bot/settings?setting_type=бот'
    response = s.request("GET", url)

    return response.json()


def update_settings():
    settings = get_settings()
    for setting in settings:
        if setting['key'] in MESSAGES:
            print(f"Updating {setting['key']}")
            if setting['value'] != MESSAGES[setting['key']]:
                print("Setting value is different on host, updating")

            data =  json.dumps({
                "value": f"{MESSAGES[setting['key']]}"
            })

            headers = {
                'Content-Type': 'application/json'
            }

            request = s.put(f"{api_url}/bot/setting/{setting['id']}", data=data, headers=headers)
            print(request.status_code)
            #TODO: Если настройка не найдена то создать


if __name__ == "__main__":
    authorize()
    update_settings()