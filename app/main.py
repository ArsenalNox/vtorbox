import logging
import uvicorn
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    orders, users, couriers, 
    admins, bot, boxes, 
    regions, routes, notifications,
    settings
    )

import os
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

#TODO: Доработать настройки
#TODO: Настройка сообщений бота
#TODO: настройка принятия заявок с бота
#TODO: переброс маршрута в яндекс маршрутизацию
#TODO: фикс дейттайма


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

#TODO argparse на инит бд  

if os.getenv('CREATE_DB'):
    from app.models import (
        init_role_table, init_boxtype_table, init_status_table,
        create_admin_user, add_default_messages_bot
    )
    init_role_table()
    init_boxtype_table()
    init_status_table()
    create_admin_user()
    add_default_messages_bot()

    exit()

if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)