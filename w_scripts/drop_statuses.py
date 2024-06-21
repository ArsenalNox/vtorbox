import requests
import httpx


s = httpx.Client()

page = 0
limit = 10

url = "http://192.168.88.225:8000"

payload = {}
headers = {
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiNmYyNDBmOTYtYWNiMC00Zjk4LThmMGEtNTM0YTU5MmVlMDYyIiwic2NvcGVzIjpbImFkbWluIiwiY3VzdG9tZXIiLCJtYW5hZ2VyIiwiYm90Il19.KAbK_ws1SNLPVRY9CqBJLaYr5oYhlj0iOPTcdNfmoYw'
}


request_first_page = s.get(f"{url}/api/orders/filter/", headers=headers, params={"state": "ожидается подтверждение", "limit": 0})

if request_first_page.status_code != 200:
    print("ERROR")
    print(request_first_page.text)
    exit()

data = request_first_page.json()

print(data['global_count'])

for order in data['orders']:
    print(order['id'], end=' ')

    requst_set_to_cancel = s.put(
            f'{url}/api/orders/{order["id"]}/status', 
            params={"status_id": 'b7065607-546d-4b2a-80eb-abe7f98acec6'},
            headers=headers
        )

    if requst_set_to_cancel.status_code != 200:
        print("Error updating")
    else:
        print("Status updated")