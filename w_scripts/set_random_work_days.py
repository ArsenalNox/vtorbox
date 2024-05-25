import requests
import json
import random

url = "http://5.253.62.213:8000/api/regions"

payload = {}
headers = {
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiNDNmOTZiN2MtYzQxNy00YmUxLTliZTgtODU3YmY5ZGY4YWNiIiwic2NvcGVzIjpbImN1c3RvbWVyIiwiYWRtaW4iLCJtYW5hZ2VyIiwiY291cmllciIsImJvdCJdfQ.aKUiidy6ZQ18QdLeEs8cvHkFjft9wV7eCnzMVObMXqQ'
}

response = requests.request("GET", url, headers=headers, data=payload)

regions = response.json()
WEEK_DAYS_WORK_STR_LIST = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "sunday",
    "saturday",
]
for region in regions:

    url = f"http://5.253.62.213:8000/api/regions/{region['id']}"
    
    payload = json.dumps({
        "work_days": WEEK_DAYS_WORK_STR_LIST[random.randint(0,6):-1]
    })

    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiNDNmOTZiN2MtYzQxNy00YmUxLTliZTgtODU3YmY5ZGY4YWNiIiwic2NvcGVzIjpbImN1c3RvbWVyIiwiYWRtaW4iLCJtYW5hZ2VyIiwiY291cmllciIsImJvdCJdfQ.aKUiidy6ZQ18QdLeEs8cvHkFjft9wV7eCnzMVObMXqQ'
    }

    response = requests.request("PUT", url, headers=headers, data=payload)  
    print(response.status_code)