
#TODO: Пригласить пользователя по e-mail

#TODO: Курьерские настройки (добавление курьеров, тонкие настройки маршрутизации и др)
#TODO: Платежные шлюзы (добавляем возможные варианты приема денег, 
# чтобы давать их на выбор клиентам, админ может вкл/выкл какие-то шлюзы, управлять их настройками)

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm, SecurityScopes

from app.models import (
    engine, 
    Session, 
    OrderStatuses,
    Roles, Permissions
)

from app.validators import (
    UserLogin as UserLoginSchema,
    StatusOut
)

from app.auth import (
    oauth2_scheme, 
    pwd_context, 
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_active_user,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
)

import os, uuid
from dotenv import load_dotenv
from app import Tags

load_dotenv()
router = APIRouter()


@router.get('/statuses', tags=['statuses'])
async def get_all_statueses(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)]
) -> list[StatusOut]:
    """
    Получение списка всех статусов
    """
    with Session(engine, expire_on_commit=False) as session:
        statuses = session.query(OrderStatuses).all()
        statuses_list = [StatusOut(**status.__dict__) for status in statuses]
        return statuses_list


@router.get('/statuses/name', tags=['statuses'])
async def get_status_info_by_name(
    current_user: Annotated[UserLoginSchema, Security(get_current_user)],
    status_name: str
) -> StatusOut:
    """
    Получение статуса по его названию
    """
    with Session(engine, expire_on_commit=False) as session:
        status_name = f"%{status_name}%"
        status = session.query(OrderStatuses).filter(OrderStatuses.status_name.like(status_name)).first()
        return status


@router.put('/statuses/{status_id}', tags=['admins'])
async def change_status():
    pass


@router.get('/roles', tags=[Tags.roles])
async def get_avaliable_roles(
    current_user: Annotated[UserLoginSchema, Security(get_current_user, scopes=["admin"])]
):
    """
    Получение списка ролей
    """

    with Session(engine, expire_on_commit=False) as session:
        roles_query = session.query(Roles).all()
        return_data = []
        for role in roles_query:
            match role.role_name:
                case 'admin':
                    role.label = 'админ'

                case 'bot':
                    role.label = 'бот'
                    
                case 'customer':
                    role.label = 'клиент'

                case 'courier':
                    role.label = 'курьер'

                case 'manager':
                    role.label = 'менеджер'

            return_data.append(role)

        return return_data


@router.get("/stats", tags=[Tags.admins])
async def get_statistics():
    """
    получить статистику использования проекта
    """
    pass