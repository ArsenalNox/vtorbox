import logging
import uvicorn
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    orders, users, couriers, 
    admins, bot, boxes, 
    regions, routes, notifications,
    settings, payments, managers
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
#TODO: Поставить фильтр на даты в маршрутах 
#TODO: Доработать настройки

#TODO: настройка принятия заявок с бота
#TODO: фикс дейттайма

#TODO: deleted_at в картах пользователя
#TODO: Если день прошёл, а маршрут не утверждён, то расформировать маршрут -> требует внимания (создана)
#TODO: История комментариев у заявки
#TODO: Дата последнего действия на определённых эндпоинтах
#TODO: Фикс медленного получения заявок с последней страницы (недостаточно озу + упростить возвращаемые данные)
#TODO: Унификация формата ответа ошибок


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
    prefix='/api'
)


app.include_router(
    settings.router,
    prefix='/api'
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


#TODO argparse на инит бд  
if os.getenv('CREATE_DB'):
    from app.models import (
        init_role_table, init_boxtype_table, init_status_table,
        create_admin_user, add_default_messages_bot, add_default_settings,
        create_demo_terminal
    )
    init_role_table()
    init_boxtype_table()
    init_status_table()
    create_admin_user()
    add_default_messages_bot()
    add_default_settings()
    create_demo_terminal()

if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)