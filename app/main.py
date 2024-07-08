import logging
import uvicorn
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    orders, users, couriers, 
    admins, bot, boxes, 
    regions, routes, notifications,
    settings, payments, managers,
    stats, jobs
    )

import os
from app import Tags
from dotenv import load_dotenv

app = FastAPI()

origins = [
    # "http://127.0.0.1",
    # "http://127.0.0.1:8000",
    # "https://127.0.0.1",
    # "http://localhost",
    # "http://localhost:8080",
    "*"
]

load_dotenv()

#ВЕЧНО
#TODO: подправить под soft delete'ы где не подправил 

#TODO: Убрать возможность удалять заявку из маршрута со статусом выполнена и выше
#TODO: Доработать настройки

#TODO: Закруглить даты
#TODO: deleted_at в картах пользователя
#TODO: Если день прошёл, а маршрут не утверждён, то расформировать маршрут -> требует внимания (создана)
#TODO: Дата последнего действия на определённых эндпоинтах

"""
TODO: Те заявки, что не подтвердили уходят в отменённые #
TODO: комментарий что заявка не прошла по подтверждению на последнем сообщении #
TODO: Множество инстансов поднимать
TODO: Отправка сообщения с уведомлением в тг 

- Изменение цены заявки
 Необходимо реализовать возможность изменить цену заявку вручную, т.е. у заявки должно быть поле, где при выборе типа и кол-ва контейнеров записывается число, 
 но его можно менять вручную, либо же при изменении типа/кол-ва, оно автоматом обсчитывается.

- Привязка смс шлюза
 Заказчик зарегает смс шлюзу sms4b, нужно подготовить систему, чтобы потом только вписать данные.
 У Саши М можно узнать, как это все работает, они уже интегрировали это в другой проект наш. (НИ В КОЕМ СЛУЧАЕ  не юзать данные (токены, логины, пароли) из других проектов, свои созданные тестовые можно)
"""

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    orders.router,
    prefix="/api",
    tags=[Tags.orders]
)

app.include_router(
    users.router,
    prefix="/api",
)

app.include_router(
    boxes.router,
    prefix="/api"
)

app.include_router(
    couriers.router,
    prefix="/api",
)

app.include_router(
    admins.router,
    prefix="/api",
)

app.include_router(
    bot.router,
    prefix="/api/bot",
    tags=['bot']
)

app.include_router(
    regions.router,
    prefix="/api",
)


app.include_router(
    routes.router,
    prefix='/api'
)


app.include_router(
    notifications.router,
    prefix='/api/notifications',
    tags=[Tags.notifications]
)


app.include_router(
    settings.router,
    prefix='/api',
    tags=[Tags.settings]
)


app.include_router(
    payments.router,
    prefix='/api',
    tags=[Tags.payments]
)


app.include_router(
    managers.router,
    prefix='/api',
    tags=[Tags.managers]
)


app.include_router(
    stats.router,
    prefix='/api',
    tags=[Tags.statistics]
)

app.include_router(
    jobs.router,
    prefix='/api',
    tags=['jobs']
)


#TODO argparse на инит бд  
if os.getenv('CREATE_DB') == 1:
    from app.models import (
        init_role_table, init_boxtype_table, init_status_table,
        create_admin_user, add_default_messages_bot, add_default_settings,
        create_demo_terminal, init_status_restrictions
    )
    init_role_table()
    init_boxtype_table()
    init_status_table()
    create_admin_user()
    add_default_messages_bot()
    add_default_settings()
    create_demo_terminal()
    init_status_restrictions()

if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)