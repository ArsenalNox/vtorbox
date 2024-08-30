import uvicorn
import time
import re
import logging
import sys 
import requests
import os

from dotenv import load_dotenv
from os import getenv

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

load_dotenv()

username=getenv("POSTGRES_USER")
host=getenv("POSTGRES_HOST")
port=int(getenv("POSTGRES_PORT"))
database=getenv("POSTGRES_DB")
password=getenv("POSTGRES_PASSWORD")

s = requests.Session()

load_dotenv()
backend_host = os.getenv('BACKEND_HOST')

api_url = f'{backend_host}:8000/api'

def authorize():
    username = 'user3@example.com'
    password = 'string'
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


def trigger_route_check(route_id):
    logging.info(f'Checking routing progress {route_id}')
    request = s.get(f'{api_url}/route/{route_id}/courier_map')
    print(request.json())
    if request.status_code == 200 and 'https://yandex.ru/maps' in request.text:
        logging.debug("Route generation is complete. Removing job")
        scheduler.remove_job(f'r-{route_id}')


def tirgger_payment_check(payment_id):
    logging.info(f"Checking payment status {payment_id}")
    request = s.get(f"{api_url}/payment/{payment_id}/status")
    print(request.json())
    statuses_failed = [
        'AUTHORIZED', 'PARTIAL_REFUNDED', 'REFUNDED', '3DS_CHECKING',
        'AUTH_FAIL', 'REJECTED', 'ATTEMPTS_EXPIRED', 'DEADLINE_EXPIRED',
        'CANCELED', 'REFUNDED', 'PARTIAL_REFUNDED', 'ASYNC_REFUNDING', 
        'REFUNDING'
    ]       

    statuses_in_progress = ['NEW', 'FORM_SHOWED', 'AUTHORIZING', 'CONFIRMING']

    statuses_completed = ['CONFIRMED', 'AUTHORIZED']

    if request.status_code != 200:
        return 
    
    logging.info(request.json())

    if not request.json():
        scheduler.remove_job(f'p-{payment_id}')
        return

    if 'Status' not in request.json():
        scheduler.remove_job(f'p-{payment_id}')
        return

    if request.json()['Status'] in statuses_in_progress:
        return 
    
    if 'Status' not in requests.json():
        scheduler.remove_job(f'p-{payment_id}')
        logging.info(f'Payment {payment_id} failed, removing check')

    if request.json()['Status'] in statuses_failed:
        scheduler.remove_job(f'p-{payment_id}')
        logging.info(f'Payment {payment_id} failed, removing check')

    if request.json()["Status"] in statuses_completed:
        scheduler.remove_job(f'p-{payment_id}')
        logging.info(f'Payment {payment_id} failed, removing check')

#TODO: Получение настройки вкд\выкл генерации пула
def trigger_poll_generation():
    request = s.get(f'{api_url}/process_orders')


#TODO: Получение настройки вкд\выкл генерации маршрутов
def trigger_route_generation():
    request = s.post(f'{api_url}/routes/generate?group_by=regions&write_after_generation=true')


def check_intervals():
    request = s.get(f'{api_url}/check-intervals')


def resend_notify():
    request = s.post(f'{api_url}/resend-notify')


@app.get("/add_timer/{resource_id}/{time}")
async def add_job(
    resource_id: str, 
    time: str,
    job_type: str,
    schedule_type: str = 'interval'
    ):

    hours = int(re.findall(r'[\d]+', time)[0]) if len(re.findall(r'H:[\d]+', time)) > 0 else 0
    minutes = int(re.findall(r'[\d]+', time)[0]) if len(re.findall(r'M:[\d]+', time)) > 0 else 0

    print(f"setting job: {resource_id} Hours: {hours}, minutes: {minutes}")
    func_to_schedule = None
    match job_type:
        case 'r':
            func_to_schedule = trigger_route_check
        
        case 'p':
            pass

        case _:
            func_to_schedule = None
        
    if func_to_schedule == None:
        return JSONResponse({
            "message": "Invalid job type provided"
        }, status_code=422)

    try: 
        scheduler.remove_job(f'{job_type}-{resource_id}')

    except:
        pass

    finally:
        scheduler.add_job(
            func=func_to_schedule, 
            trigger='interval', 
            args=[resource_id], 
            hours=hours, 
            minutes=minutes, 
            id=f'{job_type}-{resource_id}'
            )

    return 200


@app.get('/jobs')
async def get_jobs(
    type_filter: str = None
):
    jobs = scheduler.get_jobs()
    return_data = []
    for job in jobs: 
        if type_filter:
            if type_filter not in job.id:
                continue

        return_data.append({
            "job_id": job.id,
            "func_name": job.name,
            "interval": str(job.trigger)
        })

    print(jobs)
    return return_data


if __name__ == '__main__':
    authorize()
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
    jobstores = {
        "default": SQLAlchemyJobStore(f'postgresql://{username}:{password}@{host}:{port}/my_app')
    }
    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.start()

    #Генерация пула
    trigger_p_g = CronTrigger(
        year="*", month="*", day="*", hour="08", minute="01", second="00"
    )
    scheduler.add_job(
        trigger_poll_generation,
        trigger=trigger_p_g,
        id='trigger_poll_generation',
        replace_existing=True
    )

    #Проверка интервалов. Создание заявок по адресам если соответсвует интервал
    trigger_gen_intervals = CronTrigger(
        year="*", month="*", day="*", hour="22", minute="00", second="00"
    )
    scheduler.add_job(
        check_intervals,
        trigger=trigger_gen_intervals,
        id='trigger_get_intervals',
        replace_existing=True
    )

    #Формирование маршрутов, окончательное
    trigger_r_g = CronTrigger(
        year="*", month="*", day="*", hour="7", minute="30", second="00"
    )
    scheduler.add_job(
        trigger_route_generation,
        trigger=trigger_r_g,
        id='trigger_route_generation',
        replace_existing=True
    )

    #Повторная отправка сообщения на подтверждение
    trigger_s_n = CronTrigger(
        year="*", month="*", day="*", hour="19", minute="00", second="00"
    ) 
    scheduler.add_job(
        resend_notify,
        trigger=trigger_s_n,
        id='trigger_resend_notifications',
        replace_existing=True
    )

    scheduler.add_job(
        func=authorize, 
        trigger='interval', 
        hours=1, 
        id='reauthenticate',
        replace_existing=True
        )


    uvicorn.run(app, host="0.0.0.0", port=8081)
