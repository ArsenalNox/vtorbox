import logging
import uvicorn
import sys

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import orders, users, couriers, admins, bot, boxes, regions, routes

app = FastAPI()

origins = [
    # "http://127.0.0.1",
    # "http://127.0.0.1:8000",
    # "https://127.0.0.1",
    # "http://localhost",
    # "http://localhost:8080",
    "*"
]

#ВЕЧНО
#TODO: подправить под soft delete'ы где не подправил 

#TODO: Уведомление пользователю о подтверждении заявки
#TODO: Цены на контейнеры в районах 
#TODO: в какие дни автоматом генерация пулов
#TODO: В какие дни пул НЕ генерируется 

#TODO: переброс маршрута в яндекс маршрутизацию
#TODO: Добавить возможность передевать uuid вместо tg_id 


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


#TODO argparse на инит бд  

if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)