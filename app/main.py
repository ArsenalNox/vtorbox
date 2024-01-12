import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import orders, users, couriers, admins, bot, boxes

app = FastAPI()

origins = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "https://127.0.0.1",
    "http://localhost",
    "http://localhost:8080",
]

#СЕГОДНЯ
#TODO: soft delete

#TODO: Придумать как реализовать интервалы

#TODO: редактирование заявок пользователем
#TODO: Обновление статуса заявки админом или менеджером

#TODO: История вывоза 
#TODO: Формирование пула заявок (ручная)


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


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

if __name__ == '__main__':
    uvicorn.run('app.main:app', reload=True)