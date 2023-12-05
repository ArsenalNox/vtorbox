from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import orders, users, couriers, admins

app = FastAPI()

#Сегодня
#TODO: Редактирование данных пользователя

#TODO: APSCHEDULER
#TODO: Админ панель? 


origins = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "https://127.0.0.1",
    "http://localhost",
    "http://localhost:8080",
]


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
    # prefix="/api",
)


app.include_router(
    couriers.router,
    prefix="/api",
)


app.include_router(
    admins.router,
    prefix="/api",
)