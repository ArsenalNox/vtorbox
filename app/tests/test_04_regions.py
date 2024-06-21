from app.tests.test_01_before_main import client, test_globals

def test_regions_present():

    params = {
        "only_active": False,
        "with_work_days": False
    }

    request = client.get('/api/regions')

    assert request.status_code == 200
    assert request.json() is not None
    

def test_active_regions_present():
    params = {
        "only_active": False,
        "with_work_days": False
    }

    request = client.get('/api/regions')

    assert request.status_code == 200
    assert request.json() is not None

    data = request.json()
    for region in data:
        assert region['name_full'] is not None
        assert region['is_active'] is True
        assert region['work_days'] is not None


    request = client.get('/api/regions', params={"search_query": 'район Преображенское'})
    assert request.status_code == 200
    assert request.json() is not None

    test_globals['test_working_region'] = data[-1]



def test_update_region_data():
    json = {
        "name_short": "short_name_test",
        "is_active": False,
        "work_days": [
            "string"
        ]
    }

    request = client.put(f'/api/regions/{test_globals["test_working_region"]["id"]}', json=json)

    assert request.status_code == 422

    json['is_active'] = True
    json['work_days'] = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "sunday",
        "saturday",
    ]

    request = client.put(f'/api/regions/{test_globals["test_working_region"]["id"]}', json=json)
    print(json)
    print(request.text)
    assert request.status_code == 200
    assert request.json() is not None
    assert request.json()['is_active'] is True
    
    for w_day in json['work_days']:
        assert w_day in request.json()['work_days']

