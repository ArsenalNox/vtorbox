"""
Руты для пользователей


CRUD с пользователями
Управление подпиской
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from ..models import (
    Users, Orders, Session, engine, Roles, Permissions,
    ROLE_CUSTOMER_NAME
    )

from ..auth import (
    oauth2_scheme, 
    pwd_context, 
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)

from ..validators import (
    UserSignUp as UserSignUpSchema,
    UserLogin as UserLoginSchema,
    UserCreationValidator as UserCreationData,
    UserUpdateValidator as UserUpdateData

)

from passlib.context import CryptContext
from datetime import timedelta

from jose import jwt

import os, uuid
from dotenv import load_dotenv


load_dotenv()
router = APIRouter()

#TODO: Ручная привязка пользователя к боту #невозможно если пользователь не писал в тг
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
async def get_all_users(
        current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
        role_name: str = ROLE_CUSTOMER_NAME,

        #Применимо для клиентов
        with_orders: bool = False,
        with_active_orders: bool = False,
        with_inactive_orders: bool = False

        #Применимо для всех
    ):
    """
    Получение пользователей по фильтру
    """

    #TODO: Пагинация
    with Session(engine, expire_on_commit=False) as session:
        users = session.query(Users).all()
        if users:
            return users

    return []


@router.post('/users', tags=["admins"])
async def create_user(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
    new_user_data: UserCreationData
):
    """
    Ручное создание нового пользователя
    """

    with Session(engine, expire_on_commit=False) as session:
        query_user = session.query(Users).filter_by(email=new_user_data.email).first()
        if query_user: 
            return JSONResponse({
                "message": "Email already taken",
            }, status_code=400)

        new_user_data.password = get_password_hash(new_user_data.password)
        
        new_user_data = new_user_data.model_dump()
        user_role = new_user_data["role"]
        del new_user_data["role"]

        if new_user_data.send_email_invite:
            pass

        new_user = Users(**new_user_data)

        #Фикс: при flush uuid остаётся в сесси и не перегенерируется, т.е получаем Exception на unique field'е 
        new_user.link_code = str(uuid.uuid4())[:10] 

        session.add(new_user)
        session.flush()
        session.refresh(new_user)

        #Если админ - добавить все роли?
        

        for role in str(user_role).split(' '):
            role_query = Roles.get_role(role)
            if role_query:

                user_role = Permissions(
                    user_id = new_user.id,
                    role_id = Roles.get_role(role).id
                )

                session.add(user_role)

        session.commit()
        return new_user


@router.delete('/users', tags=["admins"])
async def delete_user():
    """
    Удаление пользователя (Отправляется в disabled)
    """
    pass


@router.put('/user', tags=["admin"])
async def update_user_data(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["manager"])],
    new_user_data: UserUpdateData
):
    """
    Обновление данных пользователя админом
    """
    with Session(engine, expire_on_commit=False) as session:
        user_query = session.query(Users).filter_by(id=new_user_data.user_id).first()

        if not user_query:
            user_query = session.query(Users).filter_by(telegram_id=new_user_data.user_id).first()

            if not user_query:
                return JSONResponse({
                    "message": "No such user"
                    }, status_code=404)

        for attr, value in new_user_data.model_dump().items():

            print(attr)

            if attr == 'password' and value:
                #TODO: Изменение пароля
                print('Changing user password')
                continue

            #TODO: Изменение ролей
            if value:
                setattr(user_query, attr, value)

        session.add(user_query)
        session.commit()

    return 


@router.put('/users', tags=["user"])
async def update_user_self_data(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["customer"])],
    new_user_data: UserUpdateData
):
    """
    Обновить свои данные пользователем
    """


@router.get('/users/bot_linked')
async def get_bot_users():
    """
    Получение пользователей тг бота, или пользователей сайта связавших профиль с тг
    """
    pass


@router.post('/users/signup', tags=["users"])
async def signup(signup_data: UserSignUpSchema):
    """
    Регистрация клиента
    """

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=signup_data.username).first()
        if query:
            return JSONResponse({
                "message": "Email already taken"
            }, status_code=409)

        new_user = Users(
            email=signup_data.username,
            password=get_password_hash(signup_data.password)
        )  

        session.add(new_user)
        session.flush()
        session.refresh(new_user)

        new_user.link_code = str(uuid.uuid4())[:10] 
        role_query = Roles.get_role(ROLE_CUSTOMER_NAME)

        if role_query:
            user_role = Permissions(
                user_id = new_user.id,
                role_id = role_query.id
            )

            session.add(user_role)
        else:
            raise HTTPException(status_code=503, detail="Internal server error")

        session.commit()

        return new_user


@router.post('/token', tags=["default"])
async def login(login_data: Annotated[OAuth2PasswordRequestForm, Depends()]):

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=login_data.username).first()
        if not query: 
            return JSONResponse({
                "message": "Invalid password or email"
            }, status_code=400)

        if not verify_password(login_data.password, query.password):
            return JSONResponse({
                "message": "Invalid password or email"
            }, 400)

        #TODO: Проверка на активность

        scopes_query = session.query(Permissions, Roles.role_name).filter_by(user_id=query.id).join(Roles).all()

        scopes = [role.role_name for role in scopes_query]
        print(scopes)
        expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
        token = create_access_token(
            data={
                "sub": login_data.username,
                "internal_id": str(query.id),
                "scopes": scopes
            }, 
            expires_delta=expires)

        return JSONResponse({
            "access_token": token,
            "token_type": "bearer"
        })


@router.post("/users/me", tags=["users"], responses={
    200: {
        "description": "Получение информации об авторизованном пользователе (себе)",
        "content": {
            "application/json": {
                "example": {
                    "user_data": {
                        "telegram_username": 'null',
                        "email": "test@mail.ru",
                        "password": "$2b$12$g9.50JMY2pLysGFeq15enuDxUKFz7LlXIgNO4mzgVW7ZgtruT2/YS",
                        "full_name": 'null',
                        "last_action": "2023-12-01T18:30:08.740109",
                        "link_code": "f191e981",
                        "telegram_id": 'null',
                        "id": "dec36dc4-109c-43d5-99b4-b801502606a7",
                        "phone_number": 'null',
                        "date_created": "2023-12-01T18:30:08.740109",
                        "allow_messages_from_bot": 'true'
                    },
                    "token_data": {
                        "sub": "test@mail.ru",
                        "internal_id": "dec36dc4-109c-43d5-99b4-b801502606a7",
                        "scopes": [
                        "users",
                        "me"
                        ],
                        "exp": 1701652303
                    }
                }
            }
        }
    },
    401: {
        "description": "Не удалось авторизировать пользователя",
        "content": {
                "application/json": {
                    "detail": "Not authenticated"
                }
            },
    }
})
async def get_current_user_info(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
):
    token_data = jwt.decode(token=current_user.access_token, key=SECRET_KEY, algorithms=ALGORITHM)

    with Session(engine, expire_on_commit=False) as session:
        query = session.query(Users).filter_by(email=current_user.username).first()
        return {
            "user_data": query,
            "token_data": token_data
            }


@router.post('/users/import_clients', tags=["admin"])
async def import_clients():
    """
    Импорт клиентов из excel таблицы
    """
    pass

