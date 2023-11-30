"""
Руты пользователей

CRUD с пользователями
Управление подпиской
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from ..models import Users, Orders, Session, engine
from ..auth import oauth2_scheme_admin

router = APIRouter()


#TODO: Генерация токена привязки пользователя к боту с сайта
#TODO: Ручная привязка пользователя к боту
#TODO: Отправка сообщения пользователю через бота 


@router.get('/users', tags=["admins", "managers"], responses={
    200: {
        "description": "Получение всех пользователей",
        "content": {
                "application/json": {
                    "example": 
                        [   
                            {
                                "full_name": 'null',
                                "date_created": "2023-11-29T00:57:57.654800",
                                "phone_number": 'null',
                                "email": 'null',
                                "telegram_id": 7643079034697,
                                "id": 1
                            }
                        ]
                }
        }
    }
})
async def get_all_users(token: Annotated[str, Depends(oauth2_scheme_admin)]):
    with Session(engine, expire_on_commit=False) as session:
        users = session.query(Users).all()
        if users:
            return users

    return []


@router.get('/users/{tg_id}', tags=["users"], responses={
    200: {
        "description": "Получение пользователя по телеграм айди",
        "content": {
                "application/json": {
                    "example": 
                        [   
                            {
                                "full_name": 'null',
                                "date_created": "2023-11-29T00:57:57.654800",
                                "phone_number": 'null',
                                "email": 'null',
                                "telegram_id": 7643079034697,
                                "id": 1
                            }
                        ]
                }
        }
    },
    404: {
        "description": "User not was not found",
        "content": {
                "application/json": {
                    "example": {"message": "Not found"}
                }
            },
    }
})
async def get_user_by_tg_id(tg_id:int):
    with Session(engine, expire_on_commit=False) as session:
        user = session.query(Users).filter_by(telegram_id=tg_id).first()
        if user:
            return user

    return JSONResponse({
        "message": "Not found"
    }, status_code=404)


@router.post('/users')
async def create_user():
    pass


@router.delete('/users')
async def delete_user():
    """
    Удаление пользователя
    """
    pass


@router.put('/users')
async def update_user_data():
    """
    Обновление данных пользователя
    """
    pass


@router.get('/users/bot_linked')
async def get_bot_users():
    """
    Получение пользователей тг бота, или пользователей сайта связавших профиль с тг
    """
    pass


@router.post('/users/auth')
async def authenticate_user():
    pass