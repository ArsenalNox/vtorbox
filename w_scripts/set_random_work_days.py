import requests
import json
import random

url = "http://94.41.188.133:8000/api/regions"

payload = {}
headers = {
  'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiNmYyNDBmOTYtYWNiMC00Zjk4LThmMGEtNTM0YTU5MmVlMDYyIiwic2NvcGVzIjpbImFkbWluIiwiY291cmllciIsImN1c3RvbWVyIiwibWFuYWdlciIsImJvdCJdfQ.OiwGHxQSoi22TsHbpskIUe48rXGxyvMGk40_PS3WDYM'
}

response = requests.request("GET", url, headers=headers, data=payload)
print(response.status_code)
regions = response.json()
print(regions)
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

    url = f"http://94.41.188.133:8000/api/regions/{region['id']}"
    
    payload = json.dumps({
        "work_days": WEEK_DAYS_WORK_STR_LIST,
        "is_active": True
    })

    headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyM0BleGFtcGxlLmNvbSIsImludGVybmFsX2lkIjoiNDNmOTZiN2MtYzQxNy00YmUxLTliZTgtODU3YmY5ZGY4YWNiIiwic2NvcGVzIjpbImN1c3RvbWVyIiwiYWRtaW4iLCJtYW5hZ2VyIiwiY291cmllciIsImJvdCJdfQ.aKUiidy6ZQ18QdLeEs8cvHkFjft9wV7eCnzMVObMXqQ'
    }

    response = requests.request("PUT", url, headers=headers, data=payload)  
    print(response.status_code)