from fastapi import Depends, FastAPI

from .routers import orders

app = FastAPI()

#TODO: APSCHEDULER
#TODO: Админ панель? 

app.include_router(
    orders.router,
    prefix="/api",
    tags=["orders"])


# app.include_router(
#     admin.router,
#     prefix="/admin",
#     tags=["admin"],
#     responses={418: {"description": "I'm a teapot"}},
# )


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
